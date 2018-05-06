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

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ml.speech import util
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


@parameterized.parameters('v1', 'v1p1beta1')
class SpeechUtilTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.messages = None
    self.sample_file = self.Resource(
        'tests', 'unit', 'command_lib', 'ml', 'speech', 'testdata',
        'sample.flac')

  def SetUpForVersion(self, version):
    self.messages = apis.GetMessagesModule(util.SPEECH_API, version)
    self.get_audio = util.GetAudioHook(version)

  def testGetAudioFromPath_Local(self, version):
    """Test GetAudioFromPath returns expected message with local source."""
    self.SetUpForVersion(version)
    with open(self.sample_file, 'rb') as input_file:
      contents = input_file.read()
    expected = self.messages.RecognitionAudio(content=contents)
    actual = self.get_audio(self.sample_file)
    self.assertEqual(expected, actual)

  def testGetAudioFromPath_Remote(self, version):
    """Test GetAudioFromPath returns expected message with remote source."""
    self.SetUpForVersion(version)
    expected = self.messages.RecognitionAudio(uri='gs://bucket/object')
    actual = self.get_audio('gs://bucket/object')
    self.assertEqual(expected, actual)

  def testGetAudioFromPath_Raises(self, version):
    """Test GetAudioFromPath raises with invalid URL."""
    self.SetUpForVersion(version)
    with self.assertRaisesRegex(
        util.AudioException,
        r'Invalid audio source \[http://example.com\]'):
      self.get_audio('http://example.com')


if __name__ == '__main__':
  test_case.main()
