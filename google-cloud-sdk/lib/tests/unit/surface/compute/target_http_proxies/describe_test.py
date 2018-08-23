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
"""Tests for the url-maps describe subcommand."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class TargetHttpProxiesDescribeTest(test_base.BaseTest,
                                    completer_test_base.CompleterBase,
                                    test_case.WithOutputCapture):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_v1.targetHttpProxies

  def RunDelete(self, command):
    self.Run('compute target-http-proxies describe ' + command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTP_PROXIES[0]],
    ])

    self.RunDelete('target-http-proxy-1')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Get',
          self.messages.ComputeTargetHttpProxiesGetRequest(
              project='my-project', targetHttpProxy='target-http-proxy-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My first proxy
            name: target-http-proxy-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/targetHttpProxies/target-http-proxy-1
            urlMap: https://www.googleapis.com/compute/v1/projects/my-project/global/urlMaps/url-map-1
            """))

  def testDesribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.TARGET_HTTP_PROXIES)
    uri_list = ['target-http-proxy-1', 'target-http-proxy-2',
                'target-http-proxy-3']
    self.RunCompletion('compute target-http-proxies describe t', uri_list)


class TargetHttpProxiesDescribeAlphaTest(TargetHttpProxiesDescribeTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.targetHttpProxies

  def RunDelete(self, command):
    self.Run('alpha compute target-http-proxies describe --global ' + command)


class RegionTargetHttpProxiesDescribeTest(test_base.BaseTest,
                                          completer_test_base.CompleterBase,
                                          test_case.WithOutputCapture):

  URI_PREFIX = 'https://www.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.regionTargetHttpProxies

    self.target_http_proxies = [
        self.messages.TargetHttpProxy(
            name='target-http-proxy-1',
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-1',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpProxies/target-http-proxy-1')),
        self.messages.TargetHttpProxy(
            name='target-http-proxy-2',
            urlMap=self.URI_PREFIX + 'global/urlMaps/url-map-2',
            selfLink=(self.URI_PREFIX +
                      'global/targetHttpProxies/target-http-proxy-2')),
    ]
    self.region_target_http_proxies = [
        self.messages.TargetHttpProxy(
            name='target-http-proxy-3',
            urlMap=self.URI_PREFIX + 'regions/region-1/urlMaps/url-map-3',
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/targetHttpProxies/target-http-proxy-3'),
            region='region-1'),
        self.messages.TargetHttpProxy(
            name='target-http-proxy-4',
            urlMap=self.URI_PREFIX + 'regions/region-2/urlMaps/url-map-4',
            selfLink=(self.URI_PREFIX +
                      'regions/region-2/targetHttpProxies/target-http-proxy-4'),
            region='region-2'),
    ]
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def RunDelete(self, command):
    self.Run('alpha compute target-http-proxies describe --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTP_PROXIES[0]],
    ])

    self.RunDelete('target-http-proxy-1')

    self.CheckRequests([(self._target_http_proxies_api, 'Get',
                         self.messages.ComputeRegionTargetHttpProxiesGetRequest(
                             project='my-project',
                             region='us-west-1',
                             targetHttpProxy='target-http-proxy-1'))],)

  def testDesribeCompletion(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self.target_http_proxies),
        resource_projector.MakeSerializable(self.region_target_http_proxies)
    ]
    self.RunCompleter(
        flags.TargetHttpProxiesCompleterAlpha,
        expected_command=[
            [
                'alpha',
                'compute',
                'target-http-proxies',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'target-http-proxies',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'target-http-proxy-1',
            'target-http-proxy-2',
            'target-http-proxy-3',
            'target-http-proxy-4',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
