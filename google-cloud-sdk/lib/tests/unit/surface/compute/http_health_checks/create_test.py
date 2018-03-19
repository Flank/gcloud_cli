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
"""Tests for the http-health-checks create subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class HttpHealthChecksCreateTest(test_base.BaseTest):

  def testDefaultOptions(self):
    self.make_requests.side_effect = [[
        self.messages.HttpHealthCheck(
            name='my-health-check', host='127.0.0.1', port=80, requestPath='/')
    ]]

    self.Run("""
        compute http-health-checks create my-health-check
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

    self.AssertOutputEquals("""\
      NAME             HOST       PORT  REQUEST_PATH
      my-health-check  127.0.0.1  80    /
      """, normalize_space=True)

  def testUriSupport(self):
    self.Run("""
        compute http-health-checks create
          https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHostOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --port 8888
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=8888,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testRequestPathOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --request-path /testpath
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/testpath',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --check-interval 30s
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=30,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testTimeoutSecOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHealthyThresholdOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testUnhealthyThresholdOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testDescriptionOption(self):
    self.Run("""
        compute http-health-checks create my-health-check
           --description "Circulation, Airway, Breathing"
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Insert',
          messages.ComputeHttpHealthChecksInsertRequest(
              httpHealthCheck=messages.HttpHealthCheck(
                  name='my-health-check',
                  description='Circulation, Airway, Breathing',
                  port=80,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
