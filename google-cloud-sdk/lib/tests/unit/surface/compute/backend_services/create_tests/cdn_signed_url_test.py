# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the backend services create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class WithCdnSignedUrlApiTest(test_base.BackendServiceCreateTestBase):

  def CheckRequestMadeWithCdnPolicy(self, expected_message):
    """Verifies the request was made with the expected CDN policy."""
    messages = self.messages
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  cdnPolicy=expected_message,
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  timeoutSec=30),
              project='my-project'))])

  def testCreateWithoutCacheMaxAge(self):
    """Tests creating backend service without cache max age."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        """)
    self.CheckRequestMadeWithCdnPolicy(None)

  def testCreateWithCacheMaxAgeZero(self):
    """Tests creating backend service with cache max age of 0."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 0
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=0))

  def testCreateWithCacheMaxAgeSeconds(self):
    """Tests creating backend service with cache max age in seconds."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 7890s
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testCreateWithCacheMaxAgeMinutes(self):
    """Tests creating backend service with cache max age in minutes."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 234m
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testCreateWithCacheMaxAgeHours(self):
    """Tests creating backend service with cache max age in hours."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 38h
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=38 * 60 *
                                              60))

  def testCreateWithCacheMaxAgeDays(self):
    """Tests creating backend service with cache max age in days."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 99d
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=99 * 24 *
                                              60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests creating backend service with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        "argument --signed-url-cache-max-age: Failed to parse duration: "
        "Duration unit 'invalid-value' must be preceded by a number"):
      self.Run("""
          compute backend-services create backend-service-1
          --global
          --http-health-checks my-health-check-1
          --signed-url-cache-max-age invalid-value
          """)

  def testSetCacheMaxAgeNegative(self):
    """Tests creating backend service with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --signed-url-cache-max-age: value must be greater than or '
        'equal to 0; received: -1'):
      self.Run("""
          compute backend-services create backend-service-1
          --global
          --http-health-checks my-health-check-1
          --description "My backend service"
          --signed-url-cache-max-age -1
          """)

  def testWithCacheMaxAgeAndCacheKeyPolicy(self):
    """Tests creating backend service with both cache max age and cache keys."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 1234
        --cache-key-query-string-whitelist=foo,bar,baz
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(
            signedUrlCacheMaxAgeSec=1234,
            cacheKeyPolicy=self.messages.CacheKeyPolicy(
                includeHost=True,
                includeProtocol=True,
                includeQueryString=True,
                queryStringWhitelist=['foo', 'bar', 'baz'])))


if __name__ == '__main__':
  test_case.main()
