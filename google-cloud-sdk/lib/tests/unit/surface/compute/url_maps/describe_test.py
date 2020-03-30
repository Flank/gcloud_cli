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

from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class URLMapsDescribeTest(test_base.BaseTest,
                          completer_test_base.CompleterBase,
                          test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._url_maps_api = self.compute_v1.urlMaps
    self._url_maps = test_resources.URL_MAPS

  def RunDescribe(self, command):
    self.Run('compute url-maps describe ' + command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self._url_maps[0]],
    ])

    self.RunDescribe("""
        url-map-1
        """)

    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='url-map-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
            hostRules:
            - hosts:
              - '*.google.com'
              - google.com
              pathMatcher: www
            - hosts:
              - '*.youtube.com'
              - youtube.com
              - '*-youtube.com'
              pathMatcher: youtube
            name: url-map-1
            pathMatchers:
            - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
              name: www
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
              - paths:
                - /search/ads
                - /search/ads/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
              - paths:
                - /images
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/images
            - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
              name: youtube
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
              - paths:
                - /watch
                - /view
                - /preview
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-1
            tests:
            - host: www.google.com
              path: /search/ads/inline?q=flowers
              service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
            - host: youtube.com
              path: /watch/this
              service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
            """ % {'api': self._api}))

  def testSimpleBackendBucketCase(self):
    self.make_requests.side_effect = iter([
        [self._url_maps[3]],
    ])

    self.RunDescribe("""
        url-map-4
        """)

    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='url-map-4'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/default-bucket
            name: url-map-4
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-4
            """ % {'api': self._api}))

  def testDescribeCompletion(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.URL_MAPS),
        resource_projector.MakeSerializable(test_resources.URL_MAPS)
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
            'url-map-2',
            'url-map-4',
            'url-map-1',
            'url-map-3',
        ],
        cli=self.cli,
    )


class RegionURLMapsDescribeTest(test_base.BaseTest,
                                completer_test_base.CompleterBase,
                                test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = ''
    self._url_maps_api = self.compute_v1.regionUrlMaps
    self._url_maps = test_resources.REGION_URL_MAPS

  def RunDescribe(self, command):
    self.Run(self._api + ' compute url-maps describe --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self._url_maps[0]],
    ])

    self.RunDescribe("""
        url-map-1
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='url-map-1', region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/default-service
            hostRules:
            - hosts:
              - '*.google.com'
              - google.com
              pathMatcher: www
            - hosts:
              - '*.youtube.com'
              - youtube.com
              - '*-youtube.com'
              pathMatcher: youtube
            name: url-map-1
            pathMatchers:
            - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/www-default
              name: www
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/search
              - paths:
                - /search/ads
                - /search/ads/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/ads
              - paths:
                - /images
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/images
            - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/youtube-default
              name: youtube
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/youtube-search
              - paths:
                - /watch
                - /view
                - /preview
                service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/youtube-watch
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/url-map-1
            tests:
            - host: www.google.com
              path: /search/ads/inline?q=flowers
              service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/ads
            - host: youtube.com
              path: /watch/this
              service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/youtube-default
            """ % {'api': self.api}))

  def testSimpleBackendBucketCase(self):
    self.make_requests.side_effect = iter([
        [self._url_maps[3]],
    ])

    self.RunDescribe("""
        url-map-4
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='url-map-4', region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/default-bucket
            name: url-map-4
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/url-map-4
            """ % {'api': self.api}))


class RegionURLMapsDescribeBetaTest(RegionURLMapsDescribeTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.regionUrlMaps
    self._url_maps = test_resources.REGION_URL_MAPS_BETA


class RegionURLMapsDescribeAlphaTest(RegionURLMapsDescribeBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.regionUrlMaps
    self._url_maps = test_resources.REGION_URL_MAPS_ALPHA


if __name__ == '__main__':
  test_case.main()
