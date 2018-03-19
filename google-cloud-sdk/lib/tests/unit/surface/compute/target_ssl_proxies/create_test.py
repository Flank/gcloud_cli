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
"""Tests for the target-ssl-proxies create subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetSSLProxiesCreateGATest(test_base.BaseTest):

  def _SetUpReleaseTrack(self, api_version, track):
    self.SelectApi(api_version)
    self.track = track

  def SetUp(self):
    self._SetUpReleaseTrack('v1', calliope_base.ReleaseTrack.GA)

  def testSimpleCaseProxyV1Header(self):
    messages = self.messages
    proxy_header_enum = messages.TargetSslProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetSslProxy(
            name='my-proxy',
            description='My target SSL proxy',
        )],
    ])

    result = list(
        self.Run("""
        compute target-ssl-proxies create my-proxy
          --description "My target SSL proxy"
          --ssl-certificates my-cert
          --backend-service my-service
          --proxy-header PROXY_V1
          --format=disable
        """))

    self.assertEqual(result[0].name, 'my-proxy')
    self.AssertOutputEquals('')
    self.CheckRequests(
        [(self.compute.targetSslProxies,
          'Insert',
          messages.ComputeTargetSslProxiesInsertRequest(
              project='my-project',
              targetSslProxy=messages.TargetSslProxy(
                  description='My target SSL proxy',
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.PROXY_V1,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'),
                  sslCertificates=[(self.compute_uri +
                                    '/projects/my-project/global/'
                                    'sslCertificates/my-cert')])))],
    )

  def testSimpleCaseNoneHeader(self):
    messages = self.messages
    proxy_header_enum = messages.TargetSslProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetSslProxy(
            name='my-proxy',
            description='My target SSL proxy',
        )],
    ])

    result = list(
        self.Run("""
        compute target-ssl-proxies create my-proxy
          --description "My target SSL proxy"
          --ssl-certificates my-cert
          --backend-service my-service
          --proxy-header NONE
          --format=disable
        """))

    self.assertEqual(result[0].name, 'my-proxy')

    self.CheckRequests(
        [(self.compute.targetSslProxies,
          'Insert',
          messages.ComputeTargetSslProxiesInsertRequest(
              project='my-project',
              targetSslProxy=messages.TargetSslProxy(
                  description='My target SSL proxy',
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.NONE,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'),
                  sslCertificates=[(self.compute_uri +
                                    '/projects/my-project/global/'
                                    'sslCertificates/my-cert')])))],
    )

  def testUriSupport(self):
    messages = self.messages
    proxy_header_enum = messages.TargetSslProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetSslProxy(
            name='my-proxy',
            description='My target SSL proxy',
        )],
    ])

    result = list(
        self.Run("""
        compute target-ssl-proxies create
          {uri}/projects/my-project/global/targetSslProxies/my-proxy
          --ssl-certificates {uri}/projects/my-project/global/sslCertificates/my-cert
          --backend-service {uri}/projects/my-project/global/backendServices/my-service
          --format=disable
        """.format(uri=self.compute_uri)))

    self.assertEqual(result[0].name, 'my-proxy')

    self.CheckRequests(
        [(self.compute.targetSslProxies,
          'Insert',
          messages.ComputeTargetSslProxiesInsertRequest(
              project='my-project',
              targetSslProxy=messages.TargetSslProxy(
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.NONE,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'),
                  sslCertificates=[(self.compute_uri +
                                    '/projects/my-project/global/'
                                    'sslCertificates/my-cert')])))],
    )

  def testWithoutSSLCertificate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --ssl-certificates: Must be specified.'):
      self.Run("""
          compute target-ssl-proxies create my-proxy
            --backend-service my-service
          """)

    self.CheckRequests()

  def testWithoutBackendService(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --backend-service: Must be specified.'):
      self.Run("""
          compute target-ssl-proxies create my-proxy
            --ssl-certificates my-cert
          """)

    self.CheckRequests()


class TargetSSLProxiesCreateBetaTest(TargetSSLProxiesCreateGATest):

  def SetUp(self):
    self._SetUpReleaseTrack('beta', calliope_base.ReleaseTrack.BETA)

  def testSimpleCaseSslPolicy(self):
    messages = self.messages
    proxy_header_enum = messages.TargetSslProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [
            messages.TargetSslProxy(
                name='my-proxy',
                sslCertificates=['my-cert', 'my-cert2'],
                service='my-service',
                sslPolicy='my-ssl-policy',
            )
        ],
    ])

    result = self.Run("""
        compute target-ssl-proxies create my-proxy
          --ssl-certificates my-cert,my-cert2
          --backend-service my-service
          --ssl-policy my-ssl-policy
          --format=disable
        """)

    target_ssl_proxy = list(result)[0]
    self.assertEqual(target_ssl_proxy.name, 'my-proxy')
    self.assertEqual(target_ssl_proxy.sslCertificates, ['my-cert', 'my-cert2'])
    self.assertEqual(target_ssl_proxy.service, 'my-service')
    self.assertEqual(target_ssl_proxy.sslPolicy, 'my-ssl-policy')

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests(
        [(self.compute.targetSslProxies, 'Insert',
          messages.ComputeTargetSslProxiesInsertRequest(
              project='my-project',
              targetSslProxy=messages.TargetSslProxy(
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.NONE,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'),
                  sslCertificates=[(cert_uri + 'my-cert'),
                                   (cert_uri + 'my-cert2')],
                  sslPolicy=self.compute_uri + '/projects/my-project/global/'
                  'sslPolicies/my-ssl-policy')))],)


class TargetSSLProxiesCreateAlphaTest(TargetSSLProxiesCreateBetaTest):

  def SetUp(self):
    self._SetUpReleaseTrack('alpha', calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
