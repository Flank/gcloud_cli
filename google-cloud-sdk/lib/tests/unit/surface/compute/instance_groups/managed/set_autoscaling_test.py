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
"""Tests for the instance-groups managed set-autoscaling subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import os
import random

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


def _GetUtilizationTargetType(messages, str_form):
  return (messages.AutoscalingPolicyCustomMetricUtilization.
          UtilizationTargetTypeValueValuesEnum)(str_form)


class InstanceGroupManagersSetAutoscalingZonalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = (
      test_resources.MakeInstanceGroupManagers(API_VERSION))
  AUTOSCALERS = test_resources.MakeAutoscalers(API_VERSION)

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        self.AUTOSCALERS[1:],
        []  # Insert autoscaler.
    ])

    self.StartObjectPatch(random, 'choice').return_value = 'a'
    self.autoscalers_list_request = [
        (
            self.compute.autoscalers,
            'List', self.messages.ComputeAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                zone='zone-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get', self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]
    self.managed_instance_group_self_link = (
        '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1'
        .format(self.compute_uri)
    )

  def testInsertMinimalAutoscaler(self):
    self.Run('compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1')
    self.StartPatch('googlecloudsdk.core.properties.VALUES'
                    '.core.disable_prompts.GetBool',
                    return_value=False)
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Insert', request)],
    )

  def testInsertMinimalAutoscalerWithGKEWarning_proceed(self):
    self.StartPatch('googlecloudsdk.core.properties.VALUES'
                    '.core.disable_prompts.GetBool',
                    return_value=False)
    self.WriteInput('Y\n')
    custom_managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get', self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='gke-test-cluster-default-pool-9020bb-grp',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]
    custom_self_link = (
        '{0}/projects/my-project/zones/zone-1/'
        'instanceGroupManagers/gke-test-cluster-default-pool-9020bb-grp'
        .format(self.compute_uri)
    )

    self.Run('compute instance-groups managed set-autoscaling '
             'gke-test-cluster-default-pool-9020bb-grp '
             '--max-num-replicas 10 --zone zone-1')

    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='gke-test-cluster-default-pool-9020bb-grp-aaaa',
            target=custom_self_link
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        custom_managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Insert', request)],
    )

  def testInsertMinimalAutoscalerWithGKEWarning_abort(self):
    self.StartPatch('googlecloudsdk.core.properties.VALUES'
                    '.core.disable_prompts.GetBool',
                    return_value=False)
    self.WriteInput('n\n')
    custom_managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get', self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='gke-test-cluster-default-pool-9020bb-grp',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]

    with self.assertRaisesRegexp(
        console_io.OperationCancelledError,
        r'Setting autoscaling aborted by user.'):
      self.Run('compute instance-groups managed set-autoscaling '
               'gke-test-cluster-default-pool-9020bb-grp '
               '--max-num-replicas 10 --zone zone-1')

    self.CheckRequests(custom_managed_instance_group_get_request)

  def testUpdateMinimalAutoscalerWithScopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-1'), self.messages.Zone(name='zone-2')],
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS,
        []
    ])

    self.Run('compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10')

    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testInsertAutoscalerWithEverything(self):
    self.Run('compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 '
             '--zone zone-1 '
             '--cool-down-period 1m '
             '--description whatever '
             '--min-num-replicas 5 '
             '--max-num-replicas 10 '
             '--scale-based-on-cpu --target-cpu-utilization 0.5 '
             '--scale-based-on-load-balancing '
             '--target-load-balancing-utilization 0.8 '
             '--custom-metric-utilization metric=metric1,utilization-target=1,'
             'utilization-target-type=GAUGE '
             '--custom-metric-utilization metric=metric2,utilization-target=2,'
             'utilization-target-type=DELTA_PER_SECOND '
             '--custom-metric-utilization metric=metric3,utilization-target=3,'
             'utilization-target-type=DELTA_PER_MINUTE '
            )
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                cpuUtilization=self.messages.AutoscalingPolicyCpuUtilization(
                    utilizationTarget=0.5,
                ),
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric1',
                        utilizationTarget=1.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'GAUGE'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric2',
                        utilizationTarget=2.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_SECOND'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric3',
                        utilizationTarget=3.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    ),
                ],
                loadBalancingUtilization=(
                    self.messages.AutoscalingPolicyLoadBalancingUtilization)(
                        utilizationTarget=0.8,
                    ),
                maxNumReplicas=10,
                minNumReplicas=5,
                coolDownPeriodSec=60,
            ),
            description='whatever',
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Insert', request)],
    )

  def testAssertsIgmExists(self):
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1')

    self.CheckRequests(self.managed_instance_group_get_request)

  def testAssertsPositiveMinSize(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --min-num-replicas: Value must be greater than or equal to '
        r'0; received: -1'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--min-num-replicas -1')

  def testAssertsPositiveMaxSize(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --max-num-replicas: Value must be greater than or equal to '
        r'0; received: -1'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas -10 --zone zone-1')

  def testAssertsMaxSizeGreaterThanMinSize(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--max-num-replicas\]: can\'t be less than min '
        r'num replicas\.'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--min-num-replicas 11')

  def testAssertsCpuTargetIsPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-cpu-utilization: '
        r'Value must be greater than or equal to 0.0; received: -0.1\d*'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--target-cpu-utilization -0.11')

  def testAssertsCpuTargetNotAboveOne(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-cpu-utilization: '
        r'Value must be less than or equal to 1.0; received: 1.1\d*'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--target-cpu-utilization 1.1')

  def testAssertsCustomMetricSpecificationComplete(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--custom-metric-utilization\]: metric not '
        r'present\.'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--custom-metric-utilization utilization-target=1,'
               'utilization-target-type=GAUGE')

  def testAssertsCustomMetricTargetPositive(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for '
        r'\[--custom-metric-utilization utilization-target\]: less than 0\.'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--custom-metric-utilization utilization-target=-1,'
               'utilization-target-type=GAUGE,metric=metric')

  def testAssertsLbTargetPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-load-balancing-utilization: '
        r'Value must be greater than or equal to 0.0; received: -0.1\d*'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--target-load-balancing-utilization -0.11')


class InstanceGroupManagersSetAutoscalingRegionalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = test_resources.MakeInstanceGroupManagers(
      api=API_VERSION, scope_name='region-1', scope_type='region')
  AUTOSCALERS = test_resources.MakeAutoscalers(
      api=API_VERSION, scope_name='region-1', scope_type='region')

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        self.AUTOSCALERS[1:],
        []  # Insert autoscaler.
    ])

    self.StartObjectPatch(random, 'choice').return_value = 'a'
    self.autoscalers_list_request = [
        (
            self.compute.regionAutoscalers,
            'List', self.messages.ComputeRegionAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                region='region-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.regionInstanceGroupManagers,
            'Get', self.messages.ComputeRegionInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                region='region-1',
            ),
        )
    ]
    self.managed_instance_group_self_link = (
        '{0}/projects/my-project/regions/region-1/instanceGroupManagers/group-1'
        .format(self.compute_uri)
    )
    self.region_self_link = (
        '{0}/projects/my-project/regions/region-1'.format(self.compute_uri))

  def testInsertMinimalAutoscaler(self):
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10 --region region-1
        """)
    request = self.messages.ComputeRegionAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        region='region-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.regionAutoscalers, 'Insert', request)],
    )

  def testUpdateMinimalAutoscalerWithScopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-1'), self.messages.Zone(name='zone-2')],
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS,
        []
    ])

    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
        """)

    request = self.messages.ComputeRegionAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        region='region-1',
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.regionAutoscalers, 'Update', request)],
    )

  def testInsertAutoscalerWithEverything(self):
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
            --region region-1
            --cool-down-period 1m
            --description whatever
            --min-num-replicas 5
            --max-num-replicas 10
            --scale-based-on-cpu --target-cpu-utilization 0.5
            --scale-based-on-load-balancing
            --target-load-balancing-utilization 0.8
            --custom-metric-utilization metric=metric1,utilization-target=1,utilization-target-type=GAUGE
            --custom-metric-utilization metric=metric2,utilization-target=2,utilization-target-type=DELTA_PER_SECOND
            --custom-metric-utilization metric=metric3,utilization-target=3,utilization-target-type=DELTA_PER_MINUTE
        """)
    request = self.messages.ComputeRegionAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                cpuUtilization=self.messages.AutoscalingPolicyCpuUtilization(
                    utilizationTarget=0.5,
                ),
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric1',
                        utilizationTarget=1.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'GAUGE'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric2',
                        utilizationTarget=2.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_SECOND'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='metric3',
                        utilizationTarget=3.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    ),
                ],
                loadBalancingUtilization=(
                    self.messages.AutoscalingPolicyLoadBalancingUtilization)(
                        utilizationTarget=0.8,
                    ),
                maxNumReplicas=10,
                minNumReplicas=5,
                coolDownPeriodSec=60,
            ),
            description='whatever',
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        region='region-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.regionAutoscalers, 'Insert', request)],
    )

  def testAssertsIgmExists(self):
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --max-num-replicas 10
              --region region-1
          """)

    self.CheckRequests(self.managed_instance_group_get_request)

  def testAssertsPositiveMinSize(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --min-num-replicas: Value must be greater than or equal to '
        '0; received: -1'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --min-num-replicas -1
          """)

  def testAssertsPositiveMaxSize(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --max-num-replicas: Value must be greater than or equal to '
        '0; received: -1'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas -10
          """)

  def testAssertsMaxSizeGreaterThanMinSize(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--max-num-replicas\]: can\'t be less than min '
        r'num replicas\.'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --region region-1 '
               '--min-num-replicas 11')

  def testAssertsCpuTargetIsPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-cpu-utilization: '
        r'Value must be greater than or equal to 0.0; received: -0.1\d*'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --target-cpu-utilization -0.1
          """)

  def testAssertsCpuTargetNotAboveOne(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-cpu-utilization: '
        r'Value must be less than or equal to 1.0; received: 1.1\d*'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --target-cpu-utilization 1.1
          """)

  def testAssertsCustomMetricSpecificationComplete(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--custom-metric-utilization\]: metric not '
        r'present\.'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --custom-metric-utilization utilization-target=1,utilization-target-type=GAUGE
           """)

  def testAssertsCustomMetricTargetPositive(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for '
        r'\[--custom-metric-utilization utilization-target\]: less than 0\.'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --custom-metric-utilization utilization-target=-1,utilization-target-type=GAUGE,metric=metric
          """)

  def testAssertsLbTargetPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --target-load-balancing-utilization: '
        r'Value must be greater than or equal to 0.0; received: -0.1\d*'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --region region-1
              --max-num-replicas 10
              --target-load-balancing-utilization -0.1
          """)


