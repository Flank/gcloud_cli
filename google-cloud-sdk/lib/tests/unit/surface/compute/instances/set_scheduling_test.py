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
"""Tests for the instances set-scheduling subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')

MIGRATE = messages.Scheduling.OnHostMaintenanceValueValuesEnum.MIGRATE
TERMINATE = messages.Scheduling.OnHostMaintenanceValueValuesEnum.TERMINATE


class InstancesSetSchedulingTest(test_base.BaseTest):

  def testWithDefaults(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestartMigrate(self):
    self.Run("""
        compute instances set-scheduling instance-1
        --restart-on-failure
        --maintenance-policy MIGRATE
        --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  automaticRestart=True,
                  onHostMaintenance=MIGRATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestartMigrate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --maintenance-policy MIGRATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=MIGRATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestartTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --restart-on-failure
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  automaticRestart=True,
                  onHostMaintenance=TERMINATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestartTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=TERMINATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestart(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --restart-on-failure
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(automaticRestart=True),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestart(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(automaticRestart=False),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testMigrate(self):
    self.templateTestMigrate("""
        compute instances set-scheduling instance-1
          --maintenance-policy MIGRATE
          --zone central2-a
        """)

  def testMigrateLowerCase(self):
    self.templateTestMigrate("""
        compute instances set-scheduling instance-1
          --maintenance-policy migrate
          --zone central2-a
        """)

  def templateTestMigrate(self, cmd):
    self.Run(cmd)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  onHostMaintenance=MIGRATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(
                  onHostMaintenance=TERMINATE),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances set-scheduling
          https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/instance-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(),
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
            messages.Instance(name='instance-1', zone='central1-b'),
            messages.Instance(name='instance-1', zone='central2-a'),
        ],

        [],
    ])
    self.WriteInput('3\n')

    self.Run("""
        compute instances set-scheduling
          instance-1
        """)

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'SetScheduling',
          messages.ComputeInstancesSetSchedulingRequest(
              scheduling=messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )


class InstancesSetSchedulingTestAlpha(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

    maintenance_enum = self.messages.Scheduling.OnHostMaintenanceValueValuesEnum
    self.terminate = maintenance_enum.TERMINATE

  def testMaintenancePolicyDeprecation(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')

  def testOnHostMaintenanceFlag(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --on-host-maintenance TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

if __name__ == '__main__':
  test_case.main()
