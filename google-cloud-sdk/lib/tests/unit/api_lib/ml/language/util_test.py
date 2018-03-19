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
"""Tests for the natural language utils."""

from googlecloudsdk.api_lib.ml.language import util
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base
from tests.lib import test_case


class LanguageClientTestBase(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = apis.GetMessagesModule(util.LANGUAGE_API, 'v1')

  def testGetContent_Content(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    source = util.GetContentSource(content='Some content')
    doc = self.messages.Document()
    source.UpdateContent(doc)
    self.assertEqual(doc.content, 'Some content')

  def testGetContent_ContentFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    temp_file = self.Touch(self.root_path, contents='Hello world')
    source = util.GetContentSource(content_file=temp_file)
    doc = self.messages.Document()
    source.UpdateContent(doc)
    self.assertEqual(doc.content, 'Hello world')

  def testGetContent_GCSFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    source = util.GetContentSource(content_file='gs://bucket/object')
    doc = self.messages.Document()
    source.UpdateContent(doc)
    self.assertEqual(doc.gcsContentUri, 'gs://bucket/object')

  def testGetContent_NoContent(self):
    """Test GetContentSource when empty content is given."""
    with self.assertRaises(util.ContentError):
      util.GetContentSource(content='')

  def testGetContent_NonexistentContentFile(self):
    """Test GetContentSource when badly formatted URL is given."""
    with self.assertRaises(util.ContentFileError):
      util.GetContentSource(content_file='http://text.com/text/')

  def testGetContent_ContentAndContentFile(self):
    """Test GetContentSource when both content and content file are given."""
    with self.assertRaises(ValueError):
      util.GetContentSource(content_file='gs://bucket/object',
                            content='Some content')


if __name__ == '__main__':
  test_case.main()
