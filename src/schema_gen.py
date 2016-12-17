import os
import csv
from collections import defaultdict

import predictors
import strconv

class SchemaGenerator:
    supported_extensions = []

    def __init__(self, file):
        self.file = file
        self.schema = []
        self.bonus_schema = []
        self.primary_schema = []
        self.bonus_predictors = {} # name -> predictor

    @classmethod
    def supports_file(cls, filename):
        return any(filename.endswith(x) for x in cls.supported_extensions)

class CSVSchemaGenerator(SchemaGenerator):
    supported_extensions = ['.csv']

    def extract_schema(self):
        with open(self.file, 'r') as f:
            reader = csv.DictReader( f )
            line, headers = {}, []
            for line in reader:
                headers = list(line.keys())
                values = list(line.values())
                break

            types = defaultdict(lambda : 'String')
            bonus_types = {}
            for header, value in line.items():
                # prevent identifiers from appearing as name of schema
                if header == "timestamp":
                    header = 't_timestamp'
                if header == "id":
                    header == "t_id"
                if header == "string":
                    header == "t_string"

                inferred_type = strconv.infer(value)
                if inferred_type == 'int':
                    types[header] = inferred_type
                elif inferred_type == 'float':
                    types[header] = inferred_type
                elif inferred_type == 'date':
                    types[header] = inferred_type
                elif inferred_type == 'bool':
                    types[header] = 'boolean'
                else:
                    types[header] = 'String'
                # print("Getting predictors for", header, value)
                # Now feed value into all predictors and see if they work
                bonus_predictors = predictors.find_predictors(types[header], value)
                for predictor in bonus_predictors:
                    for bonus_field, bonus_field_type in predictor.added_fields_mapping.items():
                        bonus_name =  'rodeo_{}_{}'.format(header, bonus_field)
                        self.bonus_predictors[bonus_name] = predictor
                        bonus_types[bonus_name] = bonus_field_type


            self.primary_schema = ["{} {}".format(h, t) for h,t in types.items()]
            self.bonus_schema = ["{} {}".format(h, t) for h,t in bonus_types.items()]

            self.schema = self.primary_schema + self.bonus_schema
            return self.schema

def find_generator(filename):
    for ex in [CSVSchemaGenerator]:
        if ex.supports_file(filename):
            return ex
