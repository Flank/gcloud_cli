# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class _InstanceGroupManagersCreateZonalWithAutohealingTestBase(object):

  def _CheckInsertRequestWithAutohealing(self,
                                         initial_delay=None,
                                         health_check=None):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone='us-central2-a',
        baseInstanceName='instance-1',
        instanceTemplate=self.template_1_uri,
        targetSize=1)
    if initial_delay or health_check:
      autohealing_policy = self.messages.InstanceGroupManagerAutoHealingPolicy()
      if initial_delay:
        autohealing_policy.initialDelaySec = initial_delay
      if health_check:
        autohealing_policy.healthCheck = health_check
      igm.autoHealingPolicies = [autohealing_policy]

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=igm,
              project='my-project',
              zone='us-central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testWithAutohealing_GenericHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --health-check health-check-1
        """.format(*self.scope_params))

    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self._CheckInsertRequestWithAutohealing(health_check=health_check_uri)

  def testWithAutohealing_HttpHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --http-health-check health-check-1
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing(
        health_check=self.http_health_check_uri)

    # Check default output formatting
    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
    NAME     LOCATION     SCOPE   BASE_INSTANCE_NAME    SIZE  TARGET_SIZE  INSTANCE_TEMPLATE  AUTOSCALED
    group-1  {1}  {0}  test-instance-name-1  0     1            template-1         yes
    """.format(*self.scope_params),
        normalize_space=True)
    # pylint: enable=line-too-long

  def testWithAutohealing_HttpHealthCheckAndInitilDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --http-health-check health-check-1
          --initial-delay 1m
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing(
        initial_delay=60, health_check=self.http_health_check_uri)

  def testWithAutohealing_HttpsHealthCheck(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --https-health-check health-check-2
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing(
        health_check=self.https_health_check_uri)

  def testWithAutohealing_HttpsHealthCheckAndInitilDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --https-health-check health-check-2
          --initial-delay 130s
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing(
        initial_delay=130, health_check=self.https_health_check_uri)

  def testWithAutohealing_InitialDelay(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
          --initial-delay 10m
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing(initial_delay=10 * 60)

  def testWithAutohealing_EmptyPolicy(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --base-instance-name instance-1
          --size 1
        """.format(*self.scope_params))

    self._CheckInsertRequestWithAutohealing()

  def testWithAutohealing_BothHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --http-health-check: At most one of --health-check | '
        '--http-health-check | --https-health-check may be specified.'):
      self.Run("""
          compute instance-groups managed create group-1
            --{} {}
            --template template-1
            --base-instance-name instance-1
            --size 1
            --http-health-check health-check-1
            --https-health-check health-check-2
          """.format(*self.scope_params))


class _InstanceGroupManagersCreateRegionalWithAutohealingTestBase(
    _InstanceGroupManagersCreateZonalWithAutohealingTestBase):

  def _CheckInsertRequestWithAutohealing(self,
                                         initial_delay=None,
                                         health_check=None):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_uri,
        baseInstanceName='instance-1',
        instanceTemplate=self.template_1_uri,
        targetSize=1)
    if initial_delay or health_check:
      autohealing_policy = self.messages.InstanceGroupManagerAutoHealingPolicy()
      if initial_delay:
        autohealing_policy.initialDelaySec = initial_delay
      if health_check:
        autohealing_policy.healthCheck = health_check
      igm.autoHealingPolicies = [autohealing_policy]

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=igm,
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )


class _InstanceGroupManagersCreateZonalWithStatefulTestBase(object):

  def _CheckInsertRequestWithStateful(self, stateful_policy=None):
    self.CheckRequests(
        self.zone_1_get_request,
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
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def _MakePreservedStateDisksMapEntry(self, device_name, auto_delete=None):
    auto_delete_map = {
        'never':
            self.messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum.NEVER,
        'on-permanent-instance-deletion':
            self.messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum.ON_PERMANENT_INSTANCE_DELETION
    }
    disk_device_map_entry = (
        self.messages.StatefulPolicyPreservedState.DisksValue
        .AdditionalProperty(
            key=device_name,
            value=self.messages.StatefulPolicyPreservedStateDiskDevice()))
    if auto_delete:
      disk_device_map_entry.value.autoDelete = auto_delete_map[auto_delete]
    return disk_device_map_entry

  def testStatefulDisk(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-disk=device-name=disk-1,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._CheckInsertRequestWithStateful(
        self.messages.StatefulPolicy(
            preservedState=self.messages.StatefulPolicyPreservedState(
                disks=self.messages.StatefulPolicyPreservedState.DisksValue(
                    additionalProperties=[
                        self._MakePreservedStateDisksMapEntry(
                            'disk-1', 'on-permanent-instance-deletion')
                    ]))))

  def testStatefulMultipleDisks(self):
    self.Run("""
        compute instance-groups managed create group-1
          --{} {}
          --template template-1
          --size 1
          --stateful-disk=device-name=disk-1
          --stateful-disk=device-name=disk-2,auto-delete=never
          --stateful-disk=device-name=disk-3,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._CheckInsertRequestWithStateful(
        self.messages.StatefulPolicy(
            preservedState=self.messages.StatefulPolicyPreservedState(
                disks=self.messages.StatefulPolicyPreservedState.DisksValue(
                    additionalProperties=[
                        self._MakePreservedStateDisksMapEntry('disk-1'),
                        self._MakePreservedStateDisksMapEntry(
                            'disk-2', 'never'),
                        self._MakePreservedStateDisksMapEntry(
                            'disk-3', 'on-permanent-instance-deletion')
                    ])),
        ))

  def testEmptyStatefulDisks(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--stateful-disk: expected one argument'):
      self.Run("""
          compute instance-groups managed create group-1
            --{} {}
            --template template-1
            --size 1
            --stateful-disk
          """.format(*self.scope_params))


class _InstanceGroupManagersCreateRegionalWithStatefulTestBase(
    _InstanceGroupManagersCreateZonalWithStatefulTestBase):

  def _CheckInsertRequestWithStateful(self, stateful_policy=None):
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


class InstanceGroupManagersCreateZonalTestGA(
    _InstanceGroupManagersCreateZonalWithAutohealingTestBase,
    test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self._SetUpZonal('v1')

  def _SetUpZonal(self, api_version):
    self.SelectApi(api_version)
    self.zone = 'us-central2-a'
    self.scope_params = ('zone', self.zone)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name=self.zone),
        ],
        [
            test_resources.MakeInstanceGroupManagers(
                api_version, scope_name=self.zone)[0],
        ],
        [
            test_resources.MakeInstanceGroups(
                self.messages, api_version, scope_name=self.zone)[0],
        ],
        [
            test_resources.MakeAutoscalers(api_version,
                                           scope_name=self.zone)[0],
        ],
    ])
    self.zone_1_get_request = [(self.compute.zones, 'Get',
                                self.messages.ComputeZonesGetRequest(
                                    project='my-project', zone=self.zone))]
    self.zone_ig_list_request = [
        (self.compute.instanceGroups, 'List',
         self.messages.ComputeInstanceGroupsListRequest(
             maxResults=500,
             project='my-project',
             zone=self.zone,
         ))
    ]
    self.zone_as_list_request = [(self.compute.autoscalers, 'List',
                                  self.messages.ComputeAutoscalersListRequest(
                                      maxResults=500,
                                      project='my-project',
                                      zone=self.zone))]
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))
    self.http_health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.https_health_check_uri = (
        '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'
        .format(self.compute_uri))

  def testWithRequiredOptions(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone us-central2-a
          --template template-1
          --size 1
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [
            (self.compute.instanceGroupManagers, 'Insert',
             self.messages.ComputeInstanceGroupManagersInsertRequest(
                 instanceGroupManager=self.messages.InstanceGroupManager(
                     name='group-1',
                     zone='us-central2-a',
                     baseInstanceName='group-1',
                     instanceTemplate=self.template_1_uri,
                     targetPools=[],
                     targetSize=1,
                 ),
                 project='my-project',
                 zone='us-central2-a')),
        ],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

    # Check default output formatting
    self.AssertOutputEquals(
        """\
    NAME     LOCATION  SCOPE  BASE_INSTANCE_NAME    SIZE  TARGET_SIZE  INSTANCE_TEMPLATE  AUTOSCALED
    group-1  us-central2-a  zone   test-instance-name-1  0     1            template-1         yes
    """,
        normalize_space=True)

  def testZonal(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone us-central2-a
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers, 'Insert',
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
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testWithDescription(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone us-central2-a
          --template template-1
          --base-instance-name instance-1
          --size 1
          --description "Some description"
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='us-central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[],
                  targetSize=1,
                  description='Some description',
              ),
              project='my-project',
              zone='us-central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testWithTargetPools(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone us-central2-a
          --template template-1
          --base-instance-name instance-1
          --size 1
          --target-pool target-pool-1,target-pool-2
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='us-central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[
                      self.compute_uri + '/projects/my-project/regions'
                      '/us-central2/targetPools/target-pool-1',
                      self.compute_uri + '/projects/my-project/'
                      'regions/us-central2/targetPools/target-pool-2'
                  ],
                  targetSize=1,
              ),
              project='my-project',
              zone='us-central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testUrisupport(self):
    self.Run("""
        compute instance-groups managed create
        {0}/projects/my-project/zones/us-central2-a/instanceGroupManagers/group-1
          --template {0}/projects/my-project/global/instanceTemplates/template-1
          --base-instance-name instance-1
          --size 1
          --target-pool {0}/projects/cloud-autopilot-test/regions/central2/targetPools/target-pool-1
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='us-central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  targetPools=[
                      self.compute_uri + '/projects/'
                      'cloud-autopilot-test/regions/central2/'
                      'targetPools/target-pool-1'
                  ],
              ),
              project='my-project',
              zone='us-central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testRequiredSize(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --size: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --zone us-central2-a
            --template template-1
            --base-instance-name instance-1
          """)

  def testRequiredTemplate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --zone us-central2-a
            --base-instance-name instance-1
            --size 1
          """)

  def testPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central1-a'),
            self.messages.Zone(name='us-central1-b'),
            self.messages.Zone(name='us-central2-a'),
        ],
        [],
        [],
        [],
    ])
    self.WriteInput('2\n')

    self.Run("""
        compute instance-groups managed create group-1
          --template template-1
          --base-instance-name instance-1
          --size 1
    """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.zones, 'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project', zone='us-central1-a'))],
        [(self.compute.instanceGroupManagers, 'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  baseInstanceName='instance-1',
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{}/projects/'
                      'my-project/global/instanceTemplates/template-1'.format(
                          self.api)),
                  name='group-1',
                  namedPorts=[],
                  targetPools=[],
                  targetSize=1,
                  zone='us-central1-a'),
              project='my-project',
              zone='us-central1-a'))],
        [],
    )


class InstanceGroupManagersCreateZonalTestBeta(
    _InstanceGroupManagersCreateZonalWithStatefulTestBase,
    InstanceGroupManagersCreateZonalTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self._SetUpZonal('beta')


class InstanceGroupManagersCreateZonalTestAlpha(
    InstanceGroupManagersCreateZonalTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self._SetUpZonal('alpha')


class InstanceGroupManagersCreateRegionalTestGA(
    _InstanceGroupManagersCreateRegionalWithAutohealingTestBase,
    test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self._SetUpRegional('v1')

  def _SetUpRegional(self, api_version):
    self.SelectApi(api_version)
    self.region = 'us-central2'
    self.scope_params = ('region', self.region)
    self.make_requests.side_effect = iter([
        [
            test_resources.MakeInstanceGroupManagers(
                api_version, scope_name=self.region, scope_type='region')[0],
        ],
        [
            test_resources.MakeInstanceGroups(
                self.messages,
                api_version,
                scope_name=self.region,
                scope_type='region')[0],
        ],
        [
            test_resources.MakeAutoscalers(
                api_version, scope_name=self.region, scope_type='region')[0],
        ],
    ])
    self.region_ig_list_request = [
        (self.compute.regionInstanceGroups, 'List',
         self.messages.ComputeRegionInstanceGroupsListRequest(
             maxResults=500,
             project='my-project',
             region=self.region,
         ))
    ]
    self.region_as_list_request = [
        (self.compute.regionAutoscalers, 'List',
         self.messages.ComputeRegionAutoscalersListRequest(
             maxResults=500, project='my-project', region=self.region))
    ]
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))
    self.http_health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.https_health_check_uri = (
        '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'
        .format(self.compute_uri))
    self.region_uri = ('{0}/projects/my-project/regions/{1}'.format(
        self.compute_uri, self.region))

  def _ZoneUrl(self, zone):
    return '{}/projects/my-project/zones/{}'.format(self.compute_uri, zone)

  def testWithRequiredOptions(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --size 1
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
                  targetPools=[],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2')),],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithDescription(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --description "Some description"
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
                  targetPools=[],
                  targetSize=1,
                  description='Some description',
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithTargetPools(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --target-pool target-pool-1,target-pool-2
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
                  targetPools=[self.compute_uri + '/projects/my-project/regions'
                               '/us-central2/targetPools/target-pool-1',
                               self.compute_uri + '/projects/my-project/'
                               'regions/us-central2/targetPools/target-pool-2'],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testUrisupport(self):
    self.Run("""
        compute instance-groups managed create
        {0}/projects/my-project/regions/us-central2/instanceGroupManagers/group-1
          --template {0}/projects/my-project/global/instanceTemplates/template-1
          --base-instance-name instance-1
          --size 1
          --target-pool {0}/projects/cloud-autopilot-test/regions/us-central2/targetPools/target-pool-1
        """.format(self.compute_uri))

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
                  targetPools=[self.compute_uri + '/projects/'
                               'cloud-autopilot-test/regions/us-central2/'
                               'targetPools/target-pool-1'],
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testRequiredSize(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --size: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --region us-central2
            --template template-1
            --base-instance-name instance-1
          """)

  def testRequiredTemplate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --region us-central2
            --base-instance-name instance-1
            --size 1
          """)

  def testPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central1-a'),
            self.messages.Zone(name='us-central1-b'),
            self.messages.Zone(name='us-central2-a'),
        ],
        [],
        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute instance-groups managed create group-1
          --template template-1
          --base-instance-name instance-1
          --size 1
    """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  baseInstanceName='instance-1',
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{}/projects/'
                      'my-project/global/instanceTemplates/template-1'.format(
                          self.api)),
                  name='group-1',
                  namedPorts=[],
                  targetPools=[],
                  targetSize=1,
                  region=self.region_uri,
              ),
              project='my-project',
              region='us-central2'))],
        [],
    )

  def testNegativeSize(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --size: Value must be greater than or equal to 0; '
        'received: -1'):
      self.Run("""
          compute instance-groups managed create group-1
            --zone us-central2-a
            --template template-1
            --size -1
          """)

  def testWithUnaffixedZone(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zones us-central2-a
          --template template-1
          --size 3
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(zones=[
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-a')),
                  ])),
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
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(zones=[
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-a')),
                  ])),
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
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(zones=[
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-a')),
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-b')),
                  ])),
              project='my-project',
              region='us-central2'))],
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
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(zones=[
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-a')),
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-b')),
                  ])),
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
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=3,
                  distributionPolicy=self.messages.DistributionPolicy(zones=[
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-a')),
                      self.messages.DistributionPolicyZoneConfiguration(
                          zone=self._ZoneUrl('us-central2-b')),
                  ])),
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

  def testCreateSimple(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --size 1
          --instance-redistribution-type proactive
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  updatePolicy=self.messages.InstanceGroupManagerUpdatePolicy(
                      instanceRedistributionType=self.messages
                      .InstanceGroupManagerUpdatePolicy
                      .InstanceRedistributionTypeValueValuesEnum.PROACTIVE)),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testCreateForZonalScope(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='us-central2-a'),
        ],
    ])
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'Flag --instance-redistribution-type may be specified for regional '
        'managed instance groups only.'):
      self.Run("""
          compute instance-groups managed create group-1
            --zone us-central2-a
            --template template-1
            --size 1
            --instance-redistribution-type proactive
          """)


