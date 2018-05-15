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

"""Tests for the instance-groups managed create subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'alpha'


def SetUpRegional(test_obj, api_version):
  test_obj.SelectApi(api_version)
  test_obj.make_requests.side_effect = iter([
      [
          test_resources.MakeInstanceGroupManagers(
              API_VERSION, scope_name='us-central2', scope_type='region')[0],
      ],
      [
          test_resources.MakeInstanceGroups(
              test_obj.messages, API_VERSION, scope_name='us-central2',
              scope_type='region')[0],
      ],
      [
          test_resources.MakeAutoscalers(
              API_VERSION, scope_name='us-central2', scope_type='region')[0],
      ],
  ])
  test_obj.region_ig_list_request = [(
      test_obj.compute.regionInstanceGroups,
      'List',
      test_obj.messages.ComputeRegionInstanceGroupsListRequest(
          maxResults=500,
          project='my-project',
          region='us-central2',
      ))]
  test_obj.region_as_list_request = [(
      test_obj.compute.regionAutoscalers,
      'List',
      test_obj.messages.ComputeRegionAutoscalersListRequest(
          maxResults=500,
          project='my-project',
          region='us-central2'))]
  test_obj.template_1_uri = (
      '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
          test_obj.compute_uri))
  test_obj.http_health_check_uri = (
      '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
          test_obj.compute_uri))
  test_obj.https_health_check_uri = (
      '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'.format(
          test_obj.compute_uri))
  test_obj.region_uri = (
      '{0}/projects/my-project/regions/us-central2'.format(
          test_obj.compute_uri))


def SetUpZonal(test_obj, api_version):
  test_obj.SelectApi(api_version)
  test_obj.make_requests.side_effect = iter([
      [
          test_resources.MakeInstanceGroupManagers(
              API_VERSION, scope_name='us-central2-a', scope_type='zone')[0],
      ],
      [
          test_resources.MakeInstanceGroups(
              test_obj.messages, API_VERSION, scope_name='us-central2-a',
              scope_type='zone')[0],
      ],
      [
          test_resources.MakeAutoscalers(
              API_VERSION, scope_name='us-central2-a', scope_type='zone')[0],
      ],
  ])
  test_obj.ig_list_request = [(
      test_obj.compute.instanceGroups,
      'List',
      test_obj.messages.ComputeInstanceGroupsListRequest(
          maxResults=500,
          project='my-project',
          zone='us-central2-a',
      ))]
  test_obj.as_list_request = [(
      test_obj.compute.autoscalers,
      'List',
      test_obj.messages.ComputeAutoscalersListRequest(
          maxResults=500,
          project='my-project',
          zone='us-central2-a'))]
  test_obj.template_1_uri = (
      '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
          test_obj.compute_uri))
  test_obj.http_health_check_uri = (
      '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
          test_obj.compute_uri))
  test_obj.https_health_check_uri = (
      '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'.format(
          test_obj.compute_uri))
  test_obj.zone_uri = (
      '{0}/projects/my-project/zones/us-central2-a'.format(
          test_obj.compute_uri))


class InstanceGroupManagersCreateTestWithAutohealing(test_base.BaseTest):

  def SetUp(self):
    SetUpRegional(self, API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWithAutohealing_HttpHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --http-health-check health-check-1
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  autoHealingPolicies=[
                      self.messages.InstanceGroupManagerAutoHealingPolicy(
                          healthCheck=self.http_health_check_uri),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

    # Check default output formatting
    self.AssertOutputEquals("""\
    NAME     LOCATION     SCOPE   BASE_INSTANCE_NAME    SIZE  TARGET_SIZE  INSTANCE_TEMPLATE  AUTOSCALED
    group-1  us-central2  region  test-instance-name-1  0     1            template-1         yes
    """, normalize_space=True)

  def testWithAutohealing_HttpHealthCheckAndInitilDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --http-health-check health-check-1
          --initial-delay 1m
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  autoHealingPolicies=[
                      self.messages.InstanceGroupManagerAutoHealingPolicy(
                          healthCheck=self.http_health_check_uri,
                          initialDelaySec=60),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithAutohealing_HttpsHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --https-health-check health-check-2
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  autoHealingPolicies=[
                      self.messages.InstanceGroupManagerAutoHealingPolicy(
                          healthCheck=self.https_health_check_uri),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithAutohealing_HttpsHealthCheckAndInitilDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --https-health-check health-check-2
          --initial-delay 130s
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  autoHealingPolicies=[
                      self.messages.InstanceGroupManagerAutoHealingPolicy(
                          healthCheck=self.https_health_check_uri,
                          initialDelaySec=130),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithAutohealing_InitialDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --initial-delay 10m
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  autoHealingPolicies=[
                      self.messages.InstanceGroupManagerAutoHealingPolicy(
                          initialDelaySec=10*60),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithAutohealing_EmptyPolicy(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithAutohealing_BothHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --http-health-check: At most one of --health-check | '
        '--http-health-check | --https-health-check may be specified.'):
      self.Run("""
          compute instance-groups managed create group-1
            --region us-central2
            --template template-1
            --base-instance-name instance-1
            --size 1
            --http-health-check health-check-1
            --https-health-check health-check-2
          """)


class InstanceGroupManagersCreateTestWitStateful(test_base.BaseTest):

  def SetUp(self):
    SetUpZonal(self, API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.scope_params = ('zone', 'us-central2-a')

  def checkInsertRequest(self, stateful_policy=None):
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='us-central2-a',
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  statefulPolicy=stateful_policy),
              project='my-project',
              zone='us-central2-a'))],
        self.ig_list_request,
        self.as_list_request,
    )

  def testStatefulDisk(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-disks disk-1
        """.format(*self.scope_params))

    self.checkInsertRequest(
        self.messages.StatefulPolicy(
            preservedResources=(self.messages.StatefulPolicyPreservedResources(
                disks=[
                    self.messages.StatefulPolicyPreservedDisk(
                        deviceName='disk-1'),
                ],))))

  def testStatefulMultipleDisks(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-disks disk-1,disk-2,disk-3
        """.format(*self.scope_params))

    self.checkInsertRequest(
        self.messages.StatefulPolicy(
            preservedResources=(self.messages.StatefulPolicyPreservedResources(
                disks=[
                    self.messages.StatefulPolicyPreservedDisk(
                        deviceName='disk-1'),
                    self.messages.StatefulPolicyPreservedDisk(
                        deviceName='disk-2'),
                    self.messages.StatefulPolicyPreservedDisk(
                        deviceName='disk-3'),
                ],))))

  def testEmptyStatefulDisks(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--stateful-disks: expected one argument'):
      self.Run("""
          compute instance-groups managed create group-1
            --{} {}
            --template template-1
            --size 1
            --stateful-disks
          """.format(*self.scope_params))

  def testStatefulNames(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-names
        """.format(*self.scope_params))

    self.checkInsertRequest(self.messages.StatefulPolicy())

  def testStatefulDisksWithNoStatefulNames(self):
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-disks device-1
          --no-stateful-names
        """.format(*self.scope_params))

  def testNoStatefulNames(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --no-stateful-names
        """.format(*self.scope_params))

    self.checkInsertRequest()


class RegionalInstanceGroupManagersCreateTestWithStateful(
    InstanceGroupManagersCreateTestWitStateful):

  def SetUp(self):
    SetUpRegional(self, API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.scope_params = ('region', 'us-central2')

  def checkInsertRequest(self, stateful_policy=None):
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  statefulPolicy=stateful_policy),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )


if __name__ == '__main__':
  test_case.main()
