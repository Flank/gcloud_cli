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
"""Tests for `gcloud compute shared-vpc disable`."""
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class DisableTest(xpn_test_base.XpnTestBase):

  def testDisable_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc disable')
    self.xpn_client.DisableHost.assert_not_called()

  def testDisableHost(self):
    self._testDisableHost('shared-vpc')

  def testDisableHost_xpn(self):
    self._testDisableHost('xpn')

  def _testDisableHost(self, module_name):
    self.Run('compute {} disable foo'.format(module_name))
    self.xpn_client.DisableHost.assert_called_once_with('foo')


if __name__ == '__main__':
  test_case.main()
