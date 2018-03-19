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
class DetectWebTest(vision_base.MlVisionTestBase):

  def _ExpectDetectWebRequest(self, image_path, success=False,
                              error_message=None, max_results=None,
                              contents=None):
    """Build expected requests/responses for detect-web command.

    Args:
      image_path: str, the path to the image to analyze.
      success: bool, if True a successful image properties response will be
          added to the client.
      error_message: str, the error message expected from the API (if any).
      max_results: int, the number of max results requested (if any).
      contents: the content field of the Image message to be expected (if any).
          Alternative to image_path.
    """
    feature = self.messages.Feature(
        type=self.messages.Feature.TypeValueValuesEnum.WEB_DETECTION)
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
        'webDetection': {
            'fullMatchingImages': [{
                'score': 0.5,
                'url': 'http://www.fakewebsite.com'}],
            'pagesWithMatchingImages': [{
                'score': 0.5,
                'url': 'http://www.myfakesite.com'}]
        }
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

  def testDetectWeb_Success(self, track):
    """Test `ml vision detect-web` runs and outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectWebRequest(path_to_image, success=True)
    self.Run('ml vision detect-web {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "webDetection": {
                "fullMatchingImages": [
                  {
                    "score": 0.5,
                    "url": "http://www.fakewebsite.com"
                  }
                ],
                "pagesWithMatchingImages": [
                  {
                    "score": 0.5,
                    "url": "http://www.myfakesite.com"
                  }
                ]
              }
            }
          ]
        }
    """))

  def testDetectWeb_LocalPath(self, track):
    """Test `ml vision detect-web` with a local image path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectDetectWebRequest(None, success=True, contents=bytes('image'))
    self.Run('ml vision detect-web {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "webDetection": {
                "fullMatchingImages": [
                  {
                    "score": 0.5,
                    "url": "http://www.fakewebsite.com"
                  }
                ],
                "pagesWithMatchingImages": [
                  {
                    "score": 0.5,
                    "url": "http://www.myfakesite.com"
                  }
                ]
              }
            }
          ]
        }
    """))

  def testDetectWeb_MaxResults(self, track):
    """Test `ml vision detect-web` with `--max-results` flag."""
    self.track = track
    path_to_image = 'https://example.com/fake-file'
    self._ExpectDetectWebRequest(path_to_image, success=True,
                                 max_results=4)
    self.Run('ml vision detect-web {path} '
             '--max-results 4'.format(path=path_to_image))

  def testDetectWeb_Error(self, track):
    """Test `ml vision detect-web` when a response contains an error."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectWebRequest(path_to_image,
                                 error_message='Not found.')
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-web {path}'.format(path=path_to_image))


if __name__ == '__main__':
  test_case.main()
