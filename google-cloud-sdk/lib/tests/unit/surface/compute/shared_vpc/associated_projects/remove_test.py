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
"""Tests for `gcloud compute shared-vpc associated-projects remove`."""
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class RemoveTest(xpn_test_base.XpnTestBase):

  def testRemove_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID --host-project: Must be specified.'):
      self.Run('compute shared-vpc associated-projects remove')
    self.xpn_client.DisableXpnAssociatedProject.assert_not_called()

  def testRemove(self):
    self._testRemove('shared-vpc')

  def testRemove_xpn(self):
    self._testRemove('xpn')

  def _testRemove(self, module_name):
    self.Run('compute {} associated-projects remove --host-project xpn-host '
             'xpn-user'.format(module_name))
    self.xpn_client.DisableXpnAssociatedProject.assert_called_once_with(
        'xpn-host', 'xpn-user')


if __name__ == '__main__':
  test_case.main()
