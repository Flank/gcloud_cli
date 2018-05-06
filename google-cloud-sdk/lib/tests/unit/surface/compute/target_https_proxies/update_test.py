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
"""Tests for the target-https-proxies update subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHTTPSProxiesUpdateGATest(test_base.BaseTest):

  def _SetUpReleaseTrack(self, api_version, track):
    self.SelectApi(api_version)
    self.track = track

  def SetUp(self):
    self._SetUpReleaseTrack('v1', calliope_base.ReleaseTrack.GA)

  def testSimpleCase(self):
    messages = self.messages
    self.Run("""
        compute target-https-proxies update target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests(
        [(self.compute.targetHttpsProxies, 'SetSslCertificates',
          messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              targetHttpsProxiesSetSslCertificatesRequest=(
                  messages.TargetHttpsProxiesSetSslCertificatesRequest(
                      sslCertificates=[(cert_uri + 'my-cert'),
                                       (cert_uri + 'my-cert2')])))),
         (self.compute.targetHttpsProxies, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testSimpleCaseMap(self):
    messages = self.messages
    self.Run("""
        compute target-https-proxies update target-https-proxy-1
          --url-map my-map
        """)

    self.CheckRequests(
        [(self.compute.targetHttpsProxies, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testSimpleCaseCert(self):
    messages = self.messages
    self.Run("""
        compute target-https-proxies update target-https-proxy-1
          --ssl-certificates my-cert
        """)

    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'SetSslCertificates',
         messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetSslCertificatesRequest=(
                 messages.TargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[
                         self.compute_uri +
                         '/projects/my-project/global/sslCertificates/'
                         'my-cert'
                     ])))),
    ])

  def testSimpleCaseWithSslPolicy(self):
    messages = self.messages

    self.Run("""
        compute target-https-proxies update target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --ssl-policy my-ssl-policy
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'SetSslCertificates',
         messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetSslCertificatesRequest=(
                 messages.TargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[(cert_uri + 'my-cert'), (
                         cert_uri + 'my-cert2')])))),
        (self.compute.targetHttpsProxies, 'SetUrlMap',
         messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             urlMapReference=messages.UrlMapReference(
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map')))),
        (self.compute.targetHttpsProxies, 'SetSslPolicy',
         messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=messages.SslPolicyReference(
                 sslPolicy=(self.compute_uri +
                            '/projects/my-project/global/sslPolicies/'
                            'my-ssl-policy')))),
    ])

  def testUriSupport(self):
    messages = self.messages
    self.Run("""
        compute target-https-proxies update
          {uri}/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
          --ssl-certificates {uri}/projects/my-project/global/sslCertificates/my-cert
          --url-map {uri}/projects/my-project/global/urlMaps/my-map
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.targetHttpsProxies, 'SetSslCertificates',
          messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              targetHttpsProxiesSetSslCertificatesRequest=(
                  messages.TargetHttpsProxiesSetSslCertificatesRequest(
                      sslCertificates=[
                          self.compute_uri +
                          '/projects/my-project/global/sslCertificates/'
                          'my-cert'
                      ])))),
         (self.compute.targetHttpsProxies, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testWithoutArgs(self):
    with self.AssertRaisesToolExceptionMatches(
        'You must specify at least one of [--ssl-certificates], [--url-map], '
        '[--ssl-policy] or [--clear-ssl-policy].'
    ):
      self.Run("""
          compute target-https-proxies update my-proxy
          """)
    self.CheckRequests()


class TargetHTTPSProxiesUpdateBetaTest(TargetHTTPSProxiesUpdateGATest):

  def SetUp(self):
    self._SetUpReleaseTrack('beta', calliope_base.ReleaseTrack.BETA)

  def testSimpleCaseWithQuicOverrideAndSslPolicy(self):
    messages = self.messages
    quic_enum = (
        messages.TargetHttpsProxiesSetQuicOverrideRequest.
        QuicOverrideValueValuesEnum)

    self.Run("""
        compute target-https-proxies update target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --quic-override DISABLE
          --ssl-policy my-ssl-policy
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'SetSslCertificates',
         messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetSslCertificatesRequest=(
                 messages.TargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[(cert_uri + 'my-cert'), (
                         cert_uri + 'my-cert2')])))),
        (self.compute.targetHttpsProxies, 'SetUrlMap',
         messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             urlMapReference=messages.UrlMapReference(
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map')))),
        (self.compute.targetHttpsProxies, 'SetQuicOverride',
         messages.ComputeTargetHttpsProxiesSetQuicOverrideRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetQuicOverrideRequest=(
                 messages.TargetHttpsProxiesSetQuicOverrideRequest(
                     quicOverride=quic_enum.DISABLE)))),
        (self.compute.targetHttpsProxies, 'SetSslPolicy',
         messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=messages.SslPolicyReference(
                 sslPolicy=(self.compute_uri +
                            '/projects/my-project/global/sslPolicies/'
                            'my-ssl-policy')))),
    ])

  def testClearSslPolicy(self):
    messages = self.messages
    self.Run("""
        compute target-https-proxies update target-https-proxy-1
        --clear-ssl-policy
        """)
    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'SetSslPolicy',
         messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=None)),
    ])

  def testWithoutArgs(self):
    with self.AssertRaisesToolExceptionMatches(
        'You must specify at least one of [--ssl-certificates], [--url-map], '
        '[--quic-override], [--ssl-policy] or [--clear-ssl-policy].'):
      self.Run("""
          compute target-https-proxies update my-proxy
          """)
    self.CheckRequests()

  def testBothSetAndClearSslPolicy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --clear-ssl-policy: At most one of '
        '--clear-ssl-policy | --ssl-policy may be specified.'):
      self.Run("""
          compute target-https-proxies update my-proxy
          --ssl-policy my-ssl-policy
          --clear-ssl-policy
          """)
    self.CheckRequests()


class TargetHTTPSProxiesUpdateAlphaTest(TargetHTTPSProxiesUpdateBetaTest):

  def SetUp(self):
    self._SetUpReleaseTrack('alpha', calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
