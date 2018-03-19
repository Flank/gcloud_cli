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
"""Integration tests for zonal instance group managers."""

from tests.lib.surface.compute import e2e_managers_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedZonalTest(e2e_managers_test_base.ManagedTestBase):

  def SetUp(self):
    self.prefix = 'managed-instance-group-zonal'
    self.scope = e2e_test_base.ZONAL

  def testInstanceGroupManagerCreationZonal(self):
    self.RunInstanceGroupManagerCreationTest()

  def testResizeZonal(self):
    self.RunResizeTest()

  def testSetInstanceTemplateAndRecreateZonal(self):
    self.RunSetInstanceTemplateAndRecreateTest()

  def testDeleteInstancesZonal(self):
    self.RunDeleteInstancesTest()

  def testAbandonInstancesZonal(self):
    self.RunAbandonInstancesTest()

  def testNamedPortsZonal(self):
    self.RunNamedPortsTest()

  def testTargetPools(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager()
    tp_name = self.CreateTargetPool()

    self.Run('compute instance-groups managed set-target-pools {0} '
             '--target-pools {1} '
             '--zone {2}'.format(igm_name, tp_name, self.zone))
    self.ClearOutput()
    self.Run('compute instance-groups managed describe {0} '
             '--zone {1}'.format(igm_name, self.zone))
    self.AssertNewOutputContains(tp_name)


if __name__ == '__main__':
  e2e_test_base.main()
