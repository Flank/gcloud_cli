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
"""Tests for the target-https-proxies create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHTTPSProxiesCreateGATest(test_base.BaseTest):

  def _SetUpReleaseTrack(self, api_version, track):
    self.SelectApi(api_version)
    self.track = track

  def SetUp(self):
    self._SetUpReleaseTrack('v1', calliope_base.ReleaseTrack.GA)

  def testSimpleCaseWithoutQuic(self):
    messages = self.messages
    self.make_requests.side_effect = [[
        messages.TargetHttpsProxy(
            name='my-proxy',
            sslCertificates=['my-cert'],
            urlMap='my-map',
            sslPolicy='my-ssl-policy')
    ]]

    results = self.Run("""
        compute target-https-proxies create my-proxy
          --description "My target HTTPS proxy"
          --ssl-certificates my-cert
          --url-map my-map
          --ssl-policy my-ssl-policy
          --format=disable
        """)
    target_https_proxy = list(results)[0]
    self.AssertEqual(target_https_proxy.name, 'my-proxy')
    self.AssertEqual(target_https_proxy.sslCertificates, ['my-cert'])
    self.AssertEqual(target_https_proxy.urlMap, 'my-map')
    self.AssertEqual(target_https_proxy.sslPolicy, 'my-ssl-policy')

    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'Insert',
         messages.ComputeTargetHttpsProxiesInsertRequest(
             project='my-project',
             targetHttpsProxy=messages.TargetHttpsProxy(
                 description='My target HTTPS proxy',
                 name='my-proxy',
                 sslCertificates=[
                     (self.compute_uri + '/projects/my-project/global/'
                      'sslCertificates/my-cert')
                 ],
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map'),
                 sslPolicy=(
                     self.compute_uri +
                     '/projects/my-project/global/sslPolicies/my-ssl-policy'))))
    ],)

  def testSimpleCaseWithQuicEnabled(self):
    messages = self.messages
    quic_enum = messages.TargetHttpsProxy.QuicOverrideValueValuesEnum

    self.make_requests.side_effect = [[
        messages.TargetHttpsProxy(
            name='my-proxy',
            sslCertificates=['my-cert', 'my-cert2'],
            urlMap='my-map',
            quicOverride=quic_enum.ENABLE,
            sslPolicy='my-ssl-policy')
    ]]

    results = self.Run("""
        compute target-https-proxies create my-proxy
          --description "My target HTTPS proxy"
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --quic-override ENABLE
          --ssl-policy my-ssl-policy
          --format=disable
        """)
    target_https_proxy = list(results)[0]
    self.AssertEqual(target_https_proxy.name, 'my-proxy')
    self.AssertEqual(target_https_proxy.sslCertificates,
                     ['my-cert', 'my-cert2'])
    self.AssertEqual(target_https_proxy.urlMap, 'my-map')
    self.AssertEqual(target_https_proxy.sslPolicy, 'my-ssl-policy')

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'Insert',
         messages.ComputeTargetHttpsProxiesInsertRequest(
             project='my-project',
             targetHttpsProxy=messages.TargetHttpsProxy(
                 description='My target HTTPS proxy',
                 name='my-proxy',
                 sslCertificates=[(cert_uri + 'my-cert'),
                                  (cert_uri + 'my-cert2')],
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map'),
                 quicOverride=quic_enum.ENABLE,
                 sslPolicy=(
                     self.compute_uri +
                     '/projects/my-project/global/sslPolicies/my-ssl-policy'))))
    ],)

  def testUriSupport(self):
    messages = self.messages

    self.Run("""
        compute target-https-proxies create
          {uri}/projects/my-project/global/targetHttpsProxies/my-proxy
          --ssl-certificates {uri}/projects/my-project/global/sslCertificates/my-cert
          --url-map {uri}/projects/my-project/global/urlMaps/my-map
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.targetHttpsProxies, 'Insert',
          messages.ComputeTargetHttpsProxiesInsertRequest(
              project='my-project',
              targetHttpsProxy=messages.TargetHttpsProxy(
                  name='my-proxy',
                  sslCertificates=[
                      (self.compute_uri + '/projects/my-project/global/'
                       'sslCertificates/my-cert')
                  ],
                  urlMap=(self.compute_uri +
                          '/projects/my-project/global/urlMaps/my-map'))))],)

  def testWithoutSSLCertificate(self):
    # Skip this test case in TargetHTTPSProxiesCreateAlphaTest, because
    # --ssl-certificates is now optional in Alpha.
    if not hasattr(self, '_api') or self._api != 'alpha':
      with self.AssertRaisesArgumentErrorMatches(
          'argument --ssl-certificates: Must be specified.'):
        self.Run("""
            compute target-https-proxies create my-proxy
              --url-map my-map
            """)

      self.CheckRequests()

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.Run("""
          compute target-https-proxies create my-proxy
            --ssl-certificates my-cert
          """)

    self.CheckRequests()


