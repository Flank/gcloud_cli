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

"""Tests for the natural language utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ml.language import util
from tests.lib import sdk_test_base
from tests.lib import test_case


class LanguageUtilTest(sdk_test_base.SdkBase):

  NAMESPACE = collections.namedtuple('Namespace', ['content', 'content_file'])

  def SetUp(self):
    messages = apis.GetMessagesModule('language', 'v1')
    self.request = messages.AnalyzeEntitiesRequest(document=messages.Document())

  def testGetContent_Content(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    n = LanguageUtilTest.NAMESPACE(content='Some content', content_file=None)
    util.UpdateRequestWithInput(None, n, self.request)
    self.assertEqual(self.request.document.content, 'Some content')

  def testGetContent_ContentFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    temp_file = self.Touch(self.root_path, contents='Hello world')
    n = LanguageUtilTest.NAMESPACE(content=None, content_file=temp_file)
    util.UpdateRequestWithInput(None, n, self.request)
    self.assertEqual(self.request.document.content, 'Hello world')

  def testGetContent_GCSFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    n = LanguageUtilTest.NAMESPACE(content=None,
                                   content_file='gs://bucket/object')
    util.UpdateRequestWithInput(None, n, self.request)
    self.assertEqual(self.request.document.gcsContentUri, 'gs://bucket/object')

  def testGetContent_NoContent(self):
    """Test GetContentSource when empty content is given."""
    with self.assertRaises(util.ContentError):
      n = LanguageUtilTest.NAMESPACE(content='', content_file=None)
      util.UpdateRequestWithInput(None, n, self.request)

  def testGetContent_NonexistentContentFile(self):
    """Test GetContentSource when badly formatted URL is given."""
    with self.assertRaises(util.ContentFileError):
      n = LanguageUtilTest.NAMESPACE(content='',
                                     content_file='http://text.com/text/')
      util.UpdateRequestWithInput(None, n, self.request)

  def testGetContent_ContentAndContentFile(self):
    """Test GetContentSource when both content and content file are given."""
    with self.assertRaises(ValueError):
      n = LanguageUtilTest.NAMESPACE(content='Some content',
                                     content_file='gs://bucket/object')
      util.UpdateRequestWithInput(None, n, self.request)


if __name__ == '__main__':
  test_case.main()
