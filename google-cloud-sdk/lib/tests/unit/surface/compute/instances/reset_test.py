# -*- coding: utf-8 -*- #
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
"""Tests for the instances reset subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesResetTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute instances reset
          instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testResetManyInstances(self):
    self.Run("""
        compute instances reset
          instance-1 instance-2 instance-3
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-1',
              project='my-project',
              zone='central2-a')),
         (self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-2',
              project='my-project',
              zone='central2-a')),
         (self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-3',
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances reset
          https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/instance-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='central1-a'),
        ],

        [],
    ])

    self.Run("""
        compute instances reset
          instance-1
        """)

    self.AssertErrContains(
        'No zone specified. Using zone [central1-a] for instance: [instance-1]')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'Reset',
          messages.ComputeInstancesResetRequest(
              instance='instance-1',
              project='my-project',
              zone='central1-a'))],
    )


if __name__ == '__main__':
  test_case.main()
