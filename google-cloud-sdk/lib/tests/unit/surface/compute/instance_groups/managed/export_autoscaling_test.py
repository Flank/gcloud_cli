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
import json
import os

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstanceGroupManagersExportAutoscalingTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def _GetAutoscalingFilePath(self):
    output_dir = self.CreateTempDir()
    return output_dir + os.sep + 'autoscaling_file.json'

  def testExportZonalNoneAutoscaler(self):
    autoscaling_file = self._GetAutoscalingFilePath()
    self.Run('compute instance-groups managed export-autoscaling group-1 '
             '--zone zone-1 --autoscaling-file=' + autoscaling_file)
    exported_autoscaler = json.load(open(autoscaling_file))
    self.assertIsNone(exported_autoscaler)

  def testExportregionalNoneAutoscaler(self):
    autoscaling_file = self._GetAutoscalingFilePath()
    self.Run('compute instance-groups managed export-autoscaling group-1 '
             '--region region-1 --autoscaling-file=' + autoscaling_file)
    exported_autoscaler = json.load(open(autoscaling_file))
    self.assertIsNone(exported_autoscaler)

  def _GefFullAutoscalingPolicy(self):
    return self.messages.AutoscalingPolicy(
        coolDownPeriodSec=60,
        cpuUtilization=self.messages.AutoscalingPolicyCpuUtilization(
            utilizationTarget=0.8,
        ),
        customMetricUtilizations=[
            self.messages.AutoscalingPolicyCustomMetricUtilization(
                metric='custom.cloudmonitoring.googleapis.com/seconds',
                utilizationTarget=60.,
                utilizationTargetType=(
                    self.messages.
                    AutoscalingPolicyCustomMetricUtilization.
                    UtilizationTargetTypeValueValuesEnum.
                    DELTA_PER_MINUTE),
            ),
        ],
        loadBalancingUtilization=(
            self.messages.AutoscalingPolicyLoadBalancingUtilization)(
                utilizationTarget=0.9,
            ),
        maxNumReplicas=10,
        minNumReplicas=2,
    )

  def _GetFullAutoscaler(self, zone=None, region=None):
    status_type = (
        self.messages.AutoscalerStatusDetails.TypeValueValuesEnum.UNKNOWN)
    status = self.messages.Autoscaler.StatusValueValuesEnum.ACTIVE
    my_project = 'my-project'
    result = self.messages.Autoscaler(
        kind='compute#autoscaler',
        id=1234567890,
        creationTimestamp='Sunny tuesday afternoon',
        name='Alice',
        description='sending encrypted messages',
        region='{}/projects/{}/regions/{}'.format(
            self.compute_uri, my_project, 'region-1'),
        status=status,
        statusDetails=[
            self.messages.AutoscalerStatusDetails(
                message='Somehing, something',
                type=status_type,
            )
        ],
        autoscalingPolicy=self._GefFullAutoscalingPolicy(),
    )
    if zone:
      result.zone = '{}/projects/{}/zones/{}'.format(
          self.compute_uri, my_project, zone)
      result.target = '{}/projects/{}/zones/{}/instanceGroupManagers/{}'.format(
          self.compute_uri, my_project, zone, 'group-1')
      result.selfLink = '{}/projects/{}/zones/{}/autoscalers/{}'.format(
          self.compute_uri, my_project, zone, 'autoscaler-1')
    if region:
      result.region = '{}/projects/{}/region/{}'.format(
          self.compute_uri, my_project, region)
      result.target = (
          '{}/projects/{}/regions/{}/instanceGroupManagers/{}'.format(
              self.compute_uri, my_project, region, 'group-1'))
      result.selfLink = '{}/projects/{}/regions/{}/autoscalers/{}'.format(
          self.compute_uri, my_project, region, 'autoscaler-1')
    return result

  def _GetStrippedAutoscaler(self):
    return {
        'autoscalingPolicy': {
            'minNumReplicas': 2,
            'customMetricUtilizations': [
                {
                    'utilizationTarget': 60.0,
                    'metric': 'custom.cloudmonitoring.googleapis.com/seconds',
                    'utilizationTargetType': 'DELTA_PER_MINUTE'
                },
            ],
            'coolDownPeriodSec': 60,
            'loadBalancingUtilization': {
                'utilizationTarget': 0.9,
            },
            'cpuUtilization': {
                'utilizationTarget': 0.8,
            },
            'maxNumReplicas': 10,
        },
        'description': 'sending encrypted messages',
    }

  def testExportZonalAllAutoscaler(self):
    self.make_requests.side_effect = iter([
        [self._GetFullAutoscaler(zone='zone-1')],
    ])
    autoscaling_file = self._GetAutoscalingFilePath()
    self.Run('compute instance-groups managed export-autoscaling group-1 '
             '--zone zone-1 --autoscaling-file=' + autoscaling_file)
    exported_autoscaler = json.load(open(autoscaling_file))
    self.assertEqual(self._GetStrippedAutoscaler(), exported_autoscaler)
    autoscalers_list_request = [
        (
            self.compute.autoscalers,
            'List', self.messages.ComputeAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                zone='zone-1',
            ),
        ),
    ]
    self.CheckRequests(
        autoscalers_list_request,
    )

  def testExportRegionalAllAutoscaler(self):
    self.make_requests.side_effect = iter([
        [self._GetFullAutoscaler(region='region-1')],
    ])
    autoscaling_file = self._GetAutoscalingFilePath()
    self.Run('compute instance-groups managed export-autoscaling group-1 '
             '--region region-1 --autoscaling-file=' + autoscaling_file)
    exported_autoscaler = json.load(open(autoscaling_file))
    self.assertEqual(self._GetStrippedAutoscaler(), exported_autoscaler)
    autoscalers_list_request = [
        (
            self.compute.regionAutoscalers,
            'List', self.messages.ComputeRegionAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                region='region-1',
            ),
        ),
    ]
    self.CheckRequests(
        autoscalers_list_request,
    )

if __name__ == '__main__':
  test_case.main()
