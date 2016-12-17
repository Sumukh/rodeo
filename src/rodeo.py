import sys
import os
from collections import defaultdict

import tabulate

import extractors
import schema_gen

class Table:
    def __init__(self, name, raw_dir=None, schema=None):
        self.name = name
        self.raw_dir = raw_dir
        self.sanitize_name()
        if not schema:
            self.schema = []
        else:
            self.schema = schema

    def sanitize_name(self):
        # TODO make staticmethod that returns val
        self.name = self.name.replace(' ', '').replace('/','_').replace('-', '_')

    def __str__(self):
        return "Table {name}({schema})".format(name=self.name, schema=self.schema)

    def extend_schema(self, schemas):
        added = []
        for schema_item in schemas:
            if schema_item not in self.schema:
                self.schema.append(schema_item)
                added.append(schema_item)
        return added

    def create_command(self):
        create_query = """CREATE TABLE IF NOT EXISTS {name} ( {schema})
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY '\\t'
            LINES TERMINATED BY '\\n'
            STORED AS TEXTFILE;""".format(name=self.name, schema=', '.join(self.schema))
        return create_query

class DirTable(Table):
    def __init__(self, name, raw_dir=None, schema=None):
        self.name = name
        self.raw_dir = raw_dir
        self.sanitize_name()
        if not schema:
            self.schema = ['filename String', 'name String', 'extension String']
        else:
            self.schema = schema

    @property
    def contents(self):
        return os.listdir(self.raw_dir)

class DataTable(Table):
    pass

def print_table(table):
    col_width = [max(len(x) for x in col) for col in zip(*table)]
    long_line = ""
    for line in table:
        long_line += "| " + " | ".join("{:{}}".format(x, col_width[i])
                                for i, x in enumerate(line)) + " |"
        long_line += '\n'
    return long_line


class Rodeo:
    def __init__(self, root, name='rodeo.db'):
        self.root = root
        self.standalone_tables = []
        self.all_dirs = []
        self.standalone_files = []
        self.table_predictors = {} # filename -> gen object

    @property
    def tables(self):
        return self.all_dirs + self.standalone_tables

    def lasso(self, directory, name='root'):
        """ Collect directory structure and files. """
        dir_table = DirTable(name, raw_dir=directory)
        # Take all directory as tables to be created
        files_in_dir = os.listdir(directory)
        # If a file is detected that deserves its own table, it is queued for analysis
        for file in files_in_dir:
            file_path = os.path.join(directory, file)
            if os.path.isdir(file_path):
                # loop
                self.lasso(directory +  file + '/', name=name+'_'+file)
            else:
                extractor = extractors.find_extractor(file)
                good_schema = extractor.schema_suggestion(file)
                added_items = dir_table.extend_schema(good_schema)
                if extractor.corresponding_predictor or dir_table.name not in self.table_predictors:
                    self.table_predictors[dir_table.name] = extractor.corresponding_predictor
                if extractor.should_create_new_table(file):
                    if file_path not in self.standalone_files:
                        self.standalone_files.append(file_path)

        self.all_dirs.append(dir_table)

    def tame(self, file_name):
        """ Create tables for standalone files that can be parsed.
        Taming the wild file in a domesticated relational table :)
        """
        name, extension = os.path.splitext(file_name)
        sanitized_name = name.replace(self.root, '')
        new_table = Table(sanitized_name, raw_dir=file_name)
        gen = schema_gen.find_generator(file_name)
        if not gen:
            print("Could not find a generator for", file_name)
            return
        generator = gen(file_name)
        self.table_predictors[file_name] = generator
        found_schema = generator.extract_schema()
        if not found_schema:
            print("No schema found")
            return
        new_table.extend_schema(found_schema)
        self.standalone_tables.append(new_table)

    def wrangle(self, directory):
        self.lasso(directory)
        for standalone in self.standalone_files:
            self.tame(standalone)

    def sample_predictions(self, table_name):
        for table in self.tables:
            print_table_data = []

            if table.name == table_name:
                print(table)
                gen = self.table_predictors[table.name]
                if not gen:
                    continue # Inspect some of the contents and print
                schema_fields = gen.added_fields_mapping.keys()
                print_table_data.append(schema_fields)

                for file in table.contents:
                    # print(file)
                    full_file = table.raw_dir + file
                    # print(full_file)
                    if gen.should_predict_file(full_file):
                        prediction = gen.predict(full_file)
                        prediction_vals = []
                        for field in schema_fields:
                            if field in prediction:
                                prediction_vals.append(repr(prediction[field]))
                            else:
                                prediction_vals.append("-")
                        print_table_data.append(prediction_vals)

                ascii_table = tabulate.tabulate(print_table_data)
                plain_table = tabulate.tabulate(print_table_data, tablefmt="plain")

                with open('sample-{}-preview.txt'.format(table_name), 'w') as f:
                    f.write(ascii_table)

                print(ascii_table)

    def setup_query(self):
        for d in self.all_dirs:
            print(d.create_command())
        for d in self.standalone_tables:
            print(d.create_command())

if __name__ == "__main__":
    r = Rodeo('../datasets/')
    r.wrangle(r.root)
    r.setup_query()
    # for t in r.tables:
    #     print(t)
    r.sample_predictions('root_images')
