# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import config
from tests.lib import cli_test_base
from tests.lib import test_case


class VersionTest(cli_test_base.CliTestBase):

  def DoAssertions(self, current_versions):
    if current_versions:
      for version in current_versions:
        self.AssertOutputContains(version)
    elif config.Paths().sdk_root:
      # The testing component is always present
      self.AssertOutputContains('tests')

  def testVersion(self):
    self.Run('version')
    self.DoAssertions(['Google Cloud SDK'])

  def testVersionRoot(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value='fakeroot')
    self.update_manager_mock = self.StartPatch(
        'googlecloudsdk.core.updater.update_manager.UpdateManager')
    current_versions_mock = self.update_manager_mock.return_value
    current_versions_mock.GetCurrentVersionsInformation.return_value = {
        'gsutil': '4.19'}

    self.Run('version')
    self.DoAssertions(['Google Cloud SDK', 'gsutil', '4.19'])

  def testVersionFlag(self):
    with self.assertRaises(SystemExit) as cm:
      self.Run('--version')
    self.assertEqual(cm.exception.code, 0)
    self.DoAssertions(['Google Cloud SDK'])

  def testUpdatesEpilogNoRoot(self):
    self.Run('version')
    self.AssertErrNotContains('Updates are available')

  def testUpdatesEpilogWithRoot(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value='fakeroot')

    update_manager_mock = self.StartPatch(
        'googlecloudsdk.core.updater.update_manager.UpdateManager')
    current_versions_mock = update_manager_mock.return_value

    current_versions_mock.UpdatesAvailable.return_value = False
    self.Run('version')
    self.AssertErrNotContains('Updates are available')

    current_versions_mock.UpdatesAvailable.return_value = True
    self.Run('version')
    self.AssertErrContains('Updates are available')


if __name__ == '__main__':
  test_case.main()
