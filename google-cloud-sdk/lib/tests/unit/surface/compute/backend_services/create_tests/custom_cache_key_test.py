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

from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class WithCustomCacheKeyApiTest(test_base.BackendServiceCreateTestBase):

  # When no custom cache keys flags are specified, no custom cache key flags
  # should appear in the request.
  def testDefault(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],)

  def testCacheKeyExcludeHost(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-host
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=True,
                          includeQueryString=True))),
              project='my-project'))],)

  def testCacheKeyExcludeProtocol(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-protocol
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=False,
                          includeQueryString=True))),
              project='my-project'))],)

  def testCacheKeyExcludeQueryString(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-query-string
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=False))),
              project='my-project'))],)

  def testCacheKeyQueryStringWhitelist(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --cache-key-query-string-whitelist=contentid,language
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringWhitelist=['contentid', 'language']))),
              project='my-project'))],)

  def testCacheKeyQueryStringBlacklist(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --cache-key-query-string-blacklist=campaign
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringBlacklist=['campaign']))),
              project='my-project'))],)

  def testEnableWhitelistWithExcludeQueryString(self):
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.Run("""compute backend-services create my-backend-service
                  --health-checks my-health-check
                  --no-cache-key-include-query-string
                  --cache-key-query-string-whitelist=contentid,language
                  --global""")
    self.CheckRequests()

  def testEnableBlacklistWithExcludeQueryString(self):
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.Run("""
          compute backend-services create my-backend-service
          --health-checks my-health-check
          --no-cache-key-include-query-string
          --cache-key-query-string-blacklist=campaignid
          --global
          """)
    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
