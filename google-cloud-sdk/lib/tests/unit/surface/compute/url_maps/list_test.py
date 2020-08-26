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
"""Tests for the url-maps list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.url_maps import test_resources
import mock


class URLMapsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

  def SetUp(self):
    self.SelectApi('v1')
    self._api = ''
    self._url_maps_api = self.compute_v1.urlMaps
    self._test_url_maps = test_resources.URL_MAPS

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.url_maps = [
        self.messages.UrlMap(
            name='url-map1',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map1'),
        self.messages.UrlMap(
            name='url-map2',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map2')
    ]
    self.region_url_maps = [
        self.messages.UrlMap(
            name='region-url-map1',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-1',
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/url-maps/region-url-map1')),
        self.messages.UrlMap(
            name='region-url-map2',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-2',
            selfLink=(self.URI_PREFIX +
                      'regions/region-2/url-maps/region-url-map2'))
    ]

  def RunList(self, command):
    self.Run('compute url-maps list --global ' + command)

  def testSimpleCase(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._test_url_maps),
    ]

    self.RunList('')

    self.list_json.assert_called_once_with(
        requests=[
            (self._url_maps_api, 'List',
             self.messages.ComputeUrlMapsListRequest(project='my-project'))
        ],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME      DEFAULT_SERVICE
            url-map-1 backendServices/default-service
            url-map-2 backendServices/default-service
            url-map-3 backendServices/default-service
            url-map-4 backendBuckets/default-bucket
            """),
        normalize_space=True)

  def testUrlMapsCompleter(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._test_url_maps),
    ]

    self.RunCompleter(
        flags.UrlMapsCompleter,
        expected_command=[
            'compute',
            'url-maps',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'url-map-1',
            'url-map-2',
            'url-map-3',
            'url-map-4',
        ],
        cli=self.cli,
    )


class RegionURLMapsListTest(test_base.BaseTest,
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

    self.url_maps = [
        self.messages.UrlMap(
            name='url-map1',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map1'),
        self.messages.UrlMap(
            name='url-map2',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map2')
    ]
    self.region_url_maps = [
        self.messages.UrlMap(
            name='region-url-map1',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-1',
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/url-maps/region-url-map1')),
        self.messages.UrlMap(
            name='region-url-map2',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-2',
            selfLink=(self.URI_PREFIX +
                      'regions/region-2/url-maps/region-url-map2'))
    ]

  def testGlobalOption(self):
    command = self._api + ' compute url-maps list --uri --global'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/url-maps/url-map1
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/url-maps/url-map2
    """.format(self.api))

    self.RequestOnlyGlobal(command, self.url_maps, output)

  def testOneRegion(self):
    command = self._api + ' compute url-maps list --uri --regions region-1'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/url-maps/region-url-map1
        """.format(self.api))

    self.RequestOneRegion(command, self.region_url_maps, output)

  def testTwoRegions(self):
    command = self._api + (' compute url-maps list --uri --regions '
                           'region-1,region-2')
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/url-maps/region-url-map1
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-2/url-maps/region-url-map2
        """.format(self.api))

    self.RequestTwoRegions(command, self.region_url_maps, output)

  def testPositionalArgsWithSimpleNames(self):
    command = self._api + ' compute url-maps list'
    return_value = self.url_maps + self.region_url_maps
    output = ("""\
        NAME            DEFAULT_SERVICE
        url-map1        backendService/default-service
        url-map2        backendService/default-service
        region-url-map1 backendService/default-service
        region-url-map2 backendService/default-service
    """)

    self.RequestAggregate(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[
            (self._compute_api.urlMaps, 'List',
             self.messages.ComputeUrlMapsListRequest(project='my-project'))
        ],
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
        requests=[(self._compute_api.urlMaps, 'AggregatedList',
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
        requests=[(self._compute_api.regionUrlMaps, 'List',
                   self.messages.ComputeRegionUrlMapsListRequest(
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
        requests=[(self._compute_api.regionUrlMaps, 'List',
                   self.messages.ComputeRegionUrlMapsListRequest(
                       project='my-project', region='region-1')),
                  (self._compute_api.regionUrlMaps, 'List',
                   self.messages.ComputeRegionUrlMapsListRequest(
                       project='my-project', region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def _getListRequestMessage(self, project):
    return self.messages.ComputeUrlMapsAggregatedListRequest(
        project=project, includeAllScopes=True)


class RegionURLMapsListBetaTest(RegionURLMapsListTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/beta/projects/my-project/'

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi('beta')
    self._compute_api = self.compute_beta

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.url_maps = [
        self.messages.UrlMap(
            name='url-map1',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map1'),
        self.messages.UrlMap(
            name='url-map2',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map2')
    ]
    self.region_url_maps = [
        self.messages.UrlMap(
            name='region-url-map1',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-1',
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/url-maps/region-url-map1')),
        self.messages.UrlMap(
            name='region-url-map2',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-2',
            selfLink=(self.URI_PREFIX +
                      'regions/region-2/url-maps/region-url-map2'))
    ]


class RegionURLMapsListAlphaTest(RegionURLMapsListBetaTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.url_maps = [
        self.messages.UrlMap(
            name='url-map1',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map1'),
        self.messages.UrlMap(
            name='url-map2',
            defaultService=(self.URI_PREFIX +
                            'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/url-maps/url-map2')
    ]
    self.region_url_maps = [
        self.messages.UrlMap(
            name='region-url-map1',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-1',
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/url-maps/region-url-map1')),
        self.messages.UrlMap(
            name='region-url-map2',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-2',
            selfLink=(self.URI_PREFIX +
                      'regions/region-2/url-maps/region-url-map2'))
    ]

  def _getListRequestMessage(self, project):
    request_params = {'includeAllScopes': True}
    if hasattr(self.messages.ComputeUrlMapsAggregatedListRequest,
               'returnPartialSuccess'):
      request_params['returnPartialSuccess'] = True

    return self.messages.ComputeUrlMapsAggregatedListRequest(
        project=project, **request_params)


if __name__ == '__main__':
  test_case.main()
