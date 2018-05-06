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
"""Tests for the target-ssl-proxies update subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetSSLProxiesUpdateGATest(test_base.BaseTest):

  def _SetUpReleaseTrack(self, api_version, track):
    self.SelectApi(api_version)
    self.track = track

  def SetUp(self):
    self._SetUpReleaseTrack('v1', calliope_base.ReleaseTrack.GA)

  def testSimpleCase(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --ssl-certificates my-cert,my-cert2
          --backend-service my-service
          --proxy-header PROXY_V1
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests(
        [(self.compute.targetSslProxies, 'SetSslCertificates',
          messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetSslCertificatesRequest=(
                  messages.TargetSslProxiesSetSslCertificatesRequest(
                      sslCertificates=[(cert_uri + 'my-cert'),
                                       (cert_uri + 'my-cert2')])))),
         (self.compute.targetSslProxies, 'SetBackendService',
          messages.ComputeTargetSslProxiesSetBackendServiceRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetBackendServiceRequest=(
                  messages.TargetSslProxiesSetBackendServiceRequest(
                      service=(self.compute_uri + '/projects/my-project/'
                               'global/backendServices/my-service'))))),
         (self.compute.targetSslProxies, 'SetProxyHeader',
          messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetProxyHeaderRequest=(
                  self.messages.TargetSslProxiesSetProxyHeaderRequest(
                      proxyHeader=(
                          messages.TargetSslProxiesSetProxyHeaderRequest.
                          ProxyHeaderValueValuesEnum.PROXY_V1)))))])

  def testSimpleCaseCert(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --ssl-certificates my-cert
        """)

    self.CheckRequests(
        [(self.compute.targetSslProxies, 'SetSslCertificates',
          messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetSslCertificatesRequest=(
                  messages.TargetSslProxiesSetSslCertificatesRequest(
                      sslCertificates=[
                          self.compute_uri +
                          '/projects/my-project/global/sslCertificates/'
                          'my-cert'
                      ]))))])

  def testUriSupportCert(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update
          {uri}/projects/my-project/global/targetSslProxies/target-ssl-proxy-1
          --ssl-certificates
          {uri}/projects/my-project/global/sslCertificates/my-cert
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.targetSslProxies, 'SetSslCertificates',
          messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetSslCertificatesRequest=(
                  messages.TargetSslProxiesSetSslCertificatesRequest(
                      sslCertificates=[
                          self.compute_uri +
                          '/projects/my-project/global/sslCertificates/'
                          'my-cert'
                      ]))))])

  def testSimpleCaseBackendService(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --backend-service my-service
        """)

    self.CheckRequests(
        [(self.compute.targetSslProxies, 'SetBackendService',
          messages.ComputeTargetSslProxiesSetBackendServiceRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetBackendServiceRequest=(
                  messages.TargetSslProxiesSetBackendServiceRequest(
                      service=(self.compute_uri + '/projects/my-project/'
                               'global/backendServices/my-service')))))])

  def testUriSupportBackendService(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update
          {uri}/projects/my-project/global/targetSslProxies/target-ssl-proxy-1
          --backend-service
          {uri}/projects/my-project/global/backendServices/my-service
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.targetSslProxies, 'SetBackendService',
          messages.ComputeTargetSslProxiesSetBackendServiceRequest(
              project='my-project',
              targetSslProxy='target-ssl-proxy-1',
              targetSslProxiesSetBackendServiceRequest=(
                  messages.TargetSslProxiesSetBackendServiceRequest(
                      service=(self.compute_uri + '/projects/my-project/'
                               'global/backendServices/my-service')))))])

  def testSimpleCaseProxyHeaderV1(self):
    messages = self.messages

    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --proxy-header PROXY_V1
        """)

    self.CheckRequests([
        (self.compute.targetSslProxies, 'SetProxyHeader',
         messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetProxyHeaderRequest=(
                 self.messages.TargetSslProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetSslProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.PROXY_V1))))
    ])

  def testSimpleCaseProxyHeaderNone(self):
    messages = self.messages

    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --proxy-header NONE
        """)

    self.CheckRequests([
        (self.compute.targetSslProxies, 'SetProxyHeader',
         messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetProxyHeaderRequest=(
                 self.messages.TargetSslProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetSslProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.NONE))))
    ])

  def testUriSupportProxyHeader(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update
          {uri}/projects/my-project/global/targetSslProxies/target-ssl-proxy-1
          --proxy-header PROXY_V1
        """.format(uri=self.compute_uri))

    self.CheckRequests([
        (self.compute.targetSslProxies, 'SetProxyHeader',
         messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetProxyHeaderRequest=(
                 self.messages.TargetSslProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetSslProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.PROXY_V1))))
    ])

  def testSimpleCaseWithSslPolicy(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --ssl-certificates my-cert,my-cert2
          --backend-service my-service
          --proxy-header PROXY_V1
          --ssl-policy my-ssl-policy
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self.compute.targetSslProxies, 'SetSslCertificates',
         messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetSslCertificatesRequest=(
                 messages.TargetSslProxiesSetSslCertificatesRequest(
                     sslCertificates=[(cert_uri + 'my-cert'), (
                         cert_uri + 'my-cert2')])))),
        (self.compute.targetSslProxies, 'SetBackendService',
         messages.ComputeTargetSslProxiesSetBackendServiceRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetBackendServiceRequest=(
                 messages.TargetSslProxiesSetBackendServiceRequest(
                     service=(self.compute_uri + '/projects/my-project/'
                              'global/backendServices/my-service'))))),
        (self.compute.targetSslProxies, 'SetProxyHeader',
         messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             targetSslProxiesSetProxyHeaderRequest=(
                 self.messages.TargetSslProxiesSetProxyHeaderRequest(
                     proxyHeader=(
                         messages.TargetSslProxiesSetProxyHeaderRequest.
                         ProxyHeaderValueValuesEnum.PROXY_V1))))),
        (self.compute.targetSslProxies, 'SetSslPolicy',
         messages.ComputeTargetSslProxiesSetSslPolicyRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             sslPolicyReference=messages.SslPolicyReference(
                 sslPolicy=(self.compute_uri +
                            '/projects/my-project/global/sslPolicies/'
                            'my-ssl-policy')))),
    ])

  def testClearSslPolicy(self):
    messages = self.messages
    self.Run("""
        compute target-ssl-proxies update target-ssl-proxy-1
          --clear-ssl-policy
        """)
    self.CheckRequests([
        (self.compute.targetSslProxies, 'SetSslPolicy',
         messages.ComputeTargetSslProxiesSetSslPolicyRequest(
             project='my-project',
             targetSslProxy='target-ssl-proxy-1',
             sslPolicyReference=None)),
    ])

  def testWithoutArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'You must specify at least one of '
        r'\[--ssl-certificates\], \[--backend-service\], \[--proxy-header\], '
        r'\[--ssl-policy\] or \[--clear-ssl-policy].'):
      self.Run("""
          compute target-ssl-proxies update my-proxy
          """)
    self.CheckRequests()

  def testBothSetAndClearSslPolicy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --clear-ssl-policy: At most one of '
        '--clear-ssl-policy | --ssl-policy may be specified.'):
      self.Run("""
          compute target-ssl-proxies update my-proxy
          --ssl-policy my-ssl-policy
          --clear-ssl-policy
          """)
    self.CheckRequests()


class TargetSSLProxiesUpdateBetaTest(TargetSSLProxiesUpdateGATest):

  def SetUp(self):
    self._SetUpReleaseTrack('beta', calliope_base.ReleaseTrack.BETA)


class TargetSSLProxiesUpdateAlphaTest(TargetSSLProxiesUpdateBetaTest):

  def SetUp(self):
    self._SetUpReleaseTrack('alpha', calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