class TargetHTTPSProxiesCreateBetaTest(TargetHTTPSProxiesCreateGATest):

  def SetUp(self):
    self._api = 'beta'
    self._SetUpReleaseTrack('beta', calliope_base.ReleaseTrack.BETA)

  def testSimpleCaseWithoutQuic(self):
    messages = self.messages
    self.make_requests.side_effect = [[
        messages.TargetHttpsProxy(
            name='my-proxy',
            sslCertificates=[
                'https://compute.googleapis.com/compute/{0}/'
                'projects/my-project/regions/us-west-1/'
                'sslCertificates/my-cert'.format(self._api)
            ],
            urlMap='https://compute.googleapis.com/compute/{0}/projects/'
            'my-project/regions/us-west-1/urlMaps/my-map'.format(self._api),
            sslPolicy='my-ssl-policy')
    ]]

    results = self.Run("""
        compute target-https-proxies create --region us-west-1
          my-proxy
          --description "My target HTTPS proxy"
          --ssl-certificates my-cert
          --url-map my-map
          --ssl-policy my-ssl-policy
          --format=disable
        """)
    target_https_proxy = list(results)[0]
    self.AssertEqual(target_https_proxy.name, 'my-proxy')
    self.AssertEqual(target_https_proxy.sslCertificates, [
        'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/regions/us-west-1/'
        'sslCertificates/my-cert'.format(self._api)
    ])
    self.AssertEqual(
        target_https_proxy.urlMap,
        'https://compute.googleapis.com/compute/{0}/projects/'
        'my-project/regions/us-west-1/urlMaps/my-map'.format(self._api))
    self.AssertEqual(target_https_proxy.sslPolicy, 'my-ssl-policy')

    self.CheckRequests([
        (self.compute.regionTargetHttpsProxies, 'Insert',
         messages.ComputeRegionTargetHttpsProxiesInsertRequest(
             project='my-project',
             region='us-west-1',
             targetHttpsProxy=messages.TargetHttpsProxy(
                 description='My target HTTPS proxy',
                 name='my-proxy',
                 sslCertificates=[
                     (self.compute_uri + '/projects/my-project/regions/'
                      'us-west-1/sslCertificates/my-cert')
                 ],
                 urlMap=(self.compute_uri +
                         '/projects/my-project/regions/us-west-1/'
                         'urlMaps/my-map'),
                 sslPolicy=(
                     self.compute_uri +
                     '/projects/my-project/global/sslPolicies/my-ssl-policy'))))
    ],)

  def testSimpleCaseWithQuicEnabled(self):
    messages = self.messages
    quic_enum = messages.TargetHttpsProxy.QuicOverrideValueValuesEnum

    self.make_requests.side_effect = [[
        messages.TargetHttpsProxy(
            name='my-proxy',
            sslCertificates=[
                'https://compute.googleapis.com/compute/{0}/'
                'projects/my-project/global/'
                'sslCertificates/my-cert',
                'https://compute.googleapis.com/compute/{0}/'
                'projects/my-project/global/'
                'sslCertificates/my-cert2'.format(self._api)
            ],
            urlMap='my-map',
            quicOverride=quic_enum.ENABLE,
            sslPolicy='my-ssl-policy')
    ]]

    results = self.Run("""
        compute target-https-proxies create --global my-proxy
          --description "My target HTTPS proxy"
          --ssl-certificates my-cert,my-cert2
          --url-map my-map
          --quic-override ENABLE
          --ssl-policy my-ssl-policy
          --format=disable
        """)
    target_https_proxy = list(results)[0]
    self.AssertEqual(target_https_proxy.name, 'my-proxy')
    self.AssertEqual(target_https_proxy.sslCertificates, [
        'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/global/'
        'sslCertificates/my-cert', 'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/global/'
        'sslCertificates/my-cert2'.format(self._api)
    ])
    self.AssertEqual(target_https_proxy.urlMap, 'my-map')
    self.AssertEqual(target_https_proxy.sslPolicy, 'my-ssl-policy')

    cert_uri = self.compute_uri + '/projects/my-project/global/sslCertificates/'
    self.CheckRequests([
        (self.compute.targetHttpsProxies, 'Insert',
         messages.ComputeTargetHttpsProxiesInsertRequest(
             project='my-project',
             targetHttpsProxy=messages.TargetHttpsProxy(
                 description='My target HTTPS proxy',
                 name='my-proxy',
                 sslCertificates=[(cert_uri + 'my-cert'),
                                  (cert_uri + 'my-cert2')],
                 urlMap=(self.compute_uri +
                         '/projects/my-project/global/urlMaps/my-map'),
                 quicOverride=quic_enum.ENABLE,
                 sslPolicy=(
                     self.compute_uri +
                     '/projects/my-project/global/sslPolicies/my-ssl-policy'))))
    ],)

  def testUriSupport(self):
    messages = self.messages

    self.Run("""
        compute target-https-proxies create --region us-west-1
          {uri}/projects/my-project/regions/us-west-1/targetHttpsProxies/my-proxy
          --ssl-certificates {uri}/projects/my-project/regions/us-west-1/sslCertificates/my-cert
          --url-map {uri}/projects/my-project/regions/us-west-1/urlMaps/my-map
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionTargetHttpsProxies, 'Insert',
          messages.ComputeRegionTargetHttpsProxiesInsertRequest(
              project='my-project',
              region='us-west-1',
              targetHttpsProxy=messages.TargetHttpsProxy(
                  name='my-proxy',
                  sslCertificates=[(self.compute_uri + '/projects/my-project/'
                                    'regions/us-west-1/sslCertificates/my-cert')
                                  ],
                  urlMap=(self.compute_uri +
                          '/projects/my-project/regions/us-west-1/'
                          'urlMaps/my-map'))))],)

    self.CheckRequests()


class TargetHTTPSProxiesCreateAlphaTest(TargetHTTPSProxiesCreateBetaTest):

  def SetUp(self):
    self._api = 'alpha'
    self._SetUpReleaseTrack('alpha', calliope_base.ReleaseTrack.ALPHA)

  def testProxyBind(self):
    messages = self.messages

    self.Run("""
        compute target-https-proxies create --region us-west-1
          {uri}/projects/my-project/regions/us-west-1/targetHttpsProxies/my-proxy
          --ssl-certificates {uri}/projects/my-project/regions/us-west-1/sslCertificates/my-cert
          --url-map {uri}/projects/my-project/regions/us-west-1/urlMaps/my-map
          --proxy-bind
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionTargetHttpsProxies, 'Insert',
          messages.ComputeRegionTargetHttpsProxiesInsertRequest(
              project='my-project',
              region='us-west-1',
              targetHttpsProxy=messages.TargetHttpsProxy(
                  name='my-proxy',
                  sslCertificates=[(self.compute_uri + '/projects/my-project/'
                                    'regions/us-west-1/sslCertificates/my-cert')
                                  ],
                  urlMap=(self.compute_uri +
                          '/projects/my-project/regions/us-west-1/'
                          'urlMaps/my-map'),
                  proxyBind=True)))],)

  def testOptionalSslCertificates(self):
    messages = self.messages

    self.Run("""
        compute target-https-proxies create --region us-west-1
          {uri}/projects/my-project/regions/us-west-1/targetHttpsProxies/my-proxy
          --url-map {uri}/projects/my-project/regions/us-west-1/urlMaps/my-map
          --proxy-bind
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionTargetHttpsProxies, 'Insert',
          messages.ComputeRegionTargetHttpsProxiesInsertRequest(
              project='my-project',
              region='us-west-1',
              targetHttpsProxy=messages.TargetHttpsProxy(
                  name='my-proxy',
                  sslCertificates=[],
                  urlMap=(self.compute_uri +
                          '/projects/my-project/regions/us-west-1/'
                          'urlMaps/my-map'),
                  proxyBind=True)))],)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
