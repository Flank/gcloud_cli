# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for `gcloud components copy-bundled-python`."""

from __future__ import absolute_import
from __future__ import unicode_literals

import sys

from googlecloudsdk.core.updater import update_manager
from tests.lib import cli_test_base


class CopyBundledPythonTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.update_manager_mock = self.StartObjectPatch(
        update_manager, 'UpdateManager', autospec=True)
    self.copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')
    self._old_python_executable = sys.executable

  def TearDown(self):
    sys.executable = self._old_python_executable

  def testCopyBundledPython_Bundled(self):
    self.update_manager_mock().IsPythonBundled.return_value = True
    self.copy_python_mock.return_value = 'foo'
    self.assertEqual(self.Run('components copy-bundled-python'),
                     {'python_location': 'foo'})
    self.copy_python_mock.assert_called_once_with()

  def testCopyBundledPython_NotBundled(self):
    self.update_manager_mock().IsPythonBundled.return_value = False
    sys.executable = 'bar'
    self.assertEqual(self.Run('components copy-bundled-python'),
                     {'python_location': 'bar'})
    self.assertFalse(self.copy_python_mock.called)


if __name__ == '__main__':
  cli_test_base.main()
