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

"""Base class for all ml speech tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding as apitools_encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.speech import util
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

from six.moves import range  # pylint: disable=redefined-builtin


class MlSpeechTestBase(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):
  """Base class for gcloud ml speech command unit tests."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1',
      calliope_base.ReleaseTrack.BETA: 'v1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.track = None
    self.version = None
    self.client = None
    self.messages = None

    self.long_file = self.Resource('tests', 'unit', 'api_lib', 'ml', 'speech',
                                   'testdata', 'sample.raw')
    self.sample_error_details = [
        {'@type': 'type.googleapis.com/google.rpc.DebugInfo',
         'detail': ('[ORIGINAL ERROR] generic::invalid_argument: '
                    'Invalid recognition \'config\': bad max_alternatives.')
        }
    ]
    self.StartPatch('time.sleep')

  def SetUpForTrack(self, track):
    self.track = track

    self.version = self._VERSIONS_FOR_RELEASE_TRACKS[track]
    self.client = mock.Client(
        client_class=apis.GetClientClass(util.SPEECH_API, self.version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(util.SPEECH_API, self.version)

  def _MakeRecognizeRequest(self,
                            request_type,
                            content=None,
                            uri=None,
                            enable_word_time_offsets=False,
                            language='en-US',
                            encoding=None,
                            sample_rate=None,
                            hints=None,
                            max_alternatives=None,
                            filter_profanity=False,
                            enable_word_confidence=None,
                            enable_speaker_diarization=None,
                            speaker_count=None,
                            additional_language_codes=None):
    request = request_type(
        audio=self.messages.RecognitionAudio(content=content,
                                             uri=uri),
        config=self.messages.RecognitionConfig(
            enableWordTimeOffsets=enable_word_time_offsets,
            languageCode=language,
            encoding=self.messages.RecognitionConfig.EncodingValueValuesEnum(
                encoding or 'ENCODING_UNSPECIFIED'),
            sampleRateHertz=sample_rate,
            speechContexts=([
                self.messages.SpeechContext(phrases=hints or [])]),
            profanityFilter=filter_profanity,
            maxAlternatives=max_alternatives)
    )

    try:
      # Command default value
      request.config.enableWordConfidence = False
      request.config.enableSpeakerDiarization = False
    except AttributeError:
      pass  # This is expected for some API versions
    if enable_word_confidence is not None:
      request.config.enableWordConfidence = enable_word_confidence
    if enable_speaker_diarization is not None:
      request.config.enableSpeakerDiarization = enable_speaker_diarization
    if speaker_count is not None:
      request.config.diarizationSpeakerCount = speaker_count
    if additional_language_codes is not None:
      request.config.alternativeLanguageCodes = additional_language_codes
    return request

  def _ExpectRecognizeRequest(self,
                              content=None,
                              uri=None,
                              enable_word_time_offsets=False,
                              language='en-US',
                              encoding=None,
                              sample_rate=None,
                              hints=None,
                              max_alternatives=None,
                              filter_profanity=False,
                              enable_word_confidence=None,
                              results=None,
                              error=None,
                              enable_speaker_diarization=None,
                              speaker_count=None,
                              additional_language_codes=None):
    """Expect request to client.speech.Recognize method."""
    request = self._MakeRecognizeRequest(
        self.messages.RecognizeRequest, content, uri, enable_word_time_offsets,
        language, encoding, sample_rate, hints, max_alternatives,
        filter_profanity, enable_word_confidence, enable_speaker_diarization,
        speaker_count, additional_language_codes)
    if results:
      response = self.messages.RecognizeResponse(
          results=[
              self.messages.SpeechRecognitionResult(
                  alternatives=[
                      self.messages.SpeechRecognitionAlternative(
                          confidence=0.8, transcript=text)
                      for text in results])])
    else:
      response = None
    self.client.speech.Recognize.Expect(
        request,
        response,
        exception=error)

  def _ExpectLongRunningRecognizeRequest(self,
                                         content=None,
                                         uri=None,
                                         language='en-US',
                                         enable_word_time_offsets=False,
                                         encoding=None,
                                         sample_rate=None,
                                         hints=None,
                                         max_alternatives=None,
                                         filter_profanity=False,
                                         enable_word_confidence=None,
                                         result=None,
                                         error=None,
                                         enable_speaker_diarization=None,
                                         speaker_count=None,
                                         additional_language_codes=None):
    """Expect request to client.speech.Longrunningrecognize method."""
    request = self._MakeRecognizeRequest(
        self.messages.LongRunningRecognizeRequest, content, uri,
        enable_word_time_offsets, language, encoding, sample_rate, hints,
        max_alternatives, filter_profanity, enable_word_confidence,
        enable_speaker_diarization, speaker_count, additional_language_codes)
    response = self.messages.Operation(name=result) if result else None
    self.client.speech.Longrunningrecognize.Expect(
        request,
        response,
        exception=error)

  def _GetOperationResponse(self, operation_id, results=None, error_json=None):
    """Build operation response."""
    operation = self.messages.Operation(name=operation_id)
    if results:
      operation.done = True
      operation.response = apitools_encoding.PyValueToMessage(
          self.messages.Operation.ResponseValue,
          {'@type': ('type.googleapis.com/google.cloud.speech.{}.LongRunning'
                     'RecognizeResponse').format(self.version),
           'results': [
               {'alternatives': [{'confidence': 0.8, 'transcript': text}
                                 for text in results]}]})
    if error_json:
      operation.done = True
      operation.error = apitools_encoding.PyValueToMessage(self.messages.Status,
                                                           error_json)
    return operation

  def _ExpectGetOperationRequest(self, operation_id, results=None,
                                 error_json=None):
    """Expect request to client.operations.Get method."""
    request = self.messages.SpeechOperationsGetRequest(name=operation_id)
    response = self._GetOperationResponse(operation_id, results=results,
                                          error_json=error_json)
    self.client.operations.Get.Expect(request, response)

  def _ExpectPollOperationRequests(self, operation_id, attempts,
                                   results=None, error_json=None):
    """Build polling requests to client.operations.Get method."""
    for _ in range(0, attempts - 1):
      self._ExpectGetOperationRequest(operation_id)
    self._ExpectGetOperationRequest(operation_id, results, error_json)
