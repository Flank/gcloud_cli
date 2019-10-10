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
"""Tests for the target-pools get-health subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')

HEALTH_1 = messages.TargetPoolInstanceHealth(healthStatus=[
    messages.HealthStatus(
        healthState=messages.HealthStatus.HealthStateValueValuesEnum.HEALTHY,
        ipAddress='23.251.133.75',
        instance=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/zones/zone-1/instances/instance-1'))
])

HEALTH_2 = messages.TargetPoolInstanceHealth(healthStatus=[
    messages.HealthStatus(
        healthState=messages.HealthStatus.HealthStateValueValuesEnum.UNHEALTHY,
        ipAddress='23.251.133.76',
        instance=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/zones/zone-1/instances/instance-2'))
])

OUTPUT = textwrap.dedent("""\
    ---
    healthStatus:
    - healthState: HEALTHY
      instance: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
      ipAddress: 23.251.133.75
    ---
    healthStatus:
    - healthState: UNHEALTHY
      instance: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
      ipAddress: 23.251.133.76
    """)


class TargetPoolsGetHealthTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [
            messages.TargetPool(
                name='target-pool-1',
                instances=[
                    ('https://compute.googleapis.com/compute/v1/projects/'
                     'my-project/zones/zone-1/instances/instance-1'),
                    ('https://compute.googleapis.com/compute/v1/projects/'
                     'my-project/zones/zone-1/instances/instance-2'),
                ])
        ],
        [HEALTH_1, HEALTH_2],
    ])

  def testSimpleCase(self):
    self.Run("""
        compute target-pools get-health target-pool-1
          --region region-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools, 'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
        [(self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-1')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1')),
         (self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-2')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), OUTPUT)

  def testUriSupport(self):
    self.Run("""
        compute target-pools get-health
          https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/target-pool-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools, 'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
        [(self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-1')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1')),
         (self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-2')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), OUTPUT)

  def testRegionPrompting(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='region-1'),
            messages.Region(name='region-2'),
            messages.Region(name='region-3'),
        ],
        [
            messages.TargetPool(
                name='target-pool-1',
                instances=[
                    ('https://compute.googleapis.com/compute/v1/projects/'
                     'my-project/zones/zone-1/instances/instance-1'),
                    ('https://compute.googleapis.com/compute/v1/projects/'
                     'my-project/zones/zone-1/instances/instance-2'),
                ])
        ],
        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute target-pools get-health target-pool-1
        """)

    self.CheckRequests(
        self.regions_list_request,
        [(self.compute_v1.targetPools, 'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
        [(self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-1')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1')),
         (self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-2')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
    )

    self.AssertErrContains('target-pool-1')
    self.AssertErrContains('region-1')
    self.AssertErrContains('region-2')
    self.AssertErrContains('region-3')

  def testWithNonExistentTargetPool(self):

    def MakeRequests(*_, **kwargs):
      if False:  # pylint:disable=using-constant-test
        yield
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute target-pools get-health target-pool-1
            --region region-1
          """)

    self.CheckRequests([(self.compute_v1.targetPools, 'Get',
                         messages.ComputeTargetPoolsGetRequest(
                             project='my-project',
                             region='region-1',
                             targetPool='target-pool-1'))],)
    self.assertFalse(self.GetOutput())

  def testWithGetHealthError(self):

    def MakeRequests(requests, *_, **kwargs):
      _, method, _ = requests[0]

      if method == 'Get':
        yield messages.TargetPool(
            name='target-pool-1',
            instances=[
                ('https://compute.googleapis.com/compute/v1/projects/'
                 'my-project/zones/zone-1/instances/instance-1'),
                ('https://compute.googleapis.com/compute/v1/projects/'
                 'my-project/zones/zone-1/instances/instance-2'),
            ])

      elif method == 'GetHealth':
        yield HEALTH_1
        kwargs['errors'].append((500, 'Server Error'))

      else:
        self.fail('Did not expect a call on method [{0}].'.format(method))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not get health for some targets:
         - Server Error
        """)):
      self.Run("""
          compute target-pools get-health target-pool-1
            --region region-1
          """)

    self.CheckRequests(
        [(self.compute_v1.targetPools, 'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
        [(self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-1')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1')),
         (self.compute_v1.targetPools, 'GetHealth',
          messages.ComputeTargetPoolsGetHealthRequest(
              instanceReference=messages.InstanceReference(
                  instance=(
                      'https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/zones/zone-1/instances/instance-2')),
              project='my-project',
              region='region-1',
              targetPool='target-pool-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            healthStatus:
            - healthState: HEALTHY
              instance: https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
              ipAddress: 23.251.133.75
            """))


if __name__ == '__main__':
  test_case.main()
