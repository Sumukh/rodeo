# Prediction Files
import re
import os

import tweet_classifier.classifier as sentimentClassifier
from models import cloudvision

class Predictor:
    operates_on = []

    @classmethod
    def valid_for_type(cls, filetype):
        return filetype in cls.operates_on

    @staticmethod
    def should_predict_file(filename):
        return False

    @staticmethod
    def should_predict_contents(contents):
        return False

class ImagePredictor(Predictor):
    added_fields_mapping = {
                    'filename': 'String',
                    'extension': 'String',
                    'object_labels': 'String',
                    'text': 'String',
                    'landmark': 'String',
                    'logo': 'String',
                    'colors': 'String',
                    'has_face': 'String',
                    'emotion': 'String'}
    added_fields = ["{} {}".format(k, v) for k,v in added_fields_mapping.items()]
    operates_on = ['File']

    @staticmethod
    def should_predict_file(filename):
        filename = filename.lower()
        return filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg')

    @staticmethod
    def predict(filename):
        name, extension = os.path.splitext(filename)
        path, pure_fname = os.path.split(filename)
        data = cloudvision.serialize_response(filename)
        data['filename'] = pure_fname
        data['extension'] = extension
        return data

class SentimentPredictor(Predictor):
    added_fields_mapping = {'sentiment': 'String',
                            'polarity': 'float'}
    added_fields = ["{} {}".format(k, v) for k,v in added_fields_mapping.items()]

    operates_on = ['String']

    @staticmethod
    def should_predict_contents(contents):
        if len(contents) < 40:
            # Do not operate on long strings
            return False
        return True

    @staticmethod
    def predict(contents):
        sentiment = sentimentClassifier.doSentimentAnalysis(contents)

        return {'sentiment': sentiment['sentiment'],
                'polarity': sentiment['polarity']}


class YearPredictor(Predictor):
    added_fields_mapping = {'year': 'int'}
    added_fields = ["{} {}".format(k, v) for k,v in added_fields_mapping.items()]
    operates_on = ['String']

    @staticmethod
    def should_predict_contents(contents):
        if len(contents) > 500:
            # Do not operate on long strings
            return False
        if re.match(".*([1-3][0-9]{3})", contents):
            return True
        return False

    @staticmethod
    def predict(contents):
        match = re.match(r'.*([1-3][0-9]{3})', contents)
        if match is not None:
            # Then it found a match!
            return {'year': int(match.group(1))}

#Turns out the dataset already has that info
class UnitsPredictor(Predictor):
    """ Crude unit detection. """

    added_fields_mapping = {'units': 'String'}
    added_fields = ["{} {}".format(k, v) for k,v in added_fields_mapping.items()]
    units = ['cups', 'cup', 'teaspoon', 'bottles', 'gallon',
             'pound', 'lb', 'oz', 'ounces', '-ounces', 'scoops', 'cloves']
    operates_on = ['String']

    @staticmethod
    def should_predict_contents(contents):
        if len(contents) > 200 or len(contents) < 20:
            # Do not operate on long strings
            return False
        words = contents.split(' ')
        if any([u for u in UnitsPredictor.units if u in words]):
            return True
        return False

    @staticmethod
    def predict(contents):
        words = contents.split(' ')
        found_words = [w for w in words if w in self.units]
        # TODO: Include previous unit
        return {'units': '-'.join(found_words)}


predictors = [ImagePredictor, SentimentPredictor, YearPredictor, UnitsPredictor]

def find_predictors(filetype, contents):
    """ Contents might be a file_name if the filetype is File
    otherwise contents is the contents of the value.
    """
    elgible_predictors = [p for p in predictors if p.valid_for_type(filetype)]
    # print("Elgible", elgible_predictors)
    if filetype == 'file':
        qualified_predictors = [p for p in elgible_predictors if p.should_predict_file(contents)]
    else:
        qualified_predictors = [p for p in elgible_predictors if p.should_predict_contents(contents)]
    # print("Qualified", qualified_predictors)

    return qualified_predictors

