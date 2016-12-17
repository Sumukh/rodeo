#!/usr/bin/env python
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script uses the Vision API's label detection capabilities to find a label
based on an image's content.

To run the example, install the necessary libraries by running:

    pip install -r requirements.txt

Run the script on an image to get a label, E.g.:

    ./label.py <path-to-image>
"""

# [START import_libraries]
import argparse
import base64
import json

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
# Cache
import percache
# [END import_libraries]

cache = percache.Cache("./.cloud-vision-cache")

@cache
def main(photo_file):
    """Run a label request on a single image"""

    # [START authenticate]
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('vision', 'v1', credentials=credentials)
    # [END authenticate]

    # [START construct_request]
    with open(photo_file, 'rb') as image:
        image_content = base64.b64encode(image.read())
        service_request = service.images().annotate(body={
            'requests': [{
                'image': {
                    'content': image_content.decode('UTF-8')
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': 3
                }, {
                    'type': 'FACE_DETECTION',
                    'maxResults': 2,
                }, {
                    'type': 'LANDMARK_DETECTION',
                    'maxResults': 2,
                }, {
                    'type': 'LOGO_DETECTION',
                    'maxResults': 3,
                }, {
                    'type': 'IMAGE_PROPERTIES'
                }, {
                    'type': 'TEXT_DETECTION',
                    'maxResults': 2,
                }]
            }]
        })
        # [END construct_request]
        # [START parse_response]
        response = service_request.execute()
        # for resp in response['responses']:
        #     label = resp['labelAnnotations'][0]['description']
        #     print('Found label: %s for %s' % (label, photo_file))
        # [END parse_response]
        # print(json.dumps(response, indent=2))
        return response

def serialize_response(file_name):
    data = main(file_name)
    responses = data['responses'][0]
    relationalized_data = {}
    # print(json.dumps(data, indent=2))
    if 'labelAnnotations' in responses:
        top_3 = '-'.join([label['description'] for label in responses['labelAnnotations']])
        relationalized_data['object_labels'] = top_3
    if 'landmarkAnnotations' in responses:
        top_3 = '-'.join([label['description'] for label in responses['landmarkAnnotations']])
        relationalized_data['landmark'] = top_3
    if 'faceAnnotations' in responses:
        face = responses['faceAnnotations'][0]
        relationalized_data['has_face'] = "Face Roll: {} Tilt: {} Headwear: {} Confidence: {}".format(
                face['rollAngle'], face['tiltAngle'], face['headwearLikelihood'], face['detectionConfidence'])
        relationalized_data['emotion'] = "Joy: {}, Suprise: {}, Sorrow: {}, Anger: {}".format(
            face['joyLikelihood'], face['surpriseLikelihood'], face['sorrowLikelihood'], face['angerLikelihood'])
    if 'logoAnnotations' in responses:
        top_3 = '-'.join([label['description'] for label in responses['logoAnnotations']])
        relationalized_data['logo'] = top_3
    if 'textAnnotations' in responses:
        top_3 = '-'.join([label['description'] for label in responses['textAnnotations']])
        relationalized_data['text'] = top_3
    return relationalized_data


# [START run_application]
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image_file', help='The image you\'d like to label.')
    args = parser.parse_args()
    print(json.dumps(serialize_response(args.image_file), indent=2))
# [END run_application]