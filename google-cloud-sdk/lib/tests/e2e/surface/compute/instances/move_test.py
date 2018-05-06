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
"""Integration tests for creating/using/deleting instances."""

from googlecloudsdk.core import resources
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class MoveTest(e2e_instances_test_base.InstancesTestBase):

  def testInstanceMove(self):
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    self.Run('compute instances move {} '
             '--zone {} '
             '--destination-zone {}'
             .format(self.instance_name, self.zone, self.alternative_zone))
    result = self.Run(
        'compute instances describe {} --zone {} --format=disable'.format(
            self.instance_name, self.alternative_zone))
    real_zone_ref = resources.REGISTRY.Parse(
        result.zone, collection='compute.zones', enforce_collection=True)
    self.assertEqual(self.alternative_zone, real_zone_ref.zone)


if __name__ == '__main__':
  e2e_test_base.main()