class InstanceGroupManagersCreateRegionalTestBeta(
    _InstanceGroupManagersCreateRegionalWithStatefulTestBase,
    InstanceGroupManagersCreateRegionalTestGA, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self._SetUpRegional('beta')


class InstanceGroupManagersCreateRegionalTestAlpha(
    InstanceGroupManagersCreateRegionalTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self._SetUpRegional('alpha')

  @parameterized.named_parameters(('Any', 'ANY'), ('Even', 'EVEN'))
  def testCreateWithDistributionTargetShape(self, target_shape):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --size 1
          --target-distribution-shape {target_shape}
        """.format(target_shape=target_shape))

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  distributionPolicy=self.messages.DistributionPolicy(
                      targetShape=(self.messages.DistributionPolicy
                                   .TargetShapeValueValuesEnum)(target_shape))),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  @parameterized.named_parameters(('Any', 'ANY'), ('Even', 'EVEN'))
  def testCreateForZonalScopeWithDistributionTargetShape(self, target_shape):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='us-central2-a'),
        ],
    ])
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'Flag --target-distribution-shape may be specified for regional managed instance '
        'groups only.'):
      self.Run("""
          compute instance-groups managed create group-1
            --zone us-central2-a
            --template template-1
            --size 1
            --target-distribution-shape {target_shape}
        """.format(target_shape=target_shape))


if __name__ == '__main__':
  test_case.main()
