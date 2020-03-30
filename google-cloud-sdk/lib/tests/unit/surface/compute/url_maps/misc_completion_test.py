# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for autocompletion in url-maps subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class UrlMapsCompletionTests(test_base.BaseTest,
                             completer_test_base.CompleterBase):

  def testUrlMapsInvalidateCdnCacheCompletion(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            resource_projector.MakeSerializable(test_resources.URL_MAPS))
    ]
    self.RunCompletion('compute url-maps invalidate-cdn-cache u',
                       ['url-map-1', 'url-map-2', 'url-map-3', 'url-map-4'])


class RegionUrlMapsCompletionTests(test_base.BaseTest,
                                   completer_test_base.CompleterBase):

  URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

  def SetUp(self):
    self.SelectApi('v1')
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.url_maps = [
        self.messages.UrlMap(
            name='url-map1',
            defaultService=(
                self.URI_PREFIX + 'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/urlMaps/url-map1'),
        self.messages.UrlMap(
            name='url-map2',
            defaultService=(
                self.URI_PREFIX + 'global/backendService/default-service'),
            selfLink=self.URI_PREFIX + 'global/urlMaps/url-map2'),
    ]
    self.region_url_maps = [
        self.messages.UrlMap(
            name='region-url-map1',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-1',
            selfLink=(
                self.URI_PREFIX + 'regions/region-1/urlMaps/region-url-map1')),
        self.messages.UrlMap(
            name='region-url-map2',
            defaultService=(self.URI_PREFIX +
                            'regions/region-1/backendService/default-service'),
            region='region-2',
            selfLink=(
                self.URI_PREFIX + 'regions/region-1/urlMaps/region-url-map2'))
    ]

  def testUrlMapsCompleterRegional(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self.url_maps),
        resource_projector.MakeSerializable(self.region_url_maps)
    ]
    self.RunCompleter(
        flags.UrlMapsCompleterAlpha,
        expected_command=[
            [
                'compute',
                'url-maps',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'compute',
                'url-maps',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'url-map1',
            'url-map2',
            'region-url-map1',
            'region-url-map2',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
