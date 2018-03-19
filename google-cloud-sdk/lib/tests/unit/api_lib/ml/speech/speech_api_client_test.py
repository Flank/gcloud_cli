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
"""Tests for the Speech API client."""

from googlecloudsdk.api_lib.ml.speech import exceptions
from googlecloudsdk.api_lib.ml.speech import speech_api_client
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base
from tests.lib import test_case


class SpeechClientTest(sdk_test_base.WithFakeAuth,
                       test_case.WithOutputCapture):

  def SetUp(self):
    self.messages = apis.GetMessagesModule(
        speech_api_client.SPEECH_API, speech_api_client.SPEECH_API_VERSION)
    self.sample_file = self.Resource(
        'tests', 'unit', 'api_lib', 'ml', 'speech', 'testdata', 'sample.flac')

  def testGetAudio_Local(self):
    """Test GetAudio returns expected message with local source."""
    with open(self.sample_file, 'rb') as input_file:
      contents = input_file.read()
    expected = self.messages.RecognitionAudio(content=contents)
    actual = speech_api_client.GetAudio(self.sample_file)
    self.assertEqual(expected, actual)

  def testGetAudio_Remote(self):
    """Test GetAudio returns expected message with remote source."""
    expected = self.messages.RecognitionAudio(uri='gs://bucket/object')
    actual = speech_api_client.GetAudio('gs://bucket/object')
    self.assertEqual(expected, actual)

  def testGetAudio_Raises(self):
    """Test GetAudio raises with invalid URL."""
    with self.assertRaisesRegexp(
        exceptions.AudioException,
        r'Invalid audio source \[http://example.com\]'):
      speech_api_client.GetAudio('http://example.com')


if __name__ == '__main__':
  test_case.main()
