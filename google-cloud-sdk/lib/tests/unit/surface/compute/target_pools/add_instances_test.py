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
"""Tests for the target-pools add-instance subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetPoolsAddInstanceTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute target-pools add-instances my-pool
          --instances-zone us-central2-a
          --instances my-instance
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'AddInstance',
          messages.ComputeTargetPoolsAddInstanceRequest(
              region='us-central2',
              project='my-project',
              targetPool='my-pool',
              targetPoolsAddInstanceRequest=(
                  messages.TargetPoolsAddInstanceRequest(
                      instances=[messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/v1/'
                                    'projects/my-project/zones/us-central2-a/'
                                    'instances/my-instance'))]))))],
    )

  def testMultipleInstances(self):
    self.Run("""
        compute target-pools add-instances my-pool
          --zone us-central2-a
          --instances instance-1,instance-2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'AddInstance',
          messages.ComputeTargetPoolsAddInstanceRequest(
              region='us-central2',
              project='my-project',
              targetPool='my-pool',
              targetPoolsAddInstanceRequest=(
                  messages.TargetPoolsAddInstanceRequest(
                      instances=[
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central2-a/instances/instance-1')),
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central2-a/instances/instance-2')),
                      ]))))],
    )

  def testUriSupport(self):
    # Note that we pass in two instances from different zones (but not
    # different regions) here.
    self.Run("""
        compute target-pools add-instances
          https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/targetPools/my-pool
          --instances
              https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance-1,https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-b/instances/my-instance-2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'AddInstance',
          messages.ComputeTargetPoolsAddInstanceRequest(
              region='us-central1',
              project='my-project',
              targetPool='my-pool',
              targetPoolsAddInstanceRequest=(
                  messages.TargetPoolsAddInstanceRequest(
                      instances=[
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central1-a/instances/'
                                        'my-instance-1')),
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central1-b/instances/my-instance-2')
                          )]))))],
    )

  def testInstancesFromDifferentRegions(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Instances must all be in the same region as the target pool.'):
      self.Run("""
          compute target-pools add-instances
            https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/targetPools/my-pool
            --instances
                https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance-1,https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central2-a/instances/my-instance-2
        """)

    self.CheckRequests()

  def testRegionDifferentFromInstancesRegion(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Instances must all be in the same region as the target pool.'):
      self.Run("""
          compute target-pools add-instances
            https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/targetPools/my-pool
            --region us-central2
            --instances
                https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance-1
        """)

    self.CheckRequests()

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Zone(name='us-central1-a'),
            messages.Zone(name='us-central1-b'),
            messages.Zone(name='us-central2-a'),
        ],

        [],
    ])

    self.WriteInput('1\n')

    self.Run("""
        compute target-pools add-instances my-pool
          --instances my-instance-1,my-instance-2
        """)

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute_v1.targetPools,
          'AddInstance',
          messages.ComputeTargetPoolsAddInstanceRequest(
              region='us-central1',
              project='my-project',
              targetPool='my-pool',
              targetPoolsAddInstanceRequest=(
                  messages.TargetPoolsAddInstanceRequest(
                      instances=[
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central1-a/instances/'
                                        'my-instance-1')),
                          messages.InstanceReference(
                              instance=('https://www.googleapis.com/compute/v1/'
                                        'projects/my-project/zones/'
                                        'us-central1-a/instances/my-instance-2')
                          )]))))],
    )

    self.AssertErrContains('my-instance-1')
    self.AssertErrContains('my-instance-2')
    self.AssertErrContains('us-central1-a')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('us-central2-a')


if __name__ == '__main__':
  test_case.main()
