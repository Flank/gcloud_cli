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
"""Tests for the instances describe subcommand."""
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

_COMPUTE_PATH = 'https://www.googleapis.com/compute'


def MakeCustomInstances(msgs, api):
  """Creates a set of custom VM instance messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing custom VM instances.
  """
  prefix = _COMPUTE_PATH + '/' + api
  # Create a Scheduling message that includes the preemptible flag, now that all
  # API versions support it.
  scheduling = msgs.Scheduling(
      automaticRestart=False,
      onHostMaintenance=msgs.Scheduling.
      OnHostMaintenanceValueValuesEnum.TERMINATE,
      preemptible=False)
  return [
      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/zones/zone-1/'
              'machineTypes/custom-2-3072'),
          name='instance-custom',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.4',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.77'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-custom'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),
  ]


class InstancesDescribeTest(test_base.BaseTest,
                            completer_test_base.CompleterBase,
                            test_case.WithOutputCapture):

  def SetUp(self):
    # creating side effects for the custom instance instance-1
    # mocked in test_resources
    self.make_requests.side_effect = iter([
        [test_resources.INSTANCES_V1[0]],
    ])

  def testSimpleCase(self):
    self.Run("""
        compute instances describe instance-1
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            machineType: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name: instance-1
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.75
              networkIP: 10.0.0.1
            scheduling:
              automaticRestart: false
              onHostMaintenance: TERMINATE
              preemptible: false
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            status: RUNNING
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testTextOutput(self):
    self.Run("""
        compute instances describe instance-1
          --format text
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            machineType:                                 https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name:                                        instance-1
            networkInterfaces[0].accessConfigs[0].natIP: 23.251.133.75
            networkInterfaces[0].networkIP:              10.0.0.1
            scheduling.automaticRestart:                 False
            scheduling.onHostMaintenance:                TERMINATE
            scheduling.preemptible:                      False
            selfLink:                                    https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            status:                                      RUNNING
            zone:                                        https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testJsonOutput(self):
    self.Run("""
        compute instances describe instance-1
          --format json
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            {
              "machineType": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
              "name": "instance-1",
              "networkInterfaces": [
                {
                  "accessConfigs": [
                    {
                      "natIP": "23.251.133.75"
                    }
                  ],
                  "networkIP": "10.0.0.1"
                }
              ],
              "scheduling": {
                "automaticRestart": false,
                "onHostMaintenance": "TERMINATE",
                "preemptible": false
              },
              "selfLink": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1",
              "status": "RUNNING",
              "zone": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
            }
            """))

  def testUriSupport(self):
    self.Run("""
        compute instances describe
          https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            machineType: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name: instance-1
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.75
              networkIP: 10.0.0.1
            scheduling:
              automaticRestart: false
              onHostMaintenance: TERMINATE
              preemptible: false
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            status: RUNNING
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='instance-1', zone='zone-1'),
        ],

        [test_resources.INSTANCES_V1[0]],
    ])

    self.Run("""
        compute instances describe instance-1
        """)

    self.AssertErrContains(
        'No zone specified. Using zone [zone-1] for instance: [instance-1].')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            machineType: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name: instance-1
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.75
              networkIP: 10.0.0.1
            scheduling:
              automaticRestart: false
              onHostMaintenance: TERMINATE
              preemptible: false
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            status: RUNNING
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testWithNonExistentInstance(self):
    def MakeRequests(*_, **kwargs):
      # pylint: disable=using-constant-test
      if False:
        yield
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances describe instance-1
            --zone zone-1
          """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertFalse(self.GetOutput())

  def testDesribeCompletion(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion(
        'compute instances describe --zone zone-1 --project my-project i',
        ['instance-1',
         'instance-2',
         'instance-3'])


class InstancesNoZoneDescribeTest(test_base.BaseTest,
                                  completer_test_base.CompleterBase):

  def testDesribeCompletionWithoutZone(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))

    self.RunCompletion('compute instances describe instance-3',
                       ['instance-3 --zone=zone-1'])
    self.RunCompletion('compute instances describe instance',
                       ['instance-1 --zone=zone-1',
                        'instance-2 --zone=zone-1',
                        'instance-3 --zone=zone-1'])


class InstancesCustomDescribeTest(test_base.BaseTest):

  def SetUp(self):
    # creating side effects for the custom instance instance-custom
    # mocked in test_resources
    self.make_requests.side_effect = iter([
        [MakeCustomInstances(self.messages, 'v1')[0]],
    ])

  def testCustomMachineOutput(self):
    self.Run("""
        compute instances describe instance-custom
          --zone zone-1
      """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-custom',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            machineType: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/custom-2-3072
            name: instance-custom
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.77
              networkIP: 10.0.0.4
            scheduling:
              automaticRestart: false
              onHostMaintenance: TERMINATE
              preemptible: false
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-custom
            status: RUNNING
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))


# TODO(b/68652326): Guest attribute names should be discoverable.
class InstancesAlphaDescribeTest(test_base.BaseTest,
                                 test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDescribeGuestAttributes(self):
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            selfLink='link-to-instance?',
            variableKey='foo',
            variableValue='bar',),
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            selfLink='link-to-instance?',
            variableKey='gpp',
            variableValue='cbs',)]])
    self.Run("""
        compute instances describe instance-custom --zone zone-1
        --guest-attributes foo,gpp
        """)

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request_1 = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='instance-custom',
        variableKey='foo',
        zone='zone-1',
        project='my-project')
    request_2 = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='instance-custom',
        variableKey='gpp',
        zone='zone-1',
        project='my-project')

    self.CheckRequests(
        [(service, method, request_1),
         (service, method, request_2)]
    )
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        kind: compute#guestAttributes
        selfLink: link-to-instance?
        variableKey: foo
        variableValue: bar
        ---
        kind: compute#guestAttributes
        selfLink: link-to-instance?
        variableKey: gpp
        variableValue: cbs
        """))
    self.AssertErrEquals('')

  def testSimpleDescibe(self):
    self.make_requests.side_effect = iter([
        [self.messages.Instance(
            machineType=(
                self.compute_uri + '/projects/my-project/zones/zone-1/'
                'machineTypes/custom-2-3072'),
            name='instance-1',
            networkInterfaces=[
                self.messages.NetworkInterface(
                    networkIP='10.0.0.4',
                    accessConfigs=[
                        self.messages.AccessConfig(natIP='23.251.133.77'),
                    ],
                ),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(self.compute_uri + '/projects/my-project/zones/zone-1/'
                      'instances/instance-1'),
            zone=self.compute_uri + '/projects/my-project/zones/zone-1'),
        ]])
    self.Run("""
        compute instances describe instance-1
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        textwrap.dedent("""\
            machineType: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/machineTypes/custom-2-3072
            name: instance-1
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.77
              networkIP: 10.0.0.4
            selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-1
            status: RUNNING
            zone: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1
            """),
        self.GetOutput(),)

if __name__ == '__main__':
  test_case.main()
