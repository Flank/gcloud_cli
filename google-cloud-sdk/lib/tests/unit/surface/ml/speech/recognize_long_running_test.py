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
"""gcloud ml speech recognize-long-running unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.speech import util
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.speech import base as speech_base


LONG_RUNNING_RESPONSE = ('type.googleapis.com/google.cloud.speech.{version}.'
                         'LongRunningRecognizeResponse')


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class RecognizeLongRunningTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech recognize-long-running`."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def SetUp(self):
    self.long_file = self.Resource('tests', 'unit', 'command_lib', 'ml',
                                   'speech', 'testdata', 'sample.raw')

  def testBasicOutput_Async(self, track):
    """Test recognize-long-running command basic output with --async flag."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object --language-code '
        'en-US --sample-rate 16000 --async'
    )
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testWithNoDefaults_Async(self, track):
    """Test recognize-long-running command with all flags set."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='es-ES',
        sample_rate=22000,
        max_alternatives=2,
        result='12345',
        hints=['Hola'],
        encoding='FLAC',
        enable_word_time_offsets=True,
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object --language-code '
        'es-ES --sample-rate 22000 --max-alternatives 2 --hints Hola --async '
        '--encoding FLAC --include-word-time-offsets'
    )
    self.assertEqual(expected, actual)

  def testWithLocalFile_Async(self, track):
    """Test recognize-long-running command with local content."""
    self.SetUpForTrack(track)
    with open(self.long_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectLongRunningRecognizeRequest(
        content=contents,
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None
    )
    expected = self.messages.Operation(name='12345')
    actual = self.Run(
        'ml speech recognize-long-running {} --language-code en-US '
        '--sample-rate 16000 --async'.format(self.long_file))
    self.assertEqual(expected, actual)

  def testResults_Sync(self, track):
    """Test recognize-long-running command waits for operation results."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        hints=[],
        encoding=None
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hello world.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hello world.'}]}]}
    self.Run('ml speech recognize-long-running gs://bucket/object '
             '--language-code en-US --sample-rate 16000')
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testWithNoDefaults_Sync(self, track):
    """Test recognize-long-running command with all flags set except --async."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='es-ES',
        sample_rate=22000,
        max_alternatives=2,
        result='12345',
        hints=['Hola.'],
        encoding=None,
        enable_word_time_offsets=True
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hola.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hola.'}]}]}
    self.Run('ml speech recognize-long-running gs://bucket/object '
             '--language-code es-ES --sample-rate 22000 --hints Hola. '
             '--max-alternatives 2 --include-word-time-offsets')
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testWithLocalFile_Sync(self, track):
    """Test recognize-long-running command with local source (synchronous)."""
    self.SetUpForTrack(track)
    with open(self.long_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectLongRunningRecognizeRequest(
        content=contents,
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        hints=[],
        encoding=None
    )
    self._ExpectPollOperationRequests('12345', 3, results=['Hello world.'])
    expected = {
        '@type': LONG_RUNNING_RESPONSE.format(version=self.version),
        'results': [{'alternatives': [{'confidence': 0.8,
                                       'transcript': 'Hello world.'}]}]}
    self.Run('ml speech recognize-long-running {} --language-code en-US '
             '--sample-rate 16000'.format(self.long_file))
    self.assertEqual(json.loads(self.GetOutput()), expected)

  def testRaisesError(self, track):
    """Test recognize-long-running command raises HttpException on error."""
    self.SetUpForTrack(track)
    error = http_error.MakeDetailedHttpError(code=400, message='Error message',
                                             details=self.sample_error_details)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        hints=[],
        encoding=None,
        error=error
    )
    with self.assertRaisesRegex(exceptions.HttpException, r'Error message'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000')

  def testRaisesOperationError(self, track):
    """Test recognize-long-running command if operation contains error."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        hints=[],
        encoding=None,
        result='12345'
    )
    self._ExpectPollOperationRequests(
        '12345', 3, error_json={'code': 400, 'message': 'Message.'})
    with self.assertRaisesRegex(waiter.OperationError,
                                r'Message.'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000')

  def testMissingRequiredAudioFilePositional(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        'argument AUDIO: Must be specified.'):
      self.Run('ml speech recognize-long-running --language-code en-US '
               '--sample-rate 16000')

  def testMissingRequiredLanguageFlag(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        '--language-code must be specified'):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--sample-rate 16000')

  def testInvalidFlagValues(self, track):
    """Test recognize-long-running command exits if invalid flag value given."""
    self.SetUpForTrack(track)
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--max-alternatives notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--filter-profanity invalidvalue')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--encoding NOT_AN_ENCODING')

  def testAudioError(self, track):
    """Test recognize-long-running raises AudioException with invalid audio."""
    self.SetUpForTrack(track)
    audio_path = self.long_file + 'x'
    with self.AssertRaisesExceptionMatches(util.AudioException,
                                           '[{}]'.format(audio_path)):
      self.Run('ml speech recognize-long-running {} --language-code en-US '
               '--sample-rate 16000'.format(self.long_file + 'x'))


class RecognizeLongRunningSpecificTrackTest(speech_base.MlSpeechTestBase,
                                            parameterized.TestCase):
  """Class to test `gcloud ml speech recognize-long-running`."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA))
  def testIncludeWordConfidence_Async(self, track):
    """Test recognize-long-running command basic output with --async flag."""
    self.SetUpForTrack(track)
    self._ExpectLongRunningRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=16000,
        max_alternatives=1,
        result='12345',
        encoding=None,
        enable_word_confidence=True
    )

    actual = self.Run(
        'ml speech recognize-long-running gs://bucket/object '
        '    --language-code en-US '
        '    --sample-rate 16000 '
        '    --async '
        '    --include-word-confidence'
    )

    expected = self.messages.Operation(name='12345')
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))


if __name__ == '__main__':
  test_case.main()
