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
"""Tests for the instance-groups managed set-autoscaling subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'alpha'


def _GetUtilizationTargetType(messages, str_form):
  return (messages.AutoscalingPolicyCustomMetricUtilization.
          UtilizationTargetTypeValueValuesEnum)(str_form)


class InstanceGroupManagersSetAutoscalingZonalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = (
      test_resources.MakeInstanceGroupManagers(API_VERSION))
  AUTOSCALERS = test_resources.MakeAutoscalers(API_VERSION)

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA
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
                customMetricUtilizations=[
                    self.messages.AutoscalingPolicyCustomMetricUtilization(
                        metric='custom.cloudmonitoring.googleapis.com/seconds',
                        utilizationTarget=60.0,
                        utilizationTargetType=_GetUtilizationTargetType(
                            self.messages, 'DELTA_PER_MINUTE'),
                    )
                ],
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
             '--queue-scaling-cloud-pub-sub topic=topic123,subscription=sub456 '
             '--queue-scaling-acceptable-backlog-per-instance 600 '
             '--queue-scaling-single-worker-throughput 0.5'
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
                queueBasedScaling=(
                    self.messages.AutoscalingPolicyQueueBasedScaling(
                        cloudPubSub=(
                            self.messages
                            .AutoscalingPolicyQueueBasedScalingCloudPubSub(
                                topic='topic123',
                                subscription='sub456')),
                        acceptableBacklogPerInstance=600,
                        singleWorkerThroughputPerSec=0.5,
                    )),
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

  def testAssertsQueueSpecPresent(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Both queue specification and queue scaling target must be provided'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--queue-scaling-acceptable-backlog-per-instance 600')

  def testAssertsQueueCloudPubSubBothTopicAndSubscriptionPresent(self):
    for param in ('topic=topic123', 'subscription=subscription123'):
      with self.AssertRaisesToolExceptionRegexp(
          r'Both topic and subscription are required'):
        self.Run('compute instance-groups managed set-autoscaling group-1 '
                 '--max-num-replicas 10 --zone zone-1 '
                 '--queue-scaling-cloud-pub-sub %s '
                 '--queue-scaling-acceptable-backlog-per-instance 600'
                 % param)

  def testInsertQueueCloudPubSubProperBareFormat(self):
    self.Run('compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1 '
             '--queue-scaling-cloud-pub-sub '
             'topic=topic123,subscription=sub456 '
             '--queue-scaling-acceptable-backlog-per-instance 600')
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                queueBasedScaling=(
                    self.messages.AutoscalingPolicyQueueBasedScaling(
                        cloudPubSub=(
                            self.messages
                            .AutoscalingPolicyQueueBasedScalingCloudPubSub(
                                topic='topic123',
                                subscription='sub456')),
                        acceptableBacklogPerInstance=600,
                    )),
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

  def testInsertQueueCloudPubSubProperLongFormat(self):
    self.Run('compute instance-groups managed set-autoscaling group-1 '
             '--max-num-replicas 10 --zone zone-1 '
             '--queue-scaling-cloud-pub-sub '
             'topic=projects/my-project/topics/topic123,'
             'subscription=projects/my-project/subscriptions/sub456 '
             '--queue-scaling-acceptable-backlog-per-instance 600')
    request = self.messages.ComputeAutoscalersInsertRequest(
        autoscaler=self.messages.Autoscaler(
            autoscalingPolicy=self.messages.AutoscalingPolicy(
                queueBasedScaling=(
                    self.messages.AutoscalingPolicyQueueBasedScaling(
                        cloudPubSub=(
                            self.messages
                            .AutoscalingPolicyQueueBasedScalingCloudPubSub(
                                topic='projects/my-project/topics/topic123',
                                subscription='projects/my-project/'
                                             'subscriptions/sub456')),
                        acceptableBacklogPerInstance=600,
                    )),
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

  def testAssertsQueueCloudPubSubProperFormat(self):
    for good_resource, bad_resource in (
        ('topic', 'subscription'),
        ('subscription', 'topic')):
      for bad_resource_value in (
          'projects/aaaa/resource_name',
          'projects/my-project/{0}s/what/resource_name'.format(bad_resource),
          'projects/my-project/{0}s/invalid-chars-&*)(I('.format(bad_resource)):
        with self.assertRaisesRegex(
            exceptions.InvalidArgumentException, r'.*'):
          self.Run('compute instance-groups managed set-autoscaling group-1 '
                   '--max-num-replicas 10 --zone zone-1 '
                   '--queue-scaling-cloud-pub-sub '
                   '{good}=good-resource-name,{bad}={bad_value} '
                   '--queue-scaling-acceptable-backlog-per-instance 600'.format(
                       good=good_resource, bad=bad_resource,
                       bad_value=bad_resource_value))

  def testAssertsQueueTargetPresent(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Both queue specification and queue scaling target must be provided'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--queue-scaling-cloud-pub-sub '
               'topic=topic123,subscription=sub456')

  def testAssertsQueueTargetAcceptableBacklogPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --queue-scaling-acceptable-backlog-per-instance: '
        r'Value must be greater than or equal to 0.0; received: -111[\d\.]*'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--queue-scaling-cloud-pub-sub '
               'topic=topic123,subscription=sub456 '
               '--queue-scaling-acceptable-backlog-per-instance -111')

  def testAssertsQueueSingleWorkerThroughputPositive(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --queue-scaling-single-worker-throughput: '
        r'Value must be greater than or equal to 0.0; received: -222[\d\.]*'):
      self.Run('compute instance-groups managed set-autoscaling group-1 '
               '--max-num-replicas 10 --zone zone-1 '
               '--queue-scaling-cloud-pub-sub '
               'topic=topic123,subscription=sub456 '
               '--queue-scaling-acceptable-backlog-per-instance 600 '
               '--queue-scaling-single-worker-throughput -222')


class InstanceGroupManagersSetAutoscalingRegionalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = test_resources.MakeInstanceGroupManagers(
      api=API_VERSION, scope_name='region-1', scope_type='region')
  AUTOSCALERS = test_resources.MakeAutoscalers(
      api=API_VERSION, scope_name='region-1', scope_type='region')

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA
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

if __name__ == '__main__':
  test_case.main()
