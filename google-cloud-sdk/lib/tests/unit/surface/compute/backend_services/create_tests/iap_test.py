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

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class WithIAPApiTest(test_base.BackendServiceCreateTestBase):

  def SetUp(self):
    self._create_service_cmd_line = (
        'compute backend-services create backend-service-1 '
        '--http-health-checks my-health-check-1 '
        '--description "My backend service" '
        '--global')
    self._lb_warning = (
        'WARNING: IAP only protects requests that go through the Cloud Load '
        'Balancer. See the IAP documentation for important security best '
        'practices: https://cloud.google.com/iap/\n')
    self._non_https_warning = (
        'WARNING: IAP has been enabled for a backend service that does not use '
        'HTTPS. Data sent from the Load Balancer to your VM will not be '
        'encrypted.\n')

  def CheckResultsWithProtocol(self, expected_message, protocol):
    messages = self.messages
    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                iap=expected_message,
                name='backend-service-1',
                portName='http',
                protocol=protocol,
                timeoutSec=30),
            project='my-project'))])

  def CheckResults(self, expected_message):
    self.CheckResultsWithProtocol(
        expected_message,
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP)

  def testWithIAPDisabled(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPEnabled(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))
    self.AssertErrEquals(self._lb_warning + self._non_https_warning)

  def testWithIAPEnabledAndNonHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))
    self.AssertErrEquals(self._lb_warning + self._non_https_warning)

  def testWithIAPEnabledAndHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled --protocol=HTTPS --port-name=http')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=True),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals(self._lb_warning)

  def testWithIAPDisabledAndNonHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPDisabledAndHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled --protocol=HTTPS --port-name=http')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=False),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals('')

  def testWithIAPEnabledWithCredentials(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENTID',
        oauth2ClientSecret='SECRET'))

  def testWithIAPEnabledWithCredentialsWithEmbeddedEquals(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENT=ID,'
        'oauth2-client-secret=SEC=RET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENT=ID',
        oauth2ClientSecret='SEC=RET'))

  def testWithIapCredentialsOnly(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap oauth2-client-id=ID,oauth2-client-secret=SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False,
        oauth2ClientId='ID',
        oauth2ClientSecret='SECRET'))

  def testInvalidIAPEmpty(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Must provide value when specifying '
        r'--iap$',
        self.Run, self._create_service_cmd_line + ' --iap=""')

  def testInvalidIapArgCombinationEnabledDisabled(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Must specify only one '
        'of \\[enabled\\] or \\[disabled\\]$',
        self.Run,
        self._create_service_cmd_line + ' --iap enabled,disabled')

  def testInvalidIapArgCombinationEnabledOnlyClientId(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID')

  def testInvalidIapArgCombinationEnabledOnlyClientSecret(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptyIdValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptySecretValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=')

  def testInvalidIapArgInvalidSubArg(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Invalid sub-argument \'invalid-arg1\'$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,invalid-arg1=VAL1,invalid-arg2=VAL2')


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
