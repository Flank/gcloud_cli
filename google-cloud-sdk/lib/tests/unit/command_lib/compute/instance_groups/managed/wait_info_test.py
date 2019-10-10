# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.instance_groups.managed import wait_info
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


class WaitInfoTest(test_case.TestCase):

  def _CreateInstanceGroupManager(
      self, api_version, current_operations=0):
    return test_resources.MakeInstanceGroupManagersWithActions(
        api_version, current_operations)

  def testV1CreateWaitText(self):
    igm = self._CreateInstanceGroupManager('v1')
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testV1CreateWaitTextWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('v1', current_operations=1)
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testBetaCreateWaitText(self):
    igm = self._CreateInstanceGroupManager('beta')
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testBetaCreateWaitTextWithCurrentActions(self):
    igm = self._CreateInstanceGroupManager('beta', current_operations=1)
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testAlphaCreateWaitText(self):
    igm = self._CreateInstanceGroupManager('alpha')
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable')

  def testAlphaCreateWaitTextWithOneCurrentActions(self):
    igm = self._CreateInstanceGroupManager('alpha', current_operations=1)
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1')

  def testAlphaCreateWaitTextWithTwoCurrentActions(self):
    igm = self._CreateInstanceGroupManager('alpha', current_operations=1)
    igm.currentActions.deleting = 1
    self.assertEqual(
        wait_info.CreateWaitText(igm),
        'Waiting for group to become stable, current operations: creating: 1, '
        'deleting: 1')

if __name__ == '__main__':
  test_case.main()
