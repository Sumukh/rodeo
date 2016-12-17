""" Extracts schema from folders or files.
"""
import os
import predictors

class Extractor:
    supported_extensions = []
    corresponding_predictor = None

    @classmethod
    def supports_file(cls, filename):
        return any(filename.endswith(x) for x in cls.supported_extensions)

    @staticmethod
    def schema_suggestion(filename):
        return ['name String', 'extension String']

    @staticmethod
    def should_create_new_table(filename):
        return False

    @staticmethod
    def data(filename):
        name, extension = os.path.splitext(filename)
        return {
            'name': name,
            'extension': extension
        }

class CSVExtractor(Extractor):
    """ Schema for the file table. """
    supported_extensions = ['.csv']

    @staticmethod
    def schema_suggestion(filename):
        return ['name String', 'extension String', 'size int']

    @staticmethod
    def should_create_new_table(filename):
        return True

class ImageExtractor(Extractor):
    supported_extensions = ['.png', '.jpg', '.jpeg']
    corresponding_predictor = predictors.ImagePredictor
    @staticmethod
    def schema_suggestion(filename):
        return ['name String', 'extension String', 'size int', 'exif String'] + predictors.ImagePredictor.added_fields


def find_extractor(filename):
    for ex in [CSVExtractor, ImageExtractor]:
        if ex.supports_file(filename):
            return ex
    return Extractor