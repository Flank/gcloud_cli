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
"""Integration tests for simulating maintenance on instances."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class SimulateMaintenanceEventTest(e2e_instances_test_base.InstancesTestBase):

  @test_case.Filters.skip('Failing', 'b/80485653')
  def testSimulateMaintenanceEvent(self):
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    self.Run(
        'compute instances simulate-maintenance-event {} '
        '--zone {} '.format(self.instance_name, self.zone),
        track=calliope_base.ReleaseTrack.BETA)
    operations = self.Run(
        'compute operations list --filter="targetLink={}/instances/{}" '
        '--filter=operationType=compute.instances.migrateOnHostMaintenance '
        '--format=disable'.format(self.zone, self.instance_name))

    found = False
    for entry in list(operations):
      if (entry['operationType'] == 'compute.instances.migrateOnHostMaintenance'
         ) and (entry['targetLink'].endswith(
             'cloud-sdk-integration-testing/zones/{}/instances/{}'.format(
                 self.zone, self.instance_name))):
        # The expectation is that when the SimulateMaintenanceEvent RPC
        # returns, the associated migration should be completed.  Therefore,
        # the migrateOnHostMaintenance entry should be DONE.
        found = (entry['status'] == 'DONE')
        break

    if not found:
      self.assertTrue(found, 'No migration found.')

    self.Run('compute instances delete {} --zone {}'.format(
        self.instance_name, self.zone))


if __name__ == '__main__':
  e2e_test_base.main()
