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
"""Tests for wait messages for the compute instance groups managed commands."""

from googlecloudsdk.command_lib.compute.instance_groups.managed import wait_info
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


class WaitInfoTest(test_case.TestCase):

  def _CreateInstanceGroupManager(
      self, api_version, current_operations=0, pending_operations=0):
    if api_version == 'alpha':
      return test_resources.MakeInstanceGroupManagersWithPendingActions(
          api=api_version, pending_actions_count=pending_operations,
          current_actions_count=current_operations, scope_type='zone',
          scope_name='central2-a')
    return test_resources.MakeInstanceGroupManagersWithCurrentActions(
        api_version, current_operations)

  def testV1IsGroupStableTrue(self):
    igm = self._CreateInstanceGroupManager('v1')
    self.assertTrue(wait_info.IsGroupStable(igm))

  def testV1IsGroupStableWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('v1', current_operations=1)
    self.assertFalse(wait_info.IsGroupStable(igm))

  def testBetaIsGroupStableTrue(self):
    igm = self._CreateInstanceGroupManager('beta')
    self.assertTrue(wait_info.IsGroupStable(igm))

  def testBetaIsGroupStableWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('beta', current_operations=1)
    self.assertFalse(wait_info.IsGroupStable(igm))

  def testAlphaIsGroupStableTrue(self):
    igm = self._CreateInstanceGroupManager('alpha')
    self.assertTrue(wait_info.IsGroupStableAlpha(igm))

  def testAlphaIsGroupStableWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('alpha', current_operations=1)
    self.assertFalse(wait_info.IsGroupStableAlpha(igm))

  def testAlphaIsGroupStableWithPendingActions(self):
    igm = self._CreateInstanceGroupManager('alpha', pending_operations=1)
    self.assertFalse(wait_info.IsGroupStableAlpha(igm))

  def testV1CreateWaitText(self):
    igm = self._CreateInstanceGroupManager('v1')
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testV1CreateWaitTextWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('v1', current_operations=1)
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testBetaCreateWaitText(self):
    igm = self._CreateInstanceGroupManager('beta')
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testBetaCreateWaitTextWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('beta', current_operations=1)
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testAlphaCreateWaitText(self):
    igm = self._CreateInstanceGroupManager('alpha')
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testAlphaCreateWaitTextWithOneCurrentActions(self):
    igm = self._CreateInstanceGroupManager('alpha', current_operations=1)
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testAlphaCreateWaitTextWithTwoCurrentActions(self):
    igm = self._CreateInstanceGroupManager('alpha', current_operations=1)
    igm.currentActions.deleting = 1
    self.assertEquals(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1, '
        'deleting: 1')

  def testAlphaCreateWaitTextWithPendingActions(self):
    igm = self._CreateInstanceGroupManager('alpha', pending_operations=1)
    self.assertEquals(
        wait_info.CreateWaitTextAlpha(igm),
        'Waiting for group to become stable, pending operations: creating: 1')

  def testAlphaCreateWaitTextWithCurrentAndPendingActions(self):
    igm = self._CreateInstanceGroupManager(
        'alpha', current_operations=1, pending_operations=1)
    self.assertEquals(
        wait_info.CreateWaitTextAlpha(igm),
        'Waiting for group to become stable, current operations: creating: 1, '
        'pending operations: creating: 1')

if __name__ == '__main__':
  test_case.main()
