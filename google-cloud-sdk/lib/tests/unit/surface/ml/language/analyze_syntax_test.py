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
"""Tests for gcloud ml language analyze-syntax."""

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ml.language import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.language import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class AnalyzeSyntaxTest(base.MlLanguageTestBase):
  """Tests for gcloud ml language analyze-syntax."""

  def _CreateResponse(self, tokens, language):
    token_responses = []
    for t in tokens:
      token_responses.append(
          {
              'dependencyEdge': {
                  'headTokenIndex': 0,
                  'label': 'UNKNOWN'
              },
              'lemma': t,
              'partOfSpeech': {
                  'aspect': 'ASPECT_UNKNOWN',
                  'case': 'CASE_UNKNOWN',
                  'form': 'FORM_UNKNOWN',
                  'gender': 'GENDER_UNKNOWN',
                  'mood': 'MOOD_UNKNOWN',
                  'number': 'NUMBER_UNKNOWN',
                  'person': 'PERSON_UNKNOWN',
                  'proper': 'PROPER_UNKNOWN',
                  'reciprocity': 'RECIPROCITY_UNKNOWN',
                  'tag': 'UNKNOWN',
                  'tense': 'TENSE_UNKNOWN',
                  'voice': 'VOICE_UNKNOWN'
              },
              'text': {
                  'beginOffset': 0,
                  'content': t
              }
          }
      )
    response = {
        'language': language,
        'sentences': [
            {
                'text': {
                    'beginOffset': 0,
                    'content': ' '.join(tokens)
                }
            }
        ],
        'tokens': token_responses
    }
    return response

  def _ExpectAnalyzeSyntaxRequest(self, gcs_content_uri=None, content=None,
                                  encoding_type=None, content_type=None,
                                  request_language=None,
                                  response_language='en', tokens=None,
                                  error=None):
    """Build expected requests and responses for the Language client.

    Args:
      gcs_content_uri: str, the expected URI for the document in the request,
          if any.
      content: bytes, the expected content of the document in the request,
          if any.
      encoding_type: str, the expected encoding type of the request.
      content_type: str, the expected document type in the request.
      request_language: str, the expected language of the document in the
          request.
      response_language: str, the expected language of the document in the
          response.
      tokens: [str], list of tokens for expected response.
      error: HttpError to be expected from the client, if any.
    """
    if tokens:
      response = self._CreateResponse(tokens, response_language)
    else:
      response = None
    annotate_request = self.messages.AnalyzeSyntaxRequest(
        document=self.messages.Document(
            gcsContentUri=gcs_content_uri,
            content=content,
            type=content_type,
            language=request_language),
        encodingType=encoding_type)
    if response:
      response = encoding.PyValueToMessage(
          self.messages.AnalyzeSyntaxResponse,
          response
      )
      self.client.documents.AnalyzeSyntax.Expect(annotate_request, response)
    if error:
      self.client.documents.AnalyzeSyntax.Expect(annotate_request,
                                                 exception=error)

  def testBasicResult(self, track):
    """Test that results return correctly."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='They drink',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    pos = self.messages.PartOfSpeech
    recip = pos.ReciprocityValueValuesEnum
    l = self.messages.DependencyEdge.LabelValueValuesEnum
    expected = self.messages.AnalyzeSyntaxResponse(
        language='en',
        sentences=[self.messages.Sentence(
            text=self.messages.TextSpan(
                beginOffset=0,
                content='They drink')
        )],
        tokens=[
            self.messages.Token(
                dependencyEdge=self.messages.DependencyEdge(
                    headTokenIndex=0,
                    label=l.UNKNOWN
                ),
                lemma='They',
                partOfSpeech=pos(
                    aspect=pos.AspectValueValuesEnum.ASPECT_UNKNOWN,
                    case=pos.CaseValueValuesEnum.CASE_UNKNOWN,
                    form=pos.FormValueValuesEnum.FORM_UNKNOWN,
                    gender=pos.GenderValueValuesEnum.GENDER_UNKNOWN,
                    mood=pos.MoodValueValuesEnum.MOOD_UNKNOWN,
                    number=pos.NumberValueValuesEnum.NUMBER_UNKNOWN,
                    person=pos.PersonValueValuesEnum.PERSON_UNKNOWN,
                    proper=pos.ProperValueValuesEnum.PROPER_UNKNOWN,
                    reciprocity=recip.RECIPROCITY_UNKNOWN,
                    tag=pos.TagValueValuesEnum.UNKNOWN,
                    tense=pos.TenseValueValuesEnum.TENSE_UNKNOWN,
                    voice=pos.VoiceValueValuesEnum.VOICE_UNKNOWN
                ),
                text=self.messages.TextSpan(
                    beginOffset=0,
                    content='They')),
            self.messages.Token(
                dependencyEdge=self.messages.DependencyEdge(
                    headTokenIndex=0,
                    label=l.UNKNOWN
                ),
                lemma='drink',
                partOfSpeech=pos(
                    aspect=pos.AspectValueValuesEnum.ASPECT_UNKNOWN,
                    case=pos.CaseValueValuesEnum.CASE_UNKNOWN,
                    form=pos.FormValueValuesEnum.FORM_UNKNOWN,
                    gender=pos.GenderValueValuesEnum.GENDER_UNKNOWN,
                    mood=pos.MoodValueValuesEnum.MOOD_UNKNOWN,
                    number=pos.NumberValueValuesEnum.NUMBER_UNKNOWN,
                    person=pos.PersonValueValuesEnum.PERSON_UNKNOWN,
                    proper=pos.ProperValueValuesEnum.PROPER_UNKNOWN,
                    reciprocity=recip.RECIPROCITY_UNKNOWN,
                    tag=pos.TagValueValuesEnum.UNKNOWN,
                    tense=pos.TenseValueValuesEnum.TENSE_UNKNOWN,
                    voice=pos.VoiceValueValuesEnum.VOICE_UNKNOWN
                ),
                text=self.messages.TextSpan(
                    beginOffset=0,
                    content='drink'))
        ]
    )
    result = self.Run('ml language analyze-syntax --content "They drink"')
    self.assertEqual(expected, result)

  def testBasicOutput(self, track):
    """Test that results print as expected."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='They drink',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language analyze-syntax --content "They drink"')
    self.AssertOutputContains(textwrap.dedent("""\
    {
      "language": "en",
      "sentences": [
        {
          "text": {
            "beginOffset": 0,
            "content": "They drink"
          }
        }
      ],
      "tokens": [
        {
          "dependencyEdge": {
            "headTokenIndex": 0,
            "label": "UNKNOWN"
          },
          "lemma": "They",
          "partOfSpeech": {
            "aspect": "ASPECT_UNKNOWN",
            "case": "CASE_UNKNOWN",
            "form": "FORM_UNKNOWN",
            "gender": "GENDER_UNKNOWN",
            "mood": "MOOD_UNKNOWN",
            "number": "NUMBER_UNKNOWN",
            "person": "PERSON_UNKNOWN",
            "proper": "PROPER_UNKNOWN",
            "reciprocity": "RECIPROCITY_UNKNOWN",
            "tag": "UNKNOWN",
            "tense": "TENSE_UNKNOWN",
            "voice": "VOICE_UNKNOWN"
          },
          "text": {
            "beginOffset": 0,
            "content": "They"
          }
        },
        {
          "dependencyEdge": {
            "headTokenIndex": 0,
            "label": "UNKNOWN"
          },
          "lemma": "drink",
          "partOfSpeech": {
            "aspect": "ASPECT_UNKNOWN",
            "case": "CASE_UNKNOWN",
            "form": "FORM_UNKNOWN",
            "gender": "GENDER_UNKNOWN",
            "mood": "MOOD_UNKNOWN",
            "number": "NUMBER_UNKNOWN",
            "person": "PERSON_UNKNOWN",
            "proper": "PROPER_UNKNOWN",
            "reciprocity": "RECIPROCITY_UNKNOWN",
            "tag": "UNKNOWN",
            "tense": "TENSE_UNKNOWN",
            "voice": "VOICE_UNKNOWN"
          },
          "text": {
            "beginOffset": 0,
            "content": "drink"
          }
        }
      ]
    }
    """))

  def testWithContentFile(self, track):
    """Test result when a content file is given."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='Hello world',
        tokens=['Hello', 'world'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run(
        'ml language analyze-syntax --content-file {}'.format(
            self.test_file))

  def testWithGCSContentFile(self, track):
    """Test that a GCS URL is sent to the service."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        gcs_content_uri='gs://bucket/file',
        tokens=['They', 'eat'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run('ml language analyze-syntax --content-file gs://bucket/file')

  def testWithContentType(self, track):
    """Test result with --content-type flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='<p>They drink.</p>',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.HTML
    )
    self.Run(
        'ml language analyze-syntax --content "<p>They drink.</p>" '
        '--content-type HTML')

  def testWithEncodingType(self, track):
    """Test result with --encoding-type flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='They drink.',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF32,
        content_type=self.content_enum.PLAIN_TEXT
    )
    self.Run(
        'ml language analyze-syntax --content "They drink." '
        '--encoding-type UTF32')

  def testWithLanguage(self, track):
    """Test result with --language flag."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='They drink.',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT,
        request_language='en',
        response_language='en'
    )
    self.Run(
        'ml language analyze-syntax --content "They drink." --language en')

  def testWithAllFlags(self, track):
    """Test result with --language, --content-type, --encoding-type flags."""
    self.SetTrack(track)
    self._ExpectAnalyzeSyntaxRequest(
        content='<p>They drink.</p>',
        tokens=['They', 'drink'],
        encoding_type=self.syntax_encoding_enum.UTF32,
        content_type=self.content_enum.HTML,
        request_language='en',
        response_language='en'
    )
    self.Run(
        'ml language analyze-syntax --content "<p>They drink.</p>" '
        '--language en --content-type HTML --encoding-type UTF32')

  def testWithNonGCSUrl(self, track):
    """Assert ContentFileError for a non-GCS URL in --content-file."""
    self.SetTrack(track)
    non_gcs_url = 'https://bucket/file'
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language analyze-syntax --content-file {}'.format(
          non_gcs_url))
    self.AssertErrContains(
        'Could not find --content-file [https://bucket/file]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)')

  def testWithEmptyContent(self, track):
    """Assert ContentError is raised if empty --content is given."""
    self.SetTrack(track)
    with self.assertRaises(util.ContentError):
      self.Run('ml language analyze-syntax --content ""')
    self.AssertErrContains('The content provided is empty. Please provide '
                           'language content to analyze.')

  def testWithNonExistentFile(self, track):
    """Assert ContentFileError is raised for non-existent local file."""
    self.SetTrack(track)
    with self.assertRaises(util.ContentFileError):
      self.Run('ml language analyze-syntax --content-file {}'.format(
          self.test_file + '-no-exist'))
    self.AssertErrContains(
        'Could not find --content-file [{}]. Content file '
        'must be a path to a local file or a Google Cloud Storage URL '
        '(format: `gs://bucket_name/object_name`)'.format(
            self.test_file + '-no-exist'))

  def testWithHttpError(self, track):
    """Assert HttpException is raised when API returns an error."""
    self.SetTrack(track)
    # These details do not show up in the error format string.
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
    self._ExpectAnalyzeSyntaxRequest(
        gcs_content_uri='gs://fake/fake',
        encoding_type=self.syntax_encoding_enum.UTF8,
        content_type=self.content_enum.PLAIN_TEXT,
        error=error
    )
    with self.assertRaises(exceptions.HttpException):
      self.Run('ml language analyze-syntax --content-file gs://fake/fake')
    self.AssertErrContains('The file does not exist.')


if __name__ == '__main__':
  test_case.main()
