# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""gcloud ml speech recognize unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.speech import util
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml.speech import base as speech_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class RecognizeTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech recognize`."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1p1beta1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def SetUp(self):
    self.short_file = self.Resource('tests', 'unit', 'command_lib', 'ml',
                                    'speech', 'testdata', 'sample.flac')

  def testBasicOutput(self, track):
    """Test recognize command basic output with default flag values."""
    self.SetUpForTrack(track)
    self._ExpectRecognizeRequest(uri='gs://bucket/object', language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 results=['Transcribed text'])
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Transcribed text')])])
    actual = self.Run(
        'ml speech recognize gs://bucket/object --language-code en-US')
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testWithNoDefaults(self, track):
    """Test recognize command with no default flag values."""
    self.SetUpForTrack(track)
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object', language='es-ES', sample_rate=22000,
        max_alternatives=2, hints=['Bueno'], results=['Bueno', 'Buena'],
        encoding='OGG_OPUS', enable_word_time_offsets=True)
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Bueno'),
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Buena')])])
    actual = self.Run(
        'ml speech recognize gs://bucket/object --language-code es-ES '
        '--sample-rate 22000 --max-alternatives 2 --hints Bueno --encoding '
        'OGG_OPUS --include-word-time-offsets')
    self.assertEqual(expected, actual)

  def testWithLocalFile(self, track):
    """Test recognize command with local content."""
    self.SetUpForTrack(track)
    with open(self.short_file, 'rb') as audio_file:
      contents = audio_file.read()
    self._ExpectRecognizeRequest(content=contents, language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 results=['Transcribed text'])
    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Transcribed text')])])
    actual = self.Run(
        'ml speech recognize {} --language-code en-US'.format(self.short_file))
    self.assertEqual(expected, actual)

  def testRaisesError(self, track):
    """Test recognize command raises HttpException."""
    self.SetUpForTrack(track)
    error = http_error.MakeDetailedHttpError(code=400, message='Error message',
                                             details=self.sample_error_details)
    self._ExpectRecognizeRequest(uri='gs://bucket/object', language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 error=error)
    with self.assertRaisesRegex(exceptions.HttpException,
                                r'Error message'):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US')

  def testMissingRequiredAudioFilePositional(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        'argument AUDIO: Must be specified.'):
      self.Run('ml speech recognize --language-code en-US')

  def testMissingRequiredLanguageFlag(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorMatches(
        '--language-code must be specified'):
      self.Run('ml speech recognize gs://bucket/object')

  def testInvalidFlagValues(self, track):
    """Test recognize command raises with invalid flag values."""
    self.SetUpForTrack(track)
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--max-alternatives notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--sample-rate notanumber')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize gs://bucket/object --language-code en-US '
               '--filter-profanity invalidvalue')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('ml speech recognize-long-running gs://bucket/object '
               '--language-code en-US --sample-rate 16000 '
               '--encoding NOT_AN_ENCODING')

  def testAudioError(self, track):
    """Test recognize command raises AudioException with invalid audio."""
    self.SetUpForTrack(track)
    audio_path = self.short_file + 'x'
    with self.AssertRaisesExceptionMatches(util.AudioException,
                                           '[{}]'.format(audio_path)):
      self.Run(
          'ml speech recognize {} --language-code en-US'.format(audio_path))


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class RecognizeSpecificTrackTest(speech_base.MlSpeechTestBase,
                                 parameterized.TestCase):
  """Tests for `gcloud ml speech recognize` in a subset of release tracks."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
      calliope_base.ReleaseTrack.BETA: 'v1p1beta1',
      calliope_base.ReleaseTrack.GA: 'v1'
  }

  def testIncludeWordConfidence(self, track):
    """Test recognize command basic output with word confidence requested."""
    self.SetUpForTrack(track)
    self._ExpectRecognizeRequest(uri='gs://bucket/object', language='en-US',
                                 sample_rate=None, max_alternatives=1,
                                 results=['Transcribed text'],
                                 enable_word_confidence=True)

    actual = self.Run(
        'ml speech recognize gs://bucket/object '
        '    --language-code en-US '
        '    --include-word-confidence')

    expected = self.messages.RecognizeResponse(
        results=[self.messages.SpeechRecognitionResult(
            alternatives=[
                self.messages.SpeechRecognitionAlternative(
                    confidence=0.8, transcript='Transcribed text')])])
    self.assertEqual(expected, actual)
    self.assertEqual(json.loads(self.GetOutput()),
                     encoding.MessageToPyValue(expected))

  def testSpeakerDiarizationRequest(self, track):
    """Test diarization flag values mapped in recognize request."""
    self.SetUpForTrack(track)
    transcript = 'what do you think you are doing dave'
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[transcript],
        enable_speaker_diarization=True,
        speaker_count=6)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --enable-speaker-diarization'
                      '    --diarization-speaker-count 6')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testInvalidSpeakerDiarizationRequest(self, track):
    """Test invalid diarization flag values."""
    self.SetUpForTrack(track)
    with self.AssertRaisesArgumentErrorRegexp(
        'enable-speaker-diarization must be specified.'):
      self.Run('ml speech recognize gs://bucket/object '
               '    --language-code en-US '
               '    --diarization-speaker-count 6')

    with self.AssertRaisesArgumentErrorRegexp(
        "invalid int value: 'hugsandkittens'"):
      self.Run('ml speech recognize gs://bucket/object '
               '    --language-code en-US '
               '    --enable-speaker-diarization '
               '    --diarization-speaker-count hugsandkittens')

  def testAdditionalLanguagesRequest(self, track):
    """Test additional_language_codes flag mapped in recognize request."""
    self.SetUpForTrack(track)
    transcript = 'what do you think you are doing dave'
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[transcript],
        additional_language_codes=['en-TZ', 'en-CA'])

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --additional-language-codes en-TZ,en-CA')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=transcript)
        ])
    ])
    self.assertEqual(expected, actual)


class RecognizeAlpha(speech_base.MlSpeechTestBase,
                     parameterized.TestCase):

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1p1beta1',
  }

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.transcript = 'what do you think you are doing dave'
    self.SetUpForTrack(self.track)

  @parameterized.parameters(
      ('discussion', 'DISCUSSION'),
      ('phone-call', 'PHONE_CALL'),
      ('voicemail', 'VOICEMAIL'),
      ('professionally-produced', 'PROFESSIONALLY_PRODUCED'),
      ('voice-search', 'VOICE_SEARCH'),
      ('voice-command', 'VOICE_COMMAND'),
      ('dictation', 'DICTATION'),
  )
  def testRecognizeMetadataInteractionType(self, choice, value):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        interaction_type=value
    )

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --interaction-type {} '.format(choice))
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testRecognizePunctuation(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        enable_punctuation=True)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --enable-automatic-punctuation ')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testRecognizeNaics(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        naics_code=123456)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --naics-code 123456')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('nearfield', 'NEARFIELD'),
      ('midfield', 'MIDFIELD'),
      ('farfield', 'FARFIELD')
  )
  def testRecognizeMicrophoneDistance(self, choice, value):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        microphone_distance=value)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --microphone-distance {}'.format(choice))
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('audio', 'AUDIO'),
      ('video', 'VIDEO')
  )
  def testRecognizeMediaType(self, choice, value):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        media_type=value)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --original-media-type {}'.format(choice))
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      ('smartphone', 'SMARTPHONE'),
      ('pc', 'PC'),
      ('phone-line', 'PHONE_LINE'),
      ('vehicle', 'VEHICLE'),
      ('outdoor', 'OTHER_OUTDOOR_DEVICE'),
      ('indoor', 'OTHER_INDOOR_DEVICE'),
  )
  def testRecognizeDeviceType(self, choice, value):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        device_type=value)

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --recording-device-type {}'.format(choice))
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testRecordingDeviceName(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        device_name='Nexus 5X')

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --recording-device-name "Nexus 5X"')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testRecordingMimeType(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        mime_type='audio/mp3')

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --original-mime-type "audio/mp3"')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testRecordingAudioTopic(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        audio_topic='Recordings of federal supreme court')

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --audio-topic '
                      '"Recordings of federal supreme court"')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testSeparateChannelRecognition(self):
    self._ExpectRecognizeRequest(
        uri='gs://bucket/object',
        language='en-US',
        sample_rate=None,
        max_alternatives=1,
        results=[self.transcript],
        audio_channel_count=3,
        enable_separate_recognition=True
    )

    actual = self.Run('ml speech recognize gs://bucket/object '
                      '    --language-code en-US '
                      '    --audio-channel-count 3 '
                      '    --separate-channel-recognition ')
    expected = self.messages.RecognizeResponse(results=[
        self.messages.SpeechRecognitionResult(alternatives=[
            self.messages.SpeechRecognitionAlternative(
                confidence=0.8, transcript=self.transcript)
        ])
    ])
    self.assertEqual(expected, actual)

  def testInvalidSeparateRecognitionRequest(self):
    """Test invalid separate recognition flag values."""
    with self.AssertRaisesArgumentErrorRegexp(
        '--separate-channel-recognition: Must be specified.'):
      self.Run('ml speech recognize gs://bucket/object '
               '    --language-code en-US '
               '    --audio-channel-count 3')

  def testInvalidAudioChannelCountRequest(self):
    """Test invalid separate recognition flag values."""
    with self.AssertRaisesArgumentErrorRegexp(
        '-audio-channel-count: Must be specified.'):
      self.Run('ml speech recognize gs://bucket/object '
               '    --language-code en-US '
               '    --separate-channel-recognition ')


if __name__ == '__main__':
  test_case.main()
