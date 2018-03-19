# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for the edit module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import functools
import subprocess
import tempfile

from googlecloudsdk.core.util import edit
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base


class OnlineEditTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.os_stat_mock = self.StartPatch(
        'googlecloudsdk.core.util.edit.FileModifiedTime')
    self.check_call_mock = self.StartPatch(
        'googlecloudsdk.core.util.edit.SubprocessCheckCall')
    self.platform_os_mock = self.StartPatch(
        'googlecloudsdk.core.util.platforms.OperatingSystem.Current')

  def testFileModifiedTime(self):
    self.os_stat_mock.return_value = 1
    self.assertEqual(1, edit.FileModifiedTime('example.txt'))

  def testSubprocessCheckCall(self):
    self.check_call_mock.return_value = 1
    self.assertEqual(1, edit.SubprocessCheckCall())

  def testWindowsEditorException(self):
    self.platform_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    self.check_call_mock.side_effect = subprocess.CalledProcessError(
        'unused returncode', 'unused cmd')
    with self.assertRaises(edit.EditorException):
      edit.OnlineEdit('Example text')

  def testLinuxEditorException(self):
    self.platform_os_mock.return_value = platforms.OperatingSystem.LINUX
    self.check_call_mock.side_effect = subprocess.CalledProcessError(
        'unused returncode', 'unused cmd')
    with self.assertRaises(edit.EditorException):
      edit.OnlineEdit('Example text')

  def testNoSaveException(self):
    self.platform_os_mock.return_value = platforms.OperatingSystem.LINUX
    with self.assertRaises(edit.NoSaveException):
      edit.OnlineEdit('Example text')

  def testWindowsOSEdit(self):
    self.platform_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    tempfile.NamedTemporaryFile = functools.partial(
        tempfile.NamedTemporaryFile, delete=False)
    self.os_stat_mock.side_effect = [0, 10]
    self.assertEqual('Example text', edit.OnlineEdit('Example text'))

  def testLinuxOSEdit(self):
    self.platform_os_mock.return_value = platforms.OperatingSystem.LINUX
    self.os_stat_mock.side_effect = [0, 10]
    self.assertEqual('Example text', edit.OnlineEdit('Example text'))


if __name__ == '__main__':
  sdk_test_base.main()
