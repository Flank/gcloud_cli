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
"""Tests for the instance-groups describe subcommand."""
import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'
messages = core_apis.GetMessagesModule('compute', API_VERSION)


def SetUpMockClient(api):
  mock_client = mock.Client(
      core_apis.GetClientClass('compute', api),
      real_client=core_apis.GetClientInstance('compute', api, no_http=True))
  mock_client.Mock()
  return mock_client


class InstanceGroupsDescribeTest(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_client = SetUpMockClient(API_VERSION)
    self.addCleanup(self.mock_client.Unmock)

  def testDescribeZonal(self):
    self.mock_client.instanceGroups.Get.Expect(
        messages.ComputeInstanceGroupsGetRequest(
            instanceGroup='group-1',
            project='fake-project',
            zone='zone-1'),
        test_resources.MakeInstanceGroups(messages, API_VERSION)[0]
    )

    self.Run("""
        compute instance-groups describe group-1 --zone zone-1
        """)

    self.assertMultiLineEqual(
        self.stdout.getvalue(),
        textwrap.dedent("""\
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test instance group
            fingerprint: MTIz
            name: group-1
            namedPorts:
            - name: serv-1
              port: 1111
            - name: serv-2
              port: 2222
            - name: serv-3
              port: 3333
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instanceGroups/group-1
            size: 0
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testDescribeRegional(self):
    self.mock_client.regionInstanceGroups.Get.Expect(
        messages.ComputeRegionInstanceGroupsGetRequest(
            instanceGroup='group-1',
            project='fake-project',
            region='region-1'),
        test_resources.MakeInstanceGroups(
            messages, 'alpha', scope_type='region',
            scope_name='region-1')[0]
    )
    self.Run("""
        compute instance-groups describe group-1 --region region-1
        """)

    self.assertMultiLineEqual(
        self.stdout.getvalue(),
        textwrap.dedent("""\
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test instance group
            fingerprint: MTIz
            name: group-1
            namedPorts:
            - name: serv-1
              port: 1111
            - name: serv-2
              port: 2222
            - name: serv-3
              port: 3333
            region: https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/instanceGroups/group-1
            size: 0
            """))

  def testScopePrompt(self):
    self.mock_client.instanceGroups.Get.Expect(
        messages.ComputeInstanceGroupsGetRequest(
            instanceGroup='group-1',
            project='fake-project',
            zone='zone-2'),
        test_resources.MakeInstanceGroups(messages, API_VERSION)[0]
    )
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=[
                        messages.Zone(name='zone-1'),
                        messages.Zone(name='zone-2')],
                   )
    self.StartPatch('googlecloudsdk.api_lib.compute.regions.service.List',
                    return_value=[
                        messages.Region(name='region-1')],
                   )
    self.WriteInput('3\n')
    self.Run("""
        compute instance-groups describe group-1
        """)
    self.AssertErrContains('group-1')
    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')
    self.AssertErrContains('region-1')

if __name__ == '__main__':
  test_case.main()
