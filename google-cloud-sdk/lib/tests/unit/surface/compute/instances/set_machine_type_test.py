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
"""Tests for the instances set-machine-type subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


_DEFAULT_MACHINE_TYPE = 'n1-standard-1'
_MACHINE_TYPE_TEMPLATE = ('{compute_uri}/projects/my-project/zones/central2-a/'
                          'machineTypes/{machine_type}')


class InstancesSetSchedulingTest(test_base.BaseTest):

  def _MakeMachineTypeUrl(self, machine_type):
    return _MACHINE_TYPE_TEMPLATE.format(compute_uri=self.compute_uri,
                                         machine_type=machine_type)

  def _MakeGetMachineTypeRequest(self, machine_type=_DEFAULT_MACHINE_TYPE):
    return (
        self.compute.machineTypes,
        'Get',
        messages.ComputeMachineTypesGetRequest(
            machineType=machine_type,
            project='my-project',
            zone='central2-a'))

  def _MakeSetMachineTypeRequest(self, machine_type=_DEFAULT_MACHINE_TYPE):
    instances_machine_type_request = messages.InstancesSetMachineTypeRequest(
        machineType=self._MakeMachineTypeUrl(machine_type))
    return (
        self.compute.instances,
        'SetMachineType',
        messages.ComputeInstancesSetMachineTypeRequest(
            instancesSetMachineTypeRequest=instances_machine_type_request,
            instance='instance-1',
            project='my-project',
            zone='central2-a'))

  def testWithDefaults(self):
    self.Run("""
        compute instances set-machine-type instance-1
          --zone central2-a
          --machine-type n1-standard-1
        """)

    self.CheckRequests([self._MakeSetMachineTypeRequest()])

  def testWithDefaultsUrlGiven(self):
    self.Run("""
        compute instances set-machine-type instance-1
          --zone central2-a
          --machine-type {0}
        """.format(self._MakeMachineTypeUrl(_DEFAULT_MACHINE_TYPE)))

    self.CheckRequests([self._MakeSetMachineTypeRequest()])

  def testInstanceNotTerminated(self):
    error_msg = (u"The resource 'projects/cloudsdktest/zones/us-central1-f/"
                 u"instances/zjn-win' is not ready")
    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((400, error_msg))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.Run("""
          compute instances set-machine-type instance-1
            --zone central2-a
            --machine-type n1-standard-1
          """)

    self.CheckRequests([self._MakeSetMachineTypeRequest()])

  def testBadMachineType(self):
    error_msg = (u"Invalid value for field 'resource.machineTypes': "
                 u"'projects/cloudsdktest/zones/us-central1-f/machineTypes/"
                 u"bad-machine-type'.  Resource was not found.")
    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((400, error_msg))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.Run("""
          compute instances set-machine-type instance-1
            --zone central2-a
            --machine-type bad-machine-type
          """)

    self.CheckRequests([self._MakeSetMachineTypeRequest('bad-machine-type')])

  def testNoMachineTypeDefaults(self):
    with self.assertRaisesRegexp(
        exceptions.ToolException,
        r'One of --custom-cpu, --custom-memory, --machine-type must be '
        r'specified.'):
      self.Run("""
          compute instances set-machine-type instance-1
          --zone central2-a
          """)

  def testCustomMachineType(self):
    self.make_requests.side_effect = iter([
        [
            messages.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=4,
                memoryMb=12288),
        ],
        [],
    ])

    self.Run("""
        compute instances set-machine-type instance-1
          --zone central2-a
          --custom-cpu 4
          --custom-memory 12
        """)

    self.CheckRequests(
        [self._MakeGetMachineTypeRequest(machine_type='custom-4-12288')],
        [self._MakeSetMachineTypeRequest(machine_type='custom-4-12288')])

  def testCustomCpuNoCustomMemory(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):

      self.Run("""
          compute instances set-machine-type instance-1
            --zone central2-a
            --custom-cpu 4
          """)

  def testCustomMemoryNoCustomCpu(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-memory: --custom-cpu must be specified.'):

      self.Run("""
          compute instances set-machine-type instance-1
            --zone central2-a
            --custom-memory 12
          """)

  def testMachineTypeWithCustomMemory(self):
    with self.assertRaisesRegexp(
        exceptions.InvalidArgumentException,
        r'Cannot set both \[--machine-type\] and '
        r'\[--custom-cpu\]\/\[--custom-memory\]'):

      self.Run("""
          compute instances set-machine-type instance-1
            --zone central2-a
            --custom-cpu 2
            --custom-memory 12
            --machine-type n1-standard-1
          """)

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='central2-a'),
        ],

        [],
    ])

    self.Run("""
        compute instances set-machine-type instance-1
          --machine-type n1-standard-1
        """)

    self.AssertErrContains(
        'No zone specified. Using zone [central2-a] for instance: [instance-1]')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),
        [self._MakeSetMachineTypeRequest()],
    )


if __name__ == '__main__':
  test_case.main()
