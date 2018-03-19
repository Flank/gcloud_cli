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
"""Tests for gcloud ml language classify-text."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ml.language import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.language import base as language_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class ClassifyTextTest(language_base.MlLanguageTestBase):
  """Test for the ml language classify command."""

  def _ExpectClassifyTextRequest(self,
                                 gcs_content_uri=None,
                                 content=None,
                                 content_type=None,
                                 language=None,
                                 categories=None,
                                 error=None):
    """Build expected requests and responses for ClassifyText.

    Args:
      gcs_content_uri: str, the expected URI for the document in the request,
          if any.
      content: bytes, the expected content of the document in the request,
          if any.
      content_type: str, the expected document type in the request.
      language: str, the expected language of the document in the
          request.
      categories: {str, float} the dict of {category:confidence level} values
          to be returned in the response.
      error: HttpError to be expected from the client, if any.
    """
    if categories:
      json_response = self._CreateCategoryResponse(categories)
    else:
      json_response = None
    annotate_request = self.messages.ClassifyTextRequest(
        document=self.messages.Document(
            gcsContentUri=gcs_content_uri,
            content=content,
            type=content_type,
            language=language))
    if json_response:
      response = encoding.PyValueToMessage(
          self.messages.ClassifyTextResponse,
          json_response
      )
      self.client.documents.ClassifyText.Expect(annotate_request, response)
    if error:
      self.client.documents.ClassifyText.Expect(annotate_request,
                                                exception=error)

  def _CreateCategoryResponse(self, categories):
    categories_response = []
    if categories:
      for category, confidence in categories.iteritems():
        categories_response.append({'name': category,
                                    'confidence': confidence})
    return {'categories': categories_response}

  def testBasicOutput(self, track):
    self.SetTrack(track)
    content = 'Long Political Text'
    self._ExpectClassifyTextRequest(
        content=content,
        categories={'/News/Politics': 0.96},
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language classify-text --content "{}"'.format(content))
    self.AssertOutputEquals("""\
   {
  "categories": [
    {
      "confidence": 0.96,
      "name": "/News/Politics"
    }
  ]
 }
 """, normalize_space=True)

  def testBasicResult(self, track):
    self.SetTrack(track)
    content = 'Long Political Text'
    self._ExpectClassifyTextRequest(
        content=content,
        categories={'/News/Politics': 0.96},
        content_type=self.content_enum.PLAIN_TEXT
    )

    expected = encoding.PyValueToMessage(
        self.messages.ClassifyTextResponse,
        self._CreateCategoryResponse({'/News/Politics': 0.96}))
    actual = self.Run(
        'ml language classify-text --content "{}"'.format(content))
    self.assertEqual(actual, expected)

  def testWithContentFile(self, track):
    self.SetTrack(track)
    self._ExpectClassifyTextRequest(
        content='Hello world',
        categories={'/Reference/Geographic Reference': 0.90},
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language classify-text --content-file {}'.format(
        self.test_file))

  def testWithGCSContentFile(self, track):
    self.SetTrack(track)
    self._ExpectClassifyTextRequest(
        gcs_content_uri='gs://bucket/file',
        categories={'/Reference/Geographic Reference': 0.90},
        content_type=self.content_enum.PLAIN_TEXT)
    self.Run('ml language classify-text --content-file gs://bucket/file')

  def testWithContentType(self, track):
    self.SetTrack(track)
    self._ExpectClassifyTextRequest(
        gcs_content_uri='gs://bucket/funny_file',
        categories={
            '/Arts & Entertainment/Fun & Trivia': 0.67,
            '/Arts & Entertainment/Humor': 0.87
        },
        content_type=self.content_enum.HTML)
    self.Run('ml language classify-text --content-file gs://bucket/funny_file '
             '--content-type HTML')

  def testWithLanguage(self, track):
    self.SetTrack(track)
    content = 'Knock, Knock! Whos There?'
    self._ExpectClassifyTextRequest(
        content=content,
        categories={
            '/Arts & Entertainment/Fun & Trivia': 0.67,
            '/Arts & Entertainment/Humor': 0.87
        },
        language='eng',
        content_type=self.content_enum.PLAIN_TEXT)
    self.Run('ml language classify-text --content "{}" --language eng '.format(
        content))

  def testWithAllFlags(self, track):
    self.SetTrack(track)
    content = '<p>Blue Dresses in Autumn Weather on the Beach.</p>'
    self._ExpectClassifyTextRequest(
        content=content,
        categories={
            '/Beauty & Fitness/Fashion & Style': 0.67,
            '/Beauty & Fitness/Fitness': 0.87
        },
        language='eng',
        content_type=self.content_enum.HTML)
    self.Run('ml language classify-text --content "{}" --language eng '
             '--content-type HTML'.format(content))

  def testWithNonGCSUrl(self, track):
    self.SetTrack(track)
    non_gcs_url = 'http://bucket/file'
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language classify-text --content-file {}'.format(
          non_gcs_url))
    self.AssertErrContains(
        'Could not find --content-file [http://bucket/file]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)')

  def testWithEmptyContent(self, track):
    self.SetTrack(track)
    with self.assertRaises(util.ContentError):
      self.Run('ml language classify-text  --content ""')
    self.AssertErrContains('The content provided is empty. Please provide '
                           'language content to analyze.')

  def testWithNonExistentFile(self, track):
    self.SetTrack(track)
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language classify-text --content-file fake-file.txt')
    self.AssertErrContains(
        'Could not find --content-file [fake-file.txt]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)')

  def testWithHttpError(self, track):
    self.SetTrack(track)
    details = [
        {'@type': 'type.googleapis.com/google.rpc.BadRequest',
         'fieldViolations': [
             {
                 'field': 'document.gcs_content_uri',
                 'description': 'Description of violation'
             }
         ]
        },
        {'@type': 'type.googleapis.com/google.rpc.DebugInfo',
         'detail': '[ORIGINAL ERROR] original error message'}
    ]
    error = http_error.MakeDetailedHttpError(details=details,
                                             message='The file does not exist.')
    self._ExpectClassifyTextRequest(
        gcs_content_uri='gs://fake/fake',
        content_type=self.content_enum.PLAIN_TEXT,
        error=error)
    with self.assertRaises(exceptions.HttpException):
      self.Run('ml language classify-text --content-file '
               'gs://fake/fake')
    self.AssertErrContains('The file does not exist.')


if __name__ == '__main__':
  test_case.main()
