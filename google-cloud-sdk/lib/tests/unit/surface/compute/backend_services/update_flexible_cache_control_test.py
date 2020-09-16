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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute.backend_services import test_resources
from tests.lib.surface.compute.backend_services.update import test_base


class WithFlexibleCacheControlApiBetaUpdateTest(test_base.CommonUpdateTestBase):
  """Tests CDN Flexible Cache Control update flags."""

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.make_requests.side_effect = iter([
        [test_resources.BACKEND_SERVICES_WITH_DEFAULT_CDN_POLICY_BETA],
        [],
    ])

  def testSetAllProperties(self):
    self.RunUpdate("""
          backend-service-1 --cache-mode CACHE_ALL_STATIC --negative-caching
          --client-ttl 4000 --default-ttl 5000 --max-ttl 6000
          --negative-caching-policy='404=1000,301=1200'
          --custom-response-header 'Test-Header: value'
          --custom-response-header 'Test-Header2: {cdn_cache_id}'
          """)
    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.CACHE_ALL_STATIC,
            clientTtl=4000,
            defaultTtl=5000,
            maxTtl=6000,
            negativeCaching=True,
            negativeCachingPolicy=[
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=404, ttl=1000),
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=301, ttl=1200),
            ]),
        ['Test-Header: value', 'Test-Header2: {cdn_cache_id}'],
    )

  def testUpdateCacheModeToUseOriginHeaders(self):
    self.RunUpdate("""
          backend-service-1 --cache-mode USE_ORIGIN_HEADERS
          """)
    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.USE_ORIGIN_HEADERS,
            clientTtl=None,
            defaultTtl=None,
            maxTtl=None,
            negativeCaching=True,
            negativeCachingPolicy=[
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=404, ttl=3000),
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=301, ttl=3500),
            ]),
        ['Header: Value', 'Header2: {cdn_cache_id}'],
    )

  def testUpdateCacheModeToUseOriginHeadersWithTtls(self):
    """Verify invalid ttl values are passed if user specified them explicitly."""
    self.RunUpdate("""
          backend-service-1 --cache-mode USE_ORIGIN_HEADERS
          --client-ttl 4000 --default-ttl 5000 --max-ttl 6000
          """)
    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.USE_ORIGIN_HEADERS,
            clientTtl=4000,
            defaultTtl=5000,
            maxTtl=6000,
            negativeCaching=True,
            negativeCachingPolicy=[
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=404, ttl=3000),
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=301, ttl=3500),
            ]),
        ['Header: Value', 'Header2: {cdn_cache_id}'],
    )

  def testUpdateCacheModeToForceCacheAll(self):
    self.RunUpdate("""
          backend-service-1 --cache-mode FORCE_CACHE_ALL
          """)
    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.FORCE_CACHE_ALL,
            clientTtl=4000,
            defaultTtl=5000,
            maxTtl=None,
            negativeCaching=True,
            negativeCachingPolicy=[
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=404, ttl=3000),
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=301, ttl=3500),
            ]),
        ['Header: Value', 'Header2: {cdn_cache_id}'],
    )

  def testClearProperties(self):
    self.RunUpdate("""
          backend-service-1 --no-negative-caching --no-custom-response-headers
          --no-client-ttl --no-max-ttl --no-default-ttl --no-negative-caching-policies
          """)

    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.CACHE_ALL_STATIC,
            negativeCaching=False,
            negativeCachingPolicy=[]),
        [],
    )

  def testDisableNegativeCaching(self):
    self.RunUpdate("""
          backend-service-1 --no-negative-caching
          """)

    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.CACHE_ALL_STATIC,
            clientTtl=4000,
            defaultTtl=5000,
            maxTtl=6000,
            negativeCaching=False,
            negativeCachingPolicy=[]),
        ['Header: Value', 'Header2: {cdn_cache_id}'],
    )

  def testDisableCdn(self):
    self.RunUpdate("""
          backend-service-1 --no-enable-cdn
          """)

    self.CheckRequestMadeWithCdnPolicyAndCustomResponseHeaders(
        self.messages.BackendServiceCdnPolicy(
            cacheMode=self.messages.BackendServiceCdnPolicy
            .CacheModeValueValuesEnum.CACHE_ALL_STATIC,
            clientTtl=4000,
            defaultTtl=5000,
            maxTtl=6000,
            negativeCaching=True,
            negativeCachingPolicy=[
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=404, ttl=3000),
                self.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
                    code=301, ttl=3500),
            ]), ['Header: Value', 'Header2: {cdn_cache_id}'],
        enable_cdn=False)


class WithFlexibleCacheControlApiAlphaUpdateTest(
    WithFlexibleCacheControlApiBetaUpdateTest):
  """Tests CDN Flexible Cache Control update flags."""

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.make_requests.side_effect = iter([
        [test_resources.BACKEND_SERVICES_WITH_DEFAULT_CDN_POLICY_ALPHA],
        [],
    ])


if __name__ == '__main__':
  test_case.main()
