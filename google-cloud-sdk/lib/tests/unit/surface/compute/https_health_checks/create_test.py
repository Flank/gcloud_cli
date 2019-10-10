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
"""Tests for the https-health-checks create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HttpsHealthChecksCreateTest(test_base.BaseTest):

  def testDefaultOptions(self):
    messages = self.messages
    self.make_requests.side_effect = [[
        messages.HttpsHealthCheck(
            name='my-health-check', host='host', port=443, requestPath='/')
    ]]

    self.Run("""
        compute https-health-checks create my-health-check
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

    self.AssertOutputEquals("""\
      NAME             HOST  PORT  REQUEST_PATH
      my-health-check  host  443   /
      """, normalize_space=True)

  def testUriSupport(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create
             {0}/projects/my-project/global/httpsHealthChecks/my-health-check
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHostOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testPortOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --port 8888
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
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
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --request-path /testpath
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/testpath',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --check-interval 30s
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=30,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testTimeoutSecOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testHealthyThresholdOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],
    )

  def testUnhealthyThresholdOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testDescriptionOption(self):
    messages = self.messages
    self.Run("""
        compute https-health-checks create my-health-check
          --description "Circulation, Airway, Breathing"
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Insert',
          messages.ComputeHttpsHealthChecksInsertRequest(
              httpsHealthCheck=messages.HttpsHealthCheck(
                  name='my-health-check',
                  description='Circulation, Airway, Breathing',
                  port=443,
                  requestPath='/',
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
