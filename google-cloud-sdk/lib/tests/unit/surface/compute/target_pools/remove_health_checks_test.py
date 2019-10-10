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
"""Tests for the target-pools remove-health-check subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetPoolsRemoveHealthChecksTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute target-pools remove-health-checks my-pool
          --region us-central2
          --http-health-check my-health-check
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'RemoveHealthCheck',
          messages.ComputeTargetPoolsRemoveHealthCheckRequest(
              region='us-central2',
              project='my-project',
              targetPool='my-pool',
              targetPoolsRemoveHealthCheckRequest=(
                  messages.TargetPoolsRemoveHealthCheckRequest(
                      healthChecks=[messages.HealthCheckReference(
                          healthCheck=('https://compute.googleapis.com/compute/v1/'
                                       'projects/my-project/global/'
                                       'httpHealthChecks/my-health-check')
                          )]))))],
    )

  def testUriSupport(self):
    self.Run("""
        compute target-pools remove-health-checks
          https://compute.googleapis.com/compute/v1/projects/my-project/regions/us-central2/targetPools/my-pool
          --http-health-check https://compute.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'RemoveHealthCheck',
          messages.ComputeTargetPoolsRemoveHealthCheckRequest(
              region='us-central2',
              project='my-project',
              targetPool='my-pool',
              targetPoolsRemoveHealthCheckRequest=(
                  messages.TargetPoolsRemoveHealthCheckRequest(
                      healthChecks=[messages.HealthCheckReference(
                          healthCheck=('https://compute.googleapis.com/compute/v1/'
                                       'projects/my-project/global/'
                                       'httpHealthChecks/my-health-check')
                          )]))))],
    )

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='us-central1'),
            messages.Region(name='us-central2'),
        ],

        [],
    ])
    self.WriteInput('2\n')

    self.Run("""
        compute target-pools remove-health-checks my-pool
          --http-health-check my-health-check
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.targetPools,
          'RemoveHealthCheck',
          messages.ComputeTargetPoolsRemoveHealthCheckRequest(
              region='us-central2',
              project='my-project',
              targetPool='my-pool',
              targetPoolsRemoveHealthCheckRequest=(
                  messages.TargetPoolsRemoveHealthCheckRequest(
                      healthChecks=[messages.HealthCheckReference(
                          healthCheck=('https://compute.googleapis.com/compute/v1/'
                                       'projects/my-project/global/'
                                       'httpHealthChecks/my-health-check')
                          )]))))],
    )

    self.AssertErrContains('my-pool')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')


if __name__ == '__main__':
  test_case.main()