class InstanceGroupManagersSetAutoscalingZonalBetaTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = (
      test_resources.MakeInstanceGroupManagers('beta'))
  AUTOSCALERS = test_resources.MakeAutoscalers('beta')

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.StartObjectPatch(random, 'choice').return_value = 'a'
    self.autoscalers_list_request = [
        (
            self.compute.autoscalers,
            'List',
            self.messages.ComputeAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                zone='zone-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get',
            self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]
    self.autoscaler_delete_request = [
        (
            self.compute.autoscalers,
            'Delete',
            self.messages.ComputeAutoscalersDeleteRequest(
                autoscaler='autoscaler-1',
                project='my-project',
                zone='zone-1'
            ),
        )
    ]
    self.autoscaler_insert_request = [
        (
            self.compute.autoscalers,
            'Insert',
            self.messages.ComputeAutoscalersInsertRequest(
                autoscaler=self.messages.Autoscaler(
                    name='group-1-aaaa',
                    statusDetails=[],
                ),
                project='my-project',
                zone='zone-1',
            ),
        )
    ]
    self.autoscaler_update_request = [
        (
            self.compute.autoscalers,
            'Update',
            self.messages.ComputeAutoscalersUpdateRequest(
                autoscalerResource=self.messages.Autoscaler(
                    name='autoscaler-1',
                    statusDetails=[],
                ),
                autoscaler='autoscaler-1',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]

  def _GetAutoscalingFilePath(self):
    output_dir = self.CreateTempDir()
    return os.path.join(output_dir, 'autoscaling_file.json')

  def testFlagConflictingWithAutoscalingFile(self):
    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'arguments not allowed simultaneously: --autoscaling-file, .+'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --autoscaling-file file
          """)

  def testSetAutoscalingFromFile_NewIsNoneOldIsNone(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        [],  # List autoscalers.
    ])
    autoscaling_file_path = self._GetAutoscalingFilePath()
    with open(autoscaling_file_path, 'w') as f:
      f.write('null')
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --zone zone-1
        --autoscaling-file {}
        """.format(autoscaling_file_path))
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
    )

  def testSetAutoscalingFromFile_NewIsNoneOldExists(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[1]],  # Get IGM.
        self.AUTOSCALERS,  # List autoscalers.
        [],
    ])
    autoscaling_file_path = self._GetAutoscalingFilePath()
    with open(autoscaling_file_path, 'w') as f:
      f.write('null')
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --zone zone-1
        --autoscaling-file {}
        """.format(autoscaling_file_path))
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        self.autoscaler_delete_request,
    )

  def testSetAutoscalingFromFile_NewExistsOldIsNone(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[1]],  # Get IGM.
        [],  # List autoscalers.
        [],
    ])
    autoscaling_file_path = self._GetAutoscalingFilePath()
    with open(autoscaling_file_path, 'w') as f:
      f.write('{"max_num_replicas": 10}')
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --zone zone-1
        --autoscaling-file {}
        """.format(autoscaling_file_path))
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        self.autoscaler_insert_request,
    )

  def testSetAutoscalingFromFile_NewExistsOldExists(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[1]],  # Get IGM.
        self.AUTOSCALERS,  # List autoscalers.
        [],
    ])
    autoscaling_file_path = self._GetAutoscalingFilePath()
    with open(autoscaling_file_path, 'w') as f:
      f.write('{"max_num_replicas": 10}')
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --zone zone-1
        --autoscaling-file {}
        """.format(autoscaling_file_path))
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        self.autoscaler_update_request,
    )

  def testSetAutoscalingFromFile_NewExistsOldExistsHasDifferentName(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[1]],  # Get IGM.
        self.AUTOSCALERS,  # List autoscalers.
        [],  # Delete autoscaler
        [],  # Insert autoscaler
    ])
    autoscaling_file_path = self._GetAutoscalingFilePath()
    with open(autoscaling_file_path, 'w') as f:
      f.write('{"max_num_replicas": 10, "name": "group-1-aaaa"}')
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --zone zone-1
        --autoscaling-file {}
        """.format(autoscaling_file_path))
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        self.autoscaler_delete_request,
        self.autoscaler_insert_request,
    )

  def testFlagConflictCustomMetricUtilizationVsUpdateStackdriverMetric(self):
    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'arguments not allowed simultaneously: --custom-metric-utilization, '
        r'--update-stackdriver-metric'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --custom-metric-utilization metric=metric1,utilization-target=1,utilization-target-type=GAUGE
          --update-stackdriver-metric lol.n00b
          """)

  def testFlagRequiringUpdateStackdriverMetric(self):
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        r'\[--update-stackdriver-metric\] required to use this flag'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --stackdriver-metric-filter some-expression
          """)

  def testRequiredByUpdateStackdriverMetric(self):
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        r'Missing required argument \[--update-stackdriver-metric\]: '
        r'You must provide one of .+ with'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --update-stackdriver-metric lol.n00b
          """)

  def testSingleInstanceAssignmentVsUtilizationTarget(self):
    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'You cannot use any of .+ with `.+`'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --update-stackdriver-metric lol.n00b
          --stackdriver-metric-single-instance-assignment 11
          --stackdriver-metric-utilization-target 12
          """)

  def testUtilizationTargetNeedsType(self):
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        r'Required with \[--stackdriver-metric-utilization-target\]'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
          --zone zone-1
          --max-num-replicas 10
          --update-stackdriver-metric lol.n00b
          --stackdriver-metric-utilization-target 12
          """)

  def testKeepOldAutoscalingMetricsByDefault(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
            --zone zone-1
        """)
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/seconds',
                        utilizationTarget=60.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    ),
                ],
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=(
                '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/'
                'group-1'.format(self.compute_uri)),
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testUpdateOldAutoscalingMetric(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
            --zone zone-1
            --update-stackdriver-metric
              custom.cloudmonitoring.googleapis.com/seconds
            --stackdriver-metric-utilization-target 0.9999
            --stackdriver-metric-utilization-target-type delta-per-second
        """)
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/seconds',
                        utilizationTarget=0.9999,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_SECOND'),
                    ),
                ],
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=(
                '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/'
                'group-1'.format(self.compute_uri)),
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testAddAutoscalingMetric(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
            --zone zone-1
            --update-stackdriver-metric
              custom.cloudmonitoring.googleapis.com/sith
            --stackdriver-metric-utilization-target 2
            --stackdriver-metric-utilization-target-type delta-per-second
        """)
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/seconds',
                        utilizationTarget=60,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/sith',
                        utilizationTarget=2,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_SECOND'),
                    ),
                ],
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=(
                '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/'
                'group-1'.format(self.compute_uri)),
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testRemoveAutoscalingMetric(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
            --max-num-replicas 10
            --target-cpu-utilization 0.32
            --zone zone-1
            --remove-stackdriver-metric
              custom.cloudmonitoring.googleapis.com/seconds
        """)
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                cpuUtilization=self.messages.AutoscalingPolicyCpuUtilization(
                    utilizationTarget=0.32,
                ),
                maxNumReplicas=10,
            ),
            name='autoscaler-1',
            target=(
                '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/'
                'group-1'.format(self.compute_uri)),
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testRemoveOnlyAutoscalingMetric(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--remove-stackdriver-metric\]: This would remove '
        r'the only signal used for autoscaling. If you want to stop '
        r'autoscaling the Managed Instance Group use `stop-autoscaling` '
        r'command instead\.'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --max-num-replicas 10
              --min-num-replicas 1
              --zone zone-1
              --remove-stackdriver-metric
                custom.cloudmonitoring.googleapis.com/seconds
          """)

  def testNoRemovingAnDupdatingMetricAtOnce(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'You can not remove Stackdriver metric you are updating with '
        r'\[--update-stackdriver-metric\] flag.'):
      self.Run("""
          compute instance-groups managed set-autoscaling group-1
              --max-num-replicas 10
              --min-num-replicas 1
              --zone zone-1
              --remove-stackdriver-metric
                custom.cloudmonitoring.googleapis.com/wombats
              --update-stackdriver-metric
                custom.cloudmonitoring.googleapis.com/wombats
              --stackdriver-metric-utilization-target 0.9999
              --stackdriver-metric-utilization-target-type delta-per-second
          """)

  def testSingleInstanceAssignment(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        test_resources.MakeAutoscalers('beta'),
        []  # Insert autoscaler.
    ])
    self.Run("""
        compute instance-groups managed set-autoscaling group-1
        --update-stackdriver-metric=foo.googleapis.com/foooooo
        --stackdriver-metric-single-instance-assignment=2
        --stackdriver-metric-filter='resource.type = "global"'
        --zone zone-1
        """)
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/seconds',
                        utilizationTarget=60.,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    ),
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='foo.googleapis.com/foooooo',
                        filter='resource.type = "global"',
                        singleInstanceAssignment=2.0
                    ),
                ],
            ),
            name='autoscaler-1',
            target=(
                '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/'
                'group-1'.format(self.compute_uri)),
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )


