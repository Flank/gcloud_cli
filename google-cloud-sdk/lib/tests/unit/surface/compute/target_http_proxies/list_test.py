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
from tests.lib.surface.compute.load_balancing import test_resources

import mock


class TargetHttpProxiesListTest(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

  def SetUp(self):
    self._api = ''
    self.SelectApi('v1')
    self._compute_api = self.compute_v1

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

  def testSimpleCase(self):
    expected = """\
    NAME                URL_MAP
    target-http-proxy-1 url-map-1
    target-http-proxy-2 url-map-2
    target-http-proxy-3 url-map-3
    """
    self.RequestOnlyGlobal(
        self._api + ' compute target-http-proxies list --global',
        resource_projector.MakeSerializable(test_resources.TARGET_HTTP_PROXIES),
        expected)

  def testTargetHttpProxiesCompleter(self):
    # flags.TargetHttpProxiesCompleter uses the v1 interface only.
    self._api = ''
    self.SelectApi('v1')
    self._compute_api = self.compute_v1

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.TARGET_HTTP_PROXIES),
        resource_projector.MakeSerializable(test_resources.TARGET_HTTP_PROXIES)
    ]
    expected_global_command = [
        'compute',
        'target-http-proxies',
        'list',
        '--global',
        '--uri',
        '--quiet',
        '--format=disable',
    ]
    expected_region_command = [
        'compute',
        'target-http-proxies',
        'list',
        '--filter=region:*',
        '--uri',
        '--quiet',
        '--format=disable',
    ]

    self.RunCompleter(
        flags.TargetHttpProxiesCompleter,
        expected_command=[expected_global_command, expected_region_command],
        expected_completions=[
            'target-http-proxy-1',
            'target-http-proxy-2',
            'target-http-proxy-3',
        ],
        cli=self.cli,
    )

    aggregated_list_request = self._getListRequestMessage('my-project')

    self.list_json.assert_called_with(
        requests=[
            (self._compute_api.targetHttpProxies, 'AggregatedList',
             aggregated_list_request),
        ],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testGlobalOption(self):
    command = self._api + ' compute target-http-proxies list --uri --global'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/targetHttpProxies/target-http-proxy-1
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/targetHttpProxies/target-http-proxy-2
    """.format(self.api))

    self.RequestOnlyGlobal(command, self.target_http_proxies, output)

  def testOneRegion(self):
    command = self._api + (' compute target-http-proxies list --uri --regions '
                           'region-1')
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/targetHttpProxies/target-http-proxy-3
        """.format(self.api))

    self.RequestOneRegion(command, self.region_target_http_proxies, output)

  def testTwoRegions(self):
    command = self._api + """
       compute target-http-proxies list --uri --regions region-1,region-2
    """
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/targetHttpProxies/target-http-proxy-3
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-2/targetHttpProxies/target-http-proxy-4
        """.format(self.api))

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
                   self._getListRequestMessage('my-project'))],
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

  def _getListRequestMessage(self, project):
    return self.messages.ComputeTargetHttpProxiesAggregatedListRequest(
        project=project, includeAllScopes=True)


class TargetHttpProxiesListBetaTest(TargetHttpProxiesListTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/beta/projects/my-project/'

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi('beta')
    self._compute_api = self.compute_beta


class TargetHttpProxiesListAlphaTest(TargetHttpProxiesListBetaTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha

  def _getListRequestMessage(self, project):
    request_params = {'includeAllScopes': True}
    if hasattr(self.messages.ComputeTargetHttpProxiesAggregatedListRequest,
               'returnPartialSuccess'):
      request_params['returnPartialSuccess'] = True
    return self.messages.ComputeTargetHttpProxiesAggregatedListRequest(
        project=project, **request_params)


if __name__ == '__main__':
  test_case.main()
