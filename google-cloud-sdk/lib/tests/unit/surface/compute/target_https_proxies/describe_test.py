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
"""Tests for the url-maps describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.load_balancing import test_resources

import mock


class TargetHttpsProxiesDescribeTest(test_base.BaseTest,
                                     completer_test_base.CompleterBase,
                                     test_case.WithOutputCapture):

  def SetUp(self):
    self._api = ''
    self.SelectApi('v1')
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDescribe(self, command):
    self.Run('compute target-https-proxies describe %s' % command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_V1[0]],
    ])

  def testSimpleCase(self):
    self.LoadSideEffect()

    self.RunDescribe('target-https-proxy-1')

    self.CheckRequests([(self._target_https_proxies_api, 'Get',
                         self.messages.ComputeTargetHttpsProxiesGetRequest(
                             project='my-project',
                             targetHttpsProxy='target-https-proxy-1'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My first proxy
            name: target-https-proxy-1
            selfLink: https://compute.googleapis.com/compute/{version}/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
            sslCertificates:
            - {uri}/projects/my-project/global/sslCertificates/ssl-cert-1
            urlMap: {uri}/projects/my-project/global/urlMaps/url-map-1
            """.format(version=self.api, uri=self.compute_uri)))


class TargetHttpsProxiesDescribeBetaTest(TargetHttpsProxiesDescribeTest):

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDescribe(self, command):
    self.Run('beta compute target-https-proxies describe %s' % command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_BETA[0]],
    ])


class TargetHttpsProxiesDescribeAlphaTest(TargetHttpsProxiesDescribeBetaTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDescribe(self, command):
    self.Run('alpha compute target-https-proxies describe %s' % command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_ALPHA[0]],
    ])


class RegionTargetHttpsProxiesDescribeTest(test_base.BaseTest,
                                           completer_test_base.CompleterBase,
                                           test_case.WithOutputCapture):

  URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

  def SetUp(self):
    self._api = ''
    self.SelectApi('v1')
    self._target_https_proxies_api = self.compute.regionTargetHttpsProxies

    self.target_https_proxies = [
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-1',
            sslCertificates=[
                self.URI_PREFIX + 'global/sslCertificates/my-cert-1'
            ],
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-1',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpsProxies/target-https-proxy-1')),
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-2',
            sslCertificates=[
                self.URI_PREFIX + 'global/sslCertificates/my-cert-2'
            ],
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-2',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpsProxies/target-https-proxy-2')),
    ]

    self.region_target_https_proxies = [
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-3',
            sslCertificates=[
                self.URI_PREFIX + 'regions/region-1/sslCertificates/my-cert-1'
            ],
            urlMap=self.URI_PREFIX + 'regions/region-1/urlMaps/url-map-3',
            selfLink=(self.URI_PREFIX + 'regions/region-1/targetHttpsProxies/'
                      'target-https-proxy-3'),
            region='region-1'),
        self.messages.TargetHttpsProxy(
            name='target-https-proxy-4',
            sslCertificates=[
                self.URI_PREFIX + 'regions/region-2/sslCertificates/my-cert-2'
            ],
            urlMap=self.URI_PREFIX + 'regions/region-2/urlMaps/url-map-4',
            selfLink=(self.URI_PREFIX + 'regions/region-2/targetHttpsProxies/'
                      'target-https-proxy-4'),
            region='region-2'),
    ]
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def RunDescribe(self, command):
    self.Run('compute target-https-proxies describe --region us-west-1 ' +
             command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_V1[0]],
    ])

  def testSimpleCase(self):
    self.LoadSideEffect()

    self.RunDescribe('target-https-proxy-1')

    self.CheckRequests(
        [(self._target_https_proxies_api, 'Get',
          self.messages.ComputeRegionTargetHttpsProxiesGetRequest(
              project='my-project',
              region='us-west-1',
              targetHttpsProxy='target-https-proxy-1'))],)

  def testDescribleCompletion(self):
    self._api = ''
    self.SelectApi('v1')
    self._target_https_proxies_api = self.compute.targetHttpsProxies

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self.target_https_proxies),
        resource_projector.MakeSerializable(self.region_target_https_proxies)
    ]
    self.RunCompleter(
        flags.TargetHttpsProxiesCompleterAlpha,
        expected_command=[
            [
                'compute',
                'target-https-proxies',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'compute',
                'target-https-proxies',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'target-https-proxy-1',
            'target-https-proxy-2',
            'target-https-proxy-3',
            'target-https-proxy-4',
        ],
        cli=self.cli,
    )


class RegionTargetHttpsProxiesDescribeBetaTest(
    RegionTargetHttpsProxiesDescribeTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/beta/projects/my-project/'

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.regionTargetHttpsProxies

  def RunDescribe(self, command):
    self.Run('beta compute target-https-proxies describe --region us-west-1 ' +
             command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_BETA[0]],
    ])


class RegionTargetHttpsProxiesDescribeAlphaTest(
    RegionTargetHttpsProxiesDescribeBetaTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.regionTargetHttpsProxies

  def RunDescribe(self, command):
    self.Run('alpha compute target-https-proxies describe --region us-west-1 ' +
             command)

  def LoadSideEffect(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTPS_PROXIES_ALPHA[0]],
    ])


if __name__ == '__main__':
  test_case.main()