class InstanceGroupManagersSetAutoscalingAlphaTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = (
      test_resources.MakeInstanceGroupManagers('alpha'))
  AUTOSCALERS = test_resources.MakeAutoscalers('alpha')

  def SetUp(self):
    self.SelectApi('alpha')
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],  # Get IGM.
        self.AUTOSCALERS[1:],
        []  # Insert autoscaler.
    ])

    self.StartObjectPatch(random, 'choice').return_value = 'a'
    self.autoscalers_list_request = [
        (
            self.compute.autoscalers,
            'List', self.messages.ComputeAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                zone='zone-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get', self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]
    self.managed_instance_group_self_link = (
        '{0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1'
        .format(self.compute_uri)
    )

  def testInsertMinimalAutoscaler(self):
    self.Run('alpha compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1')
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
            ),
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Insert', request)],
    )

  def testInsertAutoscaler_Mode(self):
    self.Run('alpha compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1 --mode only-up')
    mode_cls = self.messages.AutoscalingPolicy.ModeValueValuesEnum
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[],
                maxNumReplicas=10,
                mode=mode_cls.ONLY_UP,
            ),
            name='group-1-aaaa',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Insert', request)],
    )

  def testUpdateAutoscaler_Mode(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS,
        []
    ])

    self.Run('alpha compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1 --mode only-down')

    custom_metric_utilization = (
        self.messages.AutoscalingPolicyCustomMetricUtilization(
            metric='custom.cloudmonitoring.googleapis.com/seconds',
            utilizationTarget=60.,
            utilizationTargetType=(
                self.messages.AutoscalingPolicyCustomMetricUtilization.
                UtilizationTargetTypeValueValuesEnum.
                DELTA_PER_MINUTE)))
    mode_cls = self.messages.AutoscalingPolicy.ModeValueValuesEnum
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[custom_metric_utilization],
                maxNumReplicas=10,
                mode=mode_cls.ONLY_DOWN
            ),
            name='autoscaler-1',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

  def testUpdateAutoscaler_PreservesMode(self):
    autoscalers = test_resources.MakeAutoscalers('alpha')
    autoscalers[0].autoscalingPolicy.mode = (
        autoscalers[0].autoscalingPolicy.ModeValueValuesEnum.ONLY_UP)
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],
        autoscalers,
        []
    ])

    self.Run('alpha compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1')

    custom_metric_utilization = (
        self.messages.AutoscalingPolicyCustomMetricUtilization(
            metric='custom.cloudmonitoring.googleapis.com/seconds',
            utilizationTarget=60.,
            utilizationTargetType=(
                self.messages.AutoscalingPolicyCustomMetricUtilization.
                UtilizationTargetTypeValueValuesEnum.
                DELTA_PER_MINUTE)))
    request = self.messages.ComputeAutoscalersUpdateRequest(
        autoscaler='autoscaler-1',
        autoscalerResource=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                customMetricUtilizations=[custom_metric_utilization],
                maxNumReplicas=10,
                mode=self.messages.AutoscalingPolicy.ModeValueValuesEnum.ONLY_UP
            ),
            name='autoscaler-1',
            target=self.managed_instance_group_self_link,
        ),
        project='my-project',
        zone='zone-1',
    )
    self.CheckRequests(
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Update', request)],
    )

if __name__ == '__main__':
  test_case.main()
