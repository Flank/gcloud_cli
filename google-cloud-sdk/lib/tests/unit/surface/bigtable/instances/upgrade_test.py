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
"""Bigtable instance upgrade tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import instances
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class UpgradeTest(base.BigtableV2TestBase,
                  waiter_test_base.CloudOperationsBase):

  def SetUp(self):
    self.mocked = self.StartObjectPatch(
        instances,
        'Upgrade',
        return_value=self.msgs.Operation(
            name='operations/operation-name', done=False))

  def testUpgrade(self, track):
    self.track = track
    self.ExpectOperation(self.client.operations, 'operations/operation-name',
                         self.client.projects_instances,
                         'instances/my-instance')

    self.Run('bigtable instances upgrade my-instance')
    self.mocked.assert_called_once_with('my-instance')

  def testUpgradeAsync(self, track):
    self.track = track
    self.Run('bigtable instances upgrade my-instance --async')
    self.mocked.assert_called_once_with('my-instance')


if __name__ == '__main__':
  test_case.main()
