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
"""Tests for `gcloud compute shared-vpc enable`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class EnableTest(xpn_test_base.XpnTestBase):

  def testEnable_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc enable')
    self.xpn_client.EnableHost.assert_not_called()

  def testEnable(self):
    self._testEnable('shared-vpc')

  def testEnable_xpn(self):
    self._testEnable('xpn')

  def _testEnable(self, module_name):
    self.Run('compute {} enable foo'.format(module_name))
    self.xpn_client.EnableHost.assert_called_once_with('foo')


if __name__ == '__main__':
  test_case.main()
