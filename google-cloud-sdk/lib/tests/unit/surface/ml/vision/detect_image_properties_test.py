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

from __future__ import absolute_import
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


class DetectImagePropertiesBase(vision_base.MlVisionTestBase):

  def _ExpectDetectImagePropertiesRequest(self, image_path, success=False,
                                          error_message=None, contents=None,
                                          model=None):
    """Build expected requests/responses for image-properties command.

    Args:
      image_path: str, the path to the image to analyze.
      success: bool, if True a successful image properties response will be
          added to the client.
      error_message: str, the error message expected from the API (if any).
      contents: bytes, the content field of the Image message to be expected
          (if any). Alternative to image_path.
      model: str, the model version to use for the feature.
    """
    ftype = self.messages.Feature.TypeValueValuesEnum.IMAGE_PROPERTIES
    image = self.messages.Image()
    if image_path:
      image.source = self.messages.ImageSource(imageUri=image_path)
    if contents:
      image.content = contents
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[self.messages.Feature(type=ftype, model=model)],
            image=image)])
    responses = []
    if success:
      responses.append(
          self.messages.AnnotateImageResponse(
              imagePropertiesAnnotation=(
                  self.messages.ImageProperties(
                      dominantColors=(
                          self.messages.DominantColorsAnnotation(
                              colors=[self.messages.ColorInfo(
                                  color=self.messages.Color(alpha=0.5,
                                                            blue=0.5,
                                                            green=0.5,
                                                            red=0.5),
                                  pixelFraction=0.5,
                                  score=0.5)]))))))
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


@parameterized.named_parameters(
    ('Alpha', base.ReleaseTrack.ALPHA, 'builtin/stable'),
    ('Beta', base.ReleaseTrack.BETA, 'builtin/stable'),
    ('GA', base.ReleaseTrack.GA, None))
class DetectImagePropertiesCommonTest(DetectImagePropertiesBase):

  def testDetectImageProperties_Successful(self, track, model):
    """Test `vision detect-image-properties` runs & outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectImagePropertiesRequest(path_to_image, success=True,
                                             model=model)
    self.Run('ml vision detect-image-properties {path}'
             .format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "imagePropertiesAnnotation": {
                "dominantColors": {
                  "colors": [
                    {
                      "color": {
                        "alpha": 0.5,
                        "blue": 0.5,
                        "green": 0.5,
                        "red": 0.5
                      },
                      "pixelFraction": 0.5,
                      "score": 0.5
                    }
                  ]
                }
              }
            }
          ]
        }
    """))

  def testDetectImageProperties_LocalPath(self, track, model):
    """Test `detect-image-properties` with a local image path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectDetectImagePropertiesRequest(None, success=True,
                                             contents=b'image',
                                             model=model)
    self.Run('ml vision detect-image-properties {path}'
             .format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "imagePropertiesAnnotation": {
                "dominantColors": {
                  "colors": [
                    {
                      "color": {
                        "alpha": 0.5,
                        "blue": 0.5,
                        "green": 0.5,
                        "red": 0.5
                      },
                      "pixelFraction": 0.5,
                      "score": 0.5
                    }
                  ]
                }
              }
            }
          ]
        }
    """))

  def testDetectImageProperties_Error(self, track, model):
    """Test `gcloud ml vision detect-image-properties` with an error message."""
    self.track = track
    path_to_image = 'https://example.com/fake-file'
    self._ExpectDetectImagePropertiesRequest(path_to_image,
                                             error_message='Not found.',
                                             model=model)
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-image-properties {path}'.format(
          path=path_to_image))


@parameterized.named_parameters(
    ('Alpha', base.ReleaseTrack.ALPHA),
    ('Beta', base.ReleaseTrack.BETA))
class DetectImagePropertiesAlphaBetaTest(DetectImagePropertiesBase):

  def testDetectImageProperties_ModelVersion(self, track):
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectImagePropertiesRequest(path_to_image, success=True,
                                             model='builtin/latest')
    self.Run('ml vision detect-image-properties {path} '
             '--model-version builtin/latest'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "imagePropertiesAnnotation": {
                "dominantColors": {
                  "colors": [
                    {
                      "color": {
                        "alpha": 0.5,
                        "blue": 0.5,
                        "green": 0.5,
                        "red": 0.5
                      },
                      "pixelFraction": 0.5,
                      "score": 0.5
                    }
                  ]
                }
              }
            }
          ]
        }
    """))


if __name__ == '__main__':
  test_case.main()
