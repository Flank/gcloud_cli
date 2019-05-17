# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.ml.vision import base as vision_base

import httplib2


class DetectDocumentBase(vision_base.MlVisionTestBase):

  def _ExpectDetectDocumentRequest(self, image_path, text=None,
                                   error_message=None, contents=None,
                                   language_hints=None, model=None):
    """Build expected calls to the API for detect-document.

    Args:
      image_path: str, the image path given to command.
      text: str, the text to return in a successful result (if any).
      error_message: str, the error message expected from the API (if any).
      contents: the content field of the Image message to be expected (if any).
          Alternative to image_path.
      language_hints: [str], the list of language hints in the context to be
          expected (if any).
      model: str, the model version to use for the feature.
    """
    ftype = self.messages.Feature.TypeValueValuesEnum.DOCUMENT_TEXT_DETECTION
    image = self.messages.Image()
    if image_path:
      image.source = self.messages.ImageSource(imageUri=image_path)
    if contents:
      image.content = contents
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[self.messages.Feature(type=ftype, model=model)],
            image=image)])
    if language_hints:
      request.requests[0].imageContext = self.messages.ImageContext(
          languageHints=language_hints)
    responses = []
    if text:
      responses.append(
          self.messages.AnnotateImageResponse(
              fullTextAnnotation=(
                  self.messages.TextAnnotation(
                      pages=[self.messages.Page()],
                      text=text))))
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
    ('Alpha', calliope_base.ReleaseTrack.ALPHA, 'builtin/stable'),
    ('Beta', calliope_base.ReleaseTrack.BETA, 'builtin/stable'),
    ('GA', calliope_base.ReleaseTrack.GA, None))
class DetectDocumentCommonTest(DetectDocumentBase):

  def testDetectDocument_Success(self, track, model):
    """Test `gcloud ml vision detect-document` with a remote path."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectDocumentRequest(path_to_image, text='Detected text.',
                                      model=model)
    self.Run('ml vision detect-document {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_LocalPath(self, track, model):
    """Test `gcloud ml vision detect-document` with a local path."""
    self.track = track
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectDetectDocumentRequest(None, text='Detected text.',
                                      contents=b'image', model=model)
    self.Run('ml vision detect-document {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_LanguageHints(self, track, model):
    """Test `gcloud ml vision detect-document` when language hints are given."""
    self.track = track
    path_to_image = 'gs://bucket/object'
    self._ExpectDetectDocumentRequest(path_to_image, text='Detected text.',
                                      language_hints=['ja', 'ko'], model=model)
    self.Run('ml vision detect-document {path} --language-hints ja,ko'.format(
        path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))

  def testDetectDocument_Error(self, track, model):
    """Test `gcloud ml vision detect-document` when an error is returned."""
    self.track = track
    path_to_image = 'https://example.com/fake-file'
    self._ExpectDetectDocumentRequest(path_to_image,
                                      error_message='Not found.', model=model)
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-document {path}'.format(path=path_to_image))


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class DetectDocumentAlphaBetaTest(DetectDocumentBase):

  def testDetectDocument_ModelVersion(self, track):
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectDetectDocumentRequest(path_to_image, text='Detected text.',
                                      model='builtin/latest')
    self.Run('ml vision detect-document {path} '
             '--model-version builtin/latest'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "fullTextAnnotation": {
                "pages": [
                  {}
                ],
                "text": "Detected text."
              }
            }
          ]
        }
    """))


class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    mock_http_client = self.StartObjectPatch(http, 'Http')
    mock_http_client.return_value.request.return_value = \
        (httplib2.Response({'status': 200}), b'')
    self.request_mock = mock_http_client.return_value.request

  @parameterized.parameters(
      (None, 'alpha', b'foo'),
      (None, 'beta', b'foo'),
      (properties.VALUES.billing.LEGACY, 'alpha', None),
      (properties.VALUES.billing.LEGACY, 'beta', None),
      (properties.VALUES.billing.CURRENT_PROJECT, 'alpha', b'foo'),
      (properties.VALUES.billing.CURRENT_PROJECT, 'beta', b'foo'),
      ('bar', 'alpha', b'bar'),
      ('bar', 'beta', b'bar'),
  )
  def testQuotaHeader(self, prop_value, track, header_value):
    properties.VALUES.billing.quota_project.Set(prop_value)
    self.Run(track + ' ml vision detect-document --project=foo {path}'
             .format(path='gs://fake-bucket/fake-file'))
    header = self.request_mock.call_args[0][3].get(b'X-Goog-User-Project', None)
    self.assertEqual(header, header_value)


if __name__ == '__main__':
  cli_test_base.main()
