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
"""Tests for the instance-groups managed describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources
from mock import patch

API_VERSION = 'v1'
messages = core_apis.GetMessagesModule('compute', API_VERSION)


def SetUpMockClient(api):
  mock_client = mock.Client(
      core_apis.GetClientClass('compute', api),
      real_client=core_apis.GetClientInstance('compute', api, no_http=True))
  mock_client.Mock()
  return mock_client


class ManagedInstanceGroupsDescribeTest(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_client = SetUpMockClient(API_VERSION)
    self.addCleanup(self.mock_client.Unmock)
    self.compute_uri = 'https://www.googleapis.com/compute/{0}'.format(
        self.track.prefix or 'v1')

  def _MockAutoscalerRequest(self, return_value):
    # Only listing autoscalers uses this.
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        return_value=return_value,
    )

  def testDescribeZonal(self):
    self.mock_client.instanceGroupManagers.Get.Expect(
        messages.ComputeInstanceGroupManagersGetRequest(
            instanceGroupManager='group-1',
            project='fake-project',
            zone='zone-1'),
        test_resources.MakeInstanceGroupManagers(API_VERSION)[0]
    )
    self._MockAutoscalerRequest([])

    self.Run("""
        compute instance-groups managed describe group-1 --zone zone-1
        """)

    self.assertMultiLineEqual(
        encoding.Decode(self.stdout.getvalue()),
        textwrap.dedent("""\
            baseInstanceName: test-instance-name-1
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test description.
            fingerprint: MTIzNA==
            instanceGroup: {0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            instanceTemplate: {0}/projects/my-project/global/instanceTemplates/template-1
            name: group-1
            selfLink: {0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1
            targetSize: 1
            zone: {0}/projects/my-project/zones/zone-1
            """.format(self.compute_uri)))

  def testDescribeRegional(self):
    self.mock_client.regionInstanceGroupManagers.Get.Expect(
        messages.ComputeRegionInstanceGroupManagersGetRequest(
            instanceGroupManager='group-1',
            project='fake-project',
            region='region-1'),
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1')[0]
    )
    self._MockAutoscalerRequest([])
    self.Run("""
        compute instance-groups managed describe group-1 --region region-1
        """)

    self.assertMultiLineEqual(
        encoding.Decode(self.stdout.getvalue()),
        textwrap.dedent("""\
            baseInstanceName: test-instance-name-1
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test description.
            fingerprint: MTIzNA==
            instanceGroup: {0}/projects/my-project/regions/region-1/instanceGroups/group-1
            instanceTemplate: {0}/projects/my-project/global/instanceTemplates/template-1
            name: group-1
            region: {0}/projects/my-project/regions/region-1
            selfLink: {0}/projects/my-project/regions/region-1/instanceGroupManagers/group-1
            targetSize: 1
            """.format(self.compute_uri)))

  def testDescribeAutoscaledZonal(self):
    self.mock_client.instanceGroupManagers.Get.Expect(
        messages.ComputeInstanceGroupManagersGetRequest(
            instanceGroupManager='group-1',
            project='fake-project',
            zone='zone-1'),
        test_resources.MakeInstanceGroupManagers(API_VERSION)[0]
    )
    self._MockAutoscalerRequest(test_resources.MakeAutoscalers(API_VERSION))

    self.Run("""
        compute instance-groups managed describe group-1 --zone zone-1
        """)

    self.assertMultiLineEqual(
        encoding.Decode(self.stdout.getvalue()),
        textwrap.dedent("""\
            autoscaler:
              autoscalingPolicy:
                coolDownPeriodSec: 60
                cpuUtilization:
                  utilizationTarget: 0.8
                customMetricUtilizations:
                - metric: custom.cloudmonitoring.googleapis.com/seconds
                  utilizationTarget: 60.0
                  utilizationTargetType: DELTA_PER_MINUTE
                loadBalancingUtilization:
                  utilizationTarget: 0.9
                maxNumReplicas: 10
                minNumReplicas: 2
              creationTimestamp: Two days ago
              id: '1'
              name: autoscaler-1
              selfLink: {0}/projects/my-project/zones/zone-1/autoscalers/autoscaler-1
              target: {0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1
              zone: {0}/projects/my-project/zones/zone-1
            baseInstanceName: test-instance-name-1
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test description.
            fingerprint: MTIzNA==
            instanceGroup: {0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            instanceTemplate: {0}/projects/my-project/global/instanceTemplates/template-1
            name: group-1
            selfLink: {0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1
            targetSize: 1
            zone: {0}/projects/my-project/zones/zone-1
            """.format(self.compute_uri)))

  def testDescribeAutoscaledRegional(self):
    self.mock_client.regionInstanceGroupManagers.Get.Expect(
        messages.ComputeRegionInstanceGroupManagersGetRequest(
            instanceGroupManager='group-1',
            project='fake-project',
            region='region-1'),
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1')[0]
    )
    self._MockAutoscalerRequest(test_resources.MakeAutoscalers(
        API_VERSION, scope_name='region-1', scope_type='region'))
    self.Run("""
        compute instance-groups managed describe group-1 --region region-1
        """)

    self.assertMultiLineEqual(
        encoding.Decode(self.stdout.getvalue()),
        textwrap.dedent("""\
            autoscaler:
              autoscalingPolicy:
                coolDownPeriodSec: 60
                cpuUtilization:
                  utilizationTarget: 0.8
                customMetricUtilizations:
                - metric: custom.cloudmonitoring.googleapis.com/seconds
                  utilizationTarget: 60.0
                  utilizationTargetType: DELTA_PER_MINUTE
                loadBalancingUtilization:
                  utilizationTarget: 0.9
                maxNumReplicas: 10
                minNumReplicas: 2
              creationTimestamp: Two days ago
              id: '1'
              name: autoscaler-1
              region: {0}/projects/my-project/regions/region-1
              selfLink: {0}/projects/my-project/regions/region-1/autoscalers/autoscaler-1
              target: {0}/projects/my-project/regions/region-1/instanceGroupManagers/group-1
            baseInstanceName: test-instance-name-1
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test description.
            fingerprint: MTIzNA==
            instanceGroup: {0}/projects/my-project/regions/region-1/instanceGroups/group-1
            instanceTemplate: {0}/projects/my-project/global/instanceTemplates/template-1
            name: group-1
            region: {0}/projects/my-project/regions/region-1
            selfLink: {0}/projects/my-project/regions/region-1/instanceGroupManagers/group-1
            targetSize: 1
            """.format(self.compute_uri)))

  def testScopePrompt(self):
    self.mock_client.instanceGroupManagers.Get.Expect(
        messages.ComputeInstanceGroupManagersGetRequest(
            instanceGroupManager='group-1',
            project='fake-project',
            zone='zone-2'),
        test_resources.MakeInstanceGroupManagers(API_VERSION)[0]
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
    self._MockAutoscalerRequest(test_resources.MakeAutoscalers(API_VERSION))
    self.WriteInput('3\n')
    self.Run("""
        compute instance-groups managed describe group-1
        """)
    self.AssertErrContains('group-1')
    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')
    self.AssertErrContains('region-1')

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed describe group-1 --zone zone-1')


if __name__ == '__main__':
  test_case.main()
