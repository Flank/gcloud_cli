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

"""Tests for the instance-groups managed create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'beta'


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


class InstanceGroupManagersCreateTestWithAutohealing(test_base.BaseTest):

  def SetUp(self):
    SetUpRegional(self, API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA

  def testWithAutohealing_GenericHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --health-check health-check-1
        """)

    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
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
                          healthCheck=health_check_uri),
                  ],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

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


class InstanceGroupManagersCreateTestWithZoneSelection(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    SetUpRegional(self, self.track.prefix)

  def _ZoneUrl(self, zone):
    return '{}/projects/my-project/zones/{}'.format(self.compute_uri, zone)

  def testWithUnaffixedZone(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones us-central2-a
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(
                      zones=[
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-a')
                          ),
                      ]
                  )
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithUnaffixedZoneByUrl(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones {}/projects/my-project/zones/us-central2-a
          --template template-1
          --size 3
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(
                      zones=[
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-a')
                          ),
                      ]
                  )
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithSelectedZones(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones us-central2-a,us-central2-b
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(
                      zones=[
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-a')
                          ),
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-b')
                          ),
                      ]
                  )
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testZonal(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone us-central2-a
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='us-central2-a',
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
              ),
              project='my-project',
              zone='us-central2-a'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithSelectedZonesAndRegion(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones us-central2-a,us-central2-b
          --region us-central2
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(
                      zones=[
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-a')
                          ),
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-b')
                          ),
                      ]
                  )
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithSelectedZonesAndRegionByUri(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones us-central2-a,us-central2-b
          --region {}/projects/my-project/regions/us-central2
          --template template-1
          --size 3
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(
                      zones=[
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-a')
                          ),
                          self.messages.DistributionPolicyZoneConfiguration(
                              zone=self._ZoneUrl('us-central2-b')
                          ),
                      ]
                  )
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testRegionZonesConflict(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""
        compute instance-groups managed create group-1
          --zones us-central1-a
          --region us-central2
          --template template-1
          --size 3
        """)

  def testZonesZoneConflict(self):
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run("""
        compute instance-groups managed create group-1
          --zone us-central1-a
          --zones us-central1-a,us-central1-b
          --template template-1
          --size 3
        """)

  def testZonesFromDifferentRegions(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""
        compute instance-groups managed create group-1
          --zones us-central1-a,us-central2-b
          --template template-1
          --size 3
        """)

if __name__ == '__main__':
  test_case.main()
