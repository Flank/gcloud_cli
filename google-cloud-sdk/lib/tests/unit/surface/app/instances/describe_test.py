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

from googlecloudsdk.core import properties
from tests.lib.surface.app import instances_base


class InstancesDescribeTest(instances_base.InstancesTestBase):

  def testDescribe(self):
    self._ExpectGetInstanceCall('default', 'v1', 'i2')
    self.Run('app instances describe -s default -v v1 i2')
    instance = self._MakeUtilInstance('default', 'v1', 'i2')
    self.AssertOutputEquals("""\
        availability: RESIDENT
        id: {i}
        qps: 8.40422
        startTime: '2016-07-06T22:01:12.117Z'
        vmIp: 127.0.0.1
        vmName: {vm_name}
        vmStatus: RUNNING
        vmZoneName: us-central
        """.format(i=instance.id, vm_name=self._GetVMName(instance.id)),
                            normalize_space=True)

  def testDescribe_NoProject(self):
    # Due to a weird interaction with the self.Project() setup in CliTestBase,
    # both of these are required to reset the project property to None.
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    properties.VALUES.core.project.Set(None)
    with self.assertRaisesRegexp(properties.RequiredPropertyError,
                                 'is not currently set.'):
      self.Run('app instances describe -s default -v v1 i2')
