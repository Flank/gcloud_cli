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
"""Tests for the target-http-proxies list subcommand."""

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


class TargetHttpProxiesListTest(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.TARGET_HTTP_PROXIES))

  def testSimpleCase(self):
    self.Run("""
        compute target-http-proxies list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.targetHttpProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                URL_MAP
            target-http-proxy-1 url-map-1
            target-http-proxy-2 url-map-2
            target-http-proxy-3 url-map-3
            """), normalize_space=True)

  def testTargetHttpProxiesCompleter(self):
    self.RunCompleter(
        flags.TargetHttpProxiesCompleter,
        expected_command=[
            'compute',
            'target-http-proxies',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'target-http-proxy-1',
            'target-http-proxy-2',
            'target-http-proxy-3',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.targetHttpProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


class TargetHttpProxiesListBetaTest(test_base.BaseTest,
                                    completer_test_base.CompleterBase):

  URI_PREFIX = 'https://compute.googleapis.com/compute/beta/projects/my-project/'

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi('beta')
    self._compute_api = self.compute_beta

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

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

  def testGlobalOption(self):
    command = self._api + ' compute target-http-proxies list --uri --global'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/targetHttpProxies/target-http-proxy-1
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/targetHttpProxies/target-http-proxy-2
    """.format(self._api))

    self.RequestOnlyGlobal(command, self.target_http_proxies, output)

  def testOneRegion(self):
    command = self._api + (' compute target-http-proxies list --uri --regions '
                           'region-1')
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/targetHttpProxies/target-http-proxy-3
        """.format(self._api))

    self.RequestOneRegion(command, self.region_target_http_proxies, output)

  def testTwoRegions(self):
    command = self._api + """
       compute target-http-proxies list --uri --regions region-1,region-2
    """
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/targetHttpProxies/target-http-proxy-3
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-2/targetHttpProxies/target-http-proxy-4
        """.format(self._api))

    self.RequestTwoRegions(command, self.region_target_http_proxies, output)

  def testPositionalArgsWithSimpleNames(self):
    command = self._api + ' compute target-http-proxies list'
    return_value = self.target_http_proxies + self.region_target_http_proxies
    output = ("""\
        NAME                URL_MAP
        target-http-proxy-1 url-map-1
        target-http-proxy-2 url-map-2
        target-http-proxy-3 url-map-3
        target-http-proxy-4 url-map-4
    """)

    self.RequestAggregate(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.targetHttpProxies, 'List',
                   self.messages.ComputeTargetHttpProxiesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)

    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.targetHttpProxies, 'AggregatedList',
                   self.messages.ComputeTargetHttpProxiesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionTargetHttpProxies, 'List',
                   self.messages.ComputeRegionTargetHttpProxiesListRequest(
                       project='my-project', region='region-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionTargetHttpProxies, 'List',
                   self.messages.ComputeRegionTargetHttpProxiesListRequest(
                       project='my-project', region='region-1')),
                  (self._compute_api.regionTargetHttpProxies, 'List',
                   self.messages.ComputeRegionTargetHttpProxiesListRequest(
                       project='my-project', region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)


class TargetHttpProxiesListAlphaTest(TargetHttpProxiesListBetaTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha


if __name__ == '__main__':
  test_case.main()
