# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""beta ml vision tests."""

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


@parameterized.named_parameters(
    ('Alpha', base.ReleaseTrack.ALPHA),
    ('Beta', base.ReleaseTrack.BETA),
    ('GA', base.ReleaseTrack.GA))
class DetectFacesTest(vision_base.MlVisionTestBase):

  def _ExpectDetectFacesRequest(self, image_path, success=False,
                                error_message=None, max_results=None,
                                contents=None):
    """Build expected detect-faces requests and responses.

    Args:
      image_path: str, the path to the image.
      success: bool, if True, a successful response is desired.
      error_message: str, the error message expected from the API (if any).
      max_results: int, the max number of results requested by the caller (if
          any).
      contents: the content of the Image message to be expected (if any).
          Alternative to image_path.
    """
    feature = self.messages.Feature(
        type=self.messages.Feature.TypeValueValuesEnum.FACE_DETECTION)
    if max_results:
      feature.maxResults = max_results
    image = self.messages.Image()
    if image_path:
      image.source = self.messages.ImageSource(imageUri=image_path)
    if contents:
      image.content = contents
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[feature],
            image=image)])
    response = {
        'faceAnnotations': [{
            'angerLikelihood':
                'VERY_UNLIKELY',
            'blurredLikelihood':
                'VERY_UNLIKELY',
            'boundingPoly': {
                'vertices': [{
                    'x': 122
                }, {
                    'x': 336
                }, {
                    'x': 336,
                    'y': 203
                }, {
                    'x': 122,
                    'y': 203
                }]
            },
            'detectionConfidence':
                0.86162376,
            'fdBoundingPoly': {
                'vertices': [{
                    'x': 153,
                    'y': 34
                }, {
                    'x': 299,
                    'y': 34
                }, {
                    'x': 299,
                    'y': 180
                }, {
                    'x': 153,
                    'y': 180
                }]
            },
            'headwearLikelihood':
                'VERY_UNLIKELY',
            'joyLikelihood':
                'VERY_UNLIKELY',
            'landmarkingConfidence':
                0.42813218,
            'landmarks': [{
                'position': {
                    'x': 189.72849,
                    'y': 82.96587,
                    'z': -0.00075325265
                },
                'type': 'LEFT_EYE'
            }, {
                'position': {
                    'x': 258.15857,
                    'y': 78.31779,
                    'z': -4.623273
                },
                'type': 'RIGHT_EYE'
            }],
            'panAngle':
                -4.069568,
            'rollAngle':
                -5.149212,
            'sorrowLikelihood':
                'VERY_UNLIKELY',
            'surpriseLikelihood':
                'VERY_UNLIKELY',
            'tiltAngle':
                -13.083284,
            'underExposedLikelihood':
                'VERY_UNLIKELY'
        }]
    }
    response = encoding.PyValueToMessage(
        self.messages.AnnotateImageResponse,
        response)
    responses = []
    if success:
      responses.append(response)
    if error_message:
      response = encoding.PyValueToMessage(
          self.messages.AnnotateImageResponse,
          {'error': {'code': 400,
                     'details': [],
                     'message': error_message}})
      responses.append(response)
    response = self.messages.BatchAnnotateImagesResponse(responses=responses)
    self.client.images.Annotate.Expect(request,
                                       response=response)

  def testDetectFaces_Success(self, track):
    """Test `gcloud ml vision detect-faces` runs & outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectFacesRequest(path_to_image, success=True)
    self.Run('ml vision detect-faces {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "faceAnnotations": [
                {
                  "angerLikelihood": "VERY_UNLIKELY",
                  "blurredLikelihood": "VERY_UNLIKELY",
                  "boundingPoly": {
                    "vertices": [
                      {
                        "x": 122
                      },
                      {
                        "x": 336
                      },
                      {
                        "x": 336,
                        "y": 203
                      },
                      {
                        "x": 122,
                        "y": 203
                      }
                    ]
                  },
                  "detectionConfidence": 0.86162376,
                  "fdBoundingPoly": {
                    "vertices": [
                      {
                        "x": 153,
                        "y": 34
                      },
                      {
                        "x": 299,
                        "y": 34
                      },
                      {
                        "x": 299,
                        "y": 180
                      },
                      {
                        "x": 153,
                        "y": 180
                      }
                    ]
                  },
                  "headwearLikelihood": "VERY_UNLIKELY",
                  "joyLikelihood": "VERY_UNLIKELY",
                  "landmarkingConfidence": 0.42813218,
                  "landmarks": [
                    {
                      "position": {
                        "x": 189.72849,
                        "y": 82.96587,
                        "z": -0.00075325265
                      },
                      "type": "LEFT_EYE"
                    },
                    {
                      "position": {
                        "x": 258.15857,
                        "y": 78.31779,
                        "z": -4.623273
                      },
                      "type": "RIGHT_EYE"
                    }
                  ],
                  "panAngle": -4.069568,
                  "rollAngle": -5.149212,
                  "sorrowLikelihood": "VERY_UNLIKELY",
                  "surpriseLikelihood": "VERY_UNLIKELY",
                  "tiltAngle": -13.083284,
                  "underExposedLikelihood": "VERY_UNLIKELY"
                }
              ]
            }
          ]
        }
    """))

  def testDetectFaces_LocalPath(self, track):
    """Test `gcloud ml vision detect-faces with a local image path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectDetectFacesRequest(None, success=True, contents=bytes('image'))
    self.Run('ml vision detect-faces {path}'.format(path=path_to_image))

  def testDetectFaces_MaxResults(self, track):
    """Test `gcloud ml vision detect-faces with --max-results specified."""
    self.track = track
    path_to_image = 'https://example.com/fake-image'
    self._ExpectDetectFacesRequest(path_to_image, success=True,
                                   max_results=4)
    self.Run('ml vision detect-faces {path} '
             '--max-results 4'.format(path=path_to_image))

  def testDetectFaces_Error(self, track):
    """Test `gcloud ml vision detect-faces with an error."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectFacesRequest(path_to_image,
                                   error_message='Not found.')
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-faces {path}'.format(path=path_to_image))


if __name__ == '__main__':
  test_case.main()
