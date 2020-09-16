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

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class WithCdnSignedUrlApiUpdateTest(test_base.BetaUpdateTestBase):
  """Tests CDN Signed URL update flags."""

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

  def testSetValidCacheMaxAge(self):
    """Tests updating backend service with a valid cache max age."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 456789
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=456789))

  def testUpdateWithCacheMaxAgeZero(self):
    """Tests updating backend service with a cache max age of 0."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 0
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=0))

  def testUpdateWithCacheMaxAgeSeconds(self):
    """Tests updating backend service with a cache max age in seconds."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 7890s
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testUpdateWithCacheMaxAgeMinutes(self):
    """Tests updating backend service with a cache max age in minutes."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 234m
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testUpdateWithCacheMaxAgeHours(self):
    """Tests updating backend service with a cache max age in hours."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 38h
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=38 * 60 *
                                              60))

  def testUpdateWithCacheMaxAgeDays(self):
    """Tests updating backend service with a cache max age in days."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 99d
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=99 * 24 *
                                              60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests updating backend service with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --signed-url-cache-max-age: Failed to parse duration: '
        "Duration unit 'invalid-value' must be preceded by a number"):
      self.RunUpdate("""
          backend-service-1 --signed-url-cache-max-age invalid-value
          """)

  def testSetCacheMaxAgeNegative(self):
    """Tests updating backend service with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --signed-url-cache-max-age: value must be greater than or '
        'equal to 0; received: -1'):
      self.RunUpdate("""
          backend-service-1 --signed-url-cache-max-age -1
          """)


if __name__ == '__main__':
  test_case.main()
