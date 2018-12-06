# -*- coding: utf-8 -*- #
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
from __future__ import division
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
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunUpdate(self, command):
    self.Run('compute target-https-proxies update ' + command)

  def testSimpleCase(self):
    messages = self.messages
    self.RunUpdate("""
          target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests(
        [(self._target_https_proxies_api, 'SetSslCertificates',
          messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              targetHttpsProxiesSetSslCertificatesRequest=(
                  messages.TargetHttpsProxiesSetSslCertificatesRequest(
                      sslCertificates=[(cert_uri + 'my-cert'), (
                          cert_uri + 'my-cert2')])))),
         (self._target_https_proxies_api, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testSimpleCaseMap(self):
    messages = self.messages
    self.RunUpdate("""
          target-https-proxy-1
          --url-map my-map
        """)

    self.CheckRequests(
        [(self._target_https_proxies_api, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testSimpleCaseCert(self):
    messages = self.messages
    self.RunUpdate("""
          target-https-proxy-1
          --ssl-certificates my-cert
        """)

    self.CheckRequests([
        (self._target_https_proxies_api, 'SetSslCertificates',
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

    self.RunUpdate("""
        target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --ssl-policy my-ssl-policy
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self._target_https_proxies_api, 'SetSslCertificates',
         messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetSslCertificatesRequest=(
                 messages.TargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[(cert_uri + 'my-cert'), (
                         cert_uri + 'my-cert2')])))),
        (self._target_https_proxies_api, 'SetUrlMap',
         messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             urlMapReference=messages.UrlMapReference(
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map')))),
        (self._target_https_proxies_api, 'SetSslPolicy',
         messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=messages.SslPolicyReference(
                 sslPolicy=(self.compute_uri +
                            '/projects/my-project/global/sslPolicies/'
                            'my-ssl-policy')))),
    ])

  def testSimpleCaseWithQuicOverrideAndSslPolicy(self):
    messages = self.messages
    quic_enum = (
        messages.TargetHttpsProxiesSetQuicOverrideRequest.
        QuicOverrideValueValuesEnum)

    self.RunUpdate("""
        target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --quic-override DISABLE
          --ssl-policy my-ssl-policy
        """)

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self._target_https_proxies_api, 'SetSslCertificates',
         messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetSslCertificatesRequest=(
                 messages.TargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[(cert_uri + 'my-cert'), (
                         cert_uri + 'my-cert2')])))),
        (self._target_https_proxies_api, 'SetUrlMap',
         messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             urlMapReference=messages.UrlMapReference(
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map')))),
        (self._target_https_proxies_api, 'SetQuicOverride',
         messages.ComputeTargetHttpsProxiesSetQuicOverrideRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetQuicOverrideRequest=(
                 messages.TargetHttpsProxiesSetQuicOverrideRequest(
                     quicOverride=quic_enum.DISABLE)))),
        (self._target_https_proxies_api, 'SetSslPolicy',
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
    self.RunUpdate("""
          {uri}/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
          --ssl-certificates {uri}/projects/my-project/global/sslCertificates/my-cert
          --url-map {uri}/projects/my-project/global/urlMaps/my-map
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self._target_https_proxies_api, 'SetSslCertificates',
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
         (self._target_https_proxies_api, 'SetUrlMap',
          messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpsProxy='target-https-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))])

  def testClearSslPolicy(self):
    messages = self.messages
    self.RunUpdate("""
        target-https-proxy-1
        --clear-ssl-policy
        """)
    self.CheckRequests([
        (self._target_https_proxies_api, 'SetSslPolicy',
         messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=None)),
    ])

  def testBothSetAndClearSslPolicy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --clear-ssl-policy: At most one of '
        '--clear-ssl-policy | --ssl-policy may be specified.'):
      self.RunUpdate("""
          my-proxy
          --ssl-policy my-ssl-policy
          --clear-ssl-policy
          """)
    self.CheckRequests()

  def testWithoutArgs(self):
    with self.AssertRaisesToolExceptionMatches(
        'You must specify at least one of [--ssl-certificates], [--url-map], '
        '[--quic-override], [--ssl-policy] or [--clear-ssl-policy].'):
      self.RunUpdate("""
          my-proxy
          """)
    self.CheckRequests()


class TargetHTTPSProxiesUpdateBetaTest(TargetHTTPSProxiesUpdateGATest):

  def SetUp(self):
    self._SetUpReleaseTrack('beta', calliope_base.ReleaseTrack.BETA)
    self._target_https_proxies_api = self.compute.targetHttpsProxies


class TargetHTTPSProxiesUpdateAlphaTest(TargetHTTPSProxiesUpdateBetaTest):

  def SetUp(self):
    self._SetUpReleaseTrack('alpha', calliope_base.ReleaseTrack.ALPHA)
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunUpdate(self, command):
    self.Run('compute target-https-proxies update --global ' + command)


class RegionTargetHTTPSProxiesUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.regionTargetHttpsProxies

  def RunUpdate(self, command):
    self.Run('alpha compute target-https-proxies update --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.RunUpdate("""
                target-https-proxy-1
                --ssl-certificates my-cert,my-cert2
                --url-map my-map
                """)

    self.CheckRequests([(
        self._target_https_proxies_api, 'SetSslCertificates',
        self.messages.ComputeRegionTargetHttpsProxiesSetSslCertificatesRequest(
            project='my-project',
            region='us-west-1',
            targetHttpsProxy='target-https-proxy-1',
            regionTargetHttpsProxiesSetSslCertificatesRequest=(
                self.messages.RegionTargetHttpsProxiesSetSslCertificatesRequest(
                    sslCertificates=[
                        self.compute_uri +
                        '/projects/my-project/regions/us-west-1/'
                        'sslCertificates/my-cert', self.compute_uri +
                        '/projects/my-project/regions/us-west-1/'
                        'sslCertificates/my-cert2'
                    ])))
    ), (self._target_https_proxies_api, 'SetUrlMap',
        self.messages.ComputeRegionTargetHttpsProxiesSetUrlMapRequest(
            project='my-project',
            region='us-west-1',
            targetHttpsProxy='target-https-proxy-1',
            urlMapReference=self.messages.UrlMapReference(
                urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                        'my-project/regions/us-west-1/urlMaps/my-map' % {
                            'api': self._api
                        }))))],)

  def testUriSupport(self):
    self.RunUpdate("""
          https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/targetHttpsProxies/target-https-proxy-1
          --ssl-certificates https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/sslCertificates/my-cert
          --url-map https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/my-map
        """ % {'api': self._api})

    self.CheckRequests([(
        self._target_https_proxies_api, 'SetSslCertificates',
        self.messages.ComputeRegionTargetHttpsProxiesSetSslCertificatesRequest(
            project='my-project',
            region='us-west-1',
            targetHttpsProxy='target-https-proxy-1',
            regionTargetHttpsProxiesSetSslCertificatesRequest=(
                self.messages.RegionTargetHttpsProxiesSetSslCertificatesRequest(
                    sslCertificates=[
                        self.compute_uri +
                        '/projects/my-project/regions/us-west-1/'
                        'sslCertificates/my-cert'
                    ])))
    ), (self._target_https_proxies_api, 'SetUrlMap',
        self.messages.ComputeRegionTargetHttpsProxiesSetUrlMapRequest(
            project='my-project',
            region='us-west-1',
            targetHttpsProxy='target-https-proxy-1',
            urlMapReference=self.messages.UrlMapReference(
                urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                        'my-project/regions/us-west-1/urlMaps/my-map' % {
                            'api': self._api
                        }))))],)

  def testSimpleCaseWithQuicOverrideAndSslPolicy(self):
    quic_enum = (
        self.messages.TargetHttpsProxiesSetQuicOverrideRequest.
        QuicOverrideValueValuesEnum)

    self.RunUpdate("""
        target-https-proxy-1
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --quic-override DISABLE
          --ssl-policy my-ssl-policy
        """)

    self.CheckRequests([
        (self._target_https_proxies_api, 'SetSslCertificates',
         self.messages.ComputeRegionTargetHttpsProxiesSetSslCertificatesRequest(
             project='my-project',
             region='us-west-1',
             targetHttpsProxy='target-https-proxy-1',
             regionTargetHttpsProxiesSetSslCertificatesRequest=(
                 self.messages.
                 RegionTargetHttpsProxiesSetSslCertificatesRequest(
                     sslCertificates=[
                         self.compute_uri +
                         '/projects/my-project/regions/us-west-1/'
                         'sslCertificates/my-cert', self.compute_uri +
                         '/projects/my-project/regions/us-west-1/'
                         'sslCertificates/my-cert2'
                     ])))),
        (self._target_https_proxies_api, 'SetUrlMap',
         self.messages.ComputeRegionTargetHttpsProxiesSetUrlMapRequest(
             project='my-project',
             region='us-west-1',
             targetHttpsProxy='target-https-proxy-1',
             urlMapReference=self.messages.UrlMapReference(
                 urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                         'my-project/regions/us-west-1/urlMaps/my-map' % {
                             'api': self._api
                         })))),
        # Only targetHttpsProxies have
        # SetQuicOverride and SetSslPolicy requests.
        (self.compute.targetHttpsProxies, 'SetQuicOverride',
         self.messages.ComputeTargetHttpsProxiesSetQuicOverrideRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             targetHttpsProxiesSetQuicOverrideRequest=(
                 self.messages.TargetHttpsProxiesSetQuicOverrideRequest(
                     quicOverride=quic_enum.DISABLE)))),
        (self.compute.targetHttpsProxies, 'SetSslPolicy',
         self.messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project='my-project',
             targetHttpsProxy='target-https-proxy-1',
             sslPolicyReference=self.messages.SslPolicyReference(
                 sslPolicy=(self.compute_uri +
                            '/projects/my-project/global/sslPolicies/'
                            'my-ssl-policy')))),
    ])


if __name__ == '__main__':
  test_case.main()
