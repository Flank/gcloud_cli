# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for source_ref.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.run import source_ref
from tests.lib import sdk_test_base
from tests.lib import test_case


class SourceRefTest(sdk_test_base.WithLogCapture):

  def testImage(self):
    image_artifact = source_ref.SourceRef.MakeImageRef(
        'gcr.io/project/image:latest')
    self.assertEqual(image_artifact.source_type,
                     source_ref.SourceRef.SourceType.IMAGE)

  def testDirectory(self):
    self.StartObjectPatch(os.path, 'isdir', return_value=True)
    dir_artifact = source_ref.SourceRef.MakeDirRef('/app')
    self.assertEqual(dir_artifact.source_type,
                     source_ref.SourceRef.SourceType.DIRECTORY)

  def testRaisesIfNotDir(self):
    """Test raise error if provided path is not a valid directory."""
    self.StartObjectPatch(os.path, 'isdir', return_value=False)
    with self.assertRaises(source_ref.UnknownSourceError):
      source_ref.SourceRef.MakeDirRef('unknownsource')


if __name__ == '__main__':
  test_case.main()
