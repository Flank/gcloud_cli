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
"""Tests for googlecloudsdk.api_lib.ml.content_source.py."""

from googlecloudsdk.api_lib.ml import content_source
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base
from tests.lib import test_case


class ContentSourceTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.local_file = self.Touch(self.root_path, contents='Audio contents.')
    self.messages = apis.GetMessagesModule('speech', 'v1')

  def testContentPath_Local(self):
    """Test ContentSource returns LocalSource for a local file."""
    expected = content_source.LocalSource(
        self.local_file, 'content')
    actual = content_source.ContentSource.FromContentPath(
        self.local_file, 'speech')
    self.assertEqual(expected, actual)

  def testContentPath_Remote(self):
    """Test ContentSource returns RemoteSource for a valid URL."""
    expected = content_source.RemoteSource(
        'gs://bucket/object', 'uri')
    actual = content_source.ContentSource.FromContentPath(
        'gs://bucket/object', 'speech',
        url_validator=storage_util.ObjectReference.IsStorageUrl)
    self.assertEqual(expected, actual)

  def testContentPath_LocalDir(self):
    """Test ContentSource raises error for a local path that is not a file."""
    with self.assertRaises(content_source.UnrecognizedContentSourceError):
      content_source.ContentSource.FromContentPath(
          self.root_path, 'speech')

  def testContentPath_NoValidator(self):
    """Test ContentSource returns RemoteSource if no URL validator given."""
    expected = content_source.RemoteSource('http://somewebsite.com', 'uri')
    actual = content_source.ContentSource.FromContentPath(
        'http://somewebsite.com', 'speech')
    self.assertEqual(expected, actual)

  def testContentPath_InvalidUrl(self):
    """Test ContentSource raises error if URL is invalid."""
    with self.assertRaises(content_source.UnrecognizedContentSourceError):
      content_source.ContentSource.FromContentPath(
          'http://somewebsite.com', 'speech',
          url_validator=storage_util.ObjectReference.IsStorageUrl)

  def testContentPath_ReadMode(self):
    """Test ContentSource raises error if URL is invalid."""
    expected = content_source.LocalSource(
        self.local_file, 'content', read_mode='r')
    actual = content_source.ContentSource.FromContentPath(
        self.local_file, 'speech', read_mode='r')
    self.assertEqual(expected, actual)

  def testFromContents(self):
    """Test ContentSource.FromContents returns LocalSource."""
    expected = content_source.LocalSource(None, 'content', contents='Machine')
    actual = content_source.LocalSource.FromContents('Machine', 'speech')
    self.assertEqual(expected, actual)

  def testUpdateContents_LocalPath(self):
    msg = self.messages.RecognitionAudio()
    source = content_source.LocalSource(self.local_file, 'content')
    source.UpdateContent(msg)
    self.assertEqual(
        msg, self.messages.RecognitionAudio(content=bytes('Audio contents.')))

  def testUpdateContents_LocalFromContents(self):
    msg = self.messages.RecognitionAudio()
    source = content_source.LocalSource.FromContents('Learning.', 'speech')
    source.UpdateContent(msg)
    self.assertEqual(
        msg, self.messages.RecognitionAudio(content='Learning.'))

  def testUpdateContents_LocalFromEmptyContents(self):
    msg = self.messages.RecognitionAudio()
    source = content_source.LocalSource(None, 'content')
    with self.assertRaises(content_source.ContentError):
      source.UpdateContent(msg)

  def testUpdateContents_Remote(self):
    msg = self.messages.RecognitionAudio()
    source = content_source.RemoteSource('gs://bucket/object', 'uri')
    source.UpdateContent(msg)
    self.assertEqual(
        msg, self.messages.RecognitionAudio(uri='gs://bucket/object'))

  def testContentSource_OtherMessageModules_Local(self):
    """Test LocalSource with languages_v1_messages.Document."""
    msgs = apis.GetMessagesModule('language', 'v1')
    source = content_source.ContentSource.FromContentPath(
        self.local_file, 'language', read_mode='r',
        url_validator=storage_util.ObjectReference.IsStorageUrl)
    actual = msgs.Document()
    source.UpdateContent(actual)
    self.assertEqual(msgs.Document(content='Audio contents.'),
                     actual)

  def testContentSource_OtherMessageModules_Remote(self):
    """Test RemoteSource with languages_v1_messages.Document."""
    msgs = apis.GetMessagesModule('language', 'v1')
    source = content_source.ContentSource.FromContentPath(
        'gs://bucket/object', 'language', read_mode='r',
        url_validator=storage_util.ObjectReference.IsStorageUrl)
    actual = msgs.Document()
    source.UpdateContent(actual)
    self.assertEqual(msgs.Document(gcsContentUri='gs://bucket/object'),
                     actual)

if __name__ == '__main__':
  test_case.main()
