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
"""Tests for the url-maps remove-path-matcher subcommand."""

from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UrlMapsRemovePathMatcherTest(test_base.BaseTest):

  _V1_URI_PREFIX = 'https://www.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def SetUp(self):
    self.SelectApi('v1')
    self._url_maps_api = self.compute_v1.urlMaps
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
            self.messages.HostRule(
                hosts=['*-youtube.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-search'),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-watch'),
                ]),
            self.messages.PathMatcher(
                name='google',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'google-default'),
        ],
    )

  def RunRemovePathMatcher(self, command):
    self.Run('compute url-maps remove-path-matcher ' + command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunRemovePathMatcher('url-map-1 --path-matcher-name youtube')

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='google',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'google-default'),
        ],
    )

    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))],
                       [(self._url_maps_api, 'Update',
                         self.messages.ComputeUrlMapsUpdateRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             urlMapResource=expected_url_map))])

  def testWithNonExistentPathMatcher(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No path matcher with the name \[my-matcher\] was found.'):
      self.RunRemovePathMatcher('url-map-1 --path-matcher-name my-matcher')

    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))])


class UrlMapsRemovePathMatcherAlphaTest(UrlMapsRemovePathMatcherTest):

  _V1_URI_PREFIX = (
      'https://www.googleapis.com/compute/alpha/projects/my-project/')
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute_alpha.urlMaps
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
            self.messages.HostRule(
                hosts=['*-youtube.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-search'),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-watch'),
                ]),
            self.messages.PathMatcher(
                name='google',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'google-default'),
        ],
    )

  def RunRemovePathMatcher(self, command):
    self.Run('alpha compute url-maps remove-path-matcher --global ' + command)


class RegionUrlMapsRemovePathMatcherTest(test_base.BaseTest):

  _V1_URI_PREFIX = (
      'https://www.googleapis.com/compute/alpha/projects/my-project/')
  _BACKEND_SERVICES_URI_PREFIX = (
      _V1_URI_PREFIX + 'regions/us-west-1/backendServices/')

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute_alpha.regionUrlMaps
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
            self.messages.HostRule(
                hosts=['*-youtube.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-search'),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-watch'),
                ]),
            self.messages.PathMatcher(
                name='google',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'google-default'),
        ],
    )

  def RunRemovePathMatcher(self, command):
    self.Run('alpha compute url-maps remove-path-matcher --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunRemovePathMatcher('url-map-1 --path-matcher-name youtube')

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='google',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'google-default'),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              urlMap='url-map-1', project='my-project', region='us-west-1'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              region='us-west-1',
              urlMapResource=expected_url_map))])

  def testWithNonExistentPathMatcher(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No path matcher with the name \[my-matcher\] was found.'):
      self.RunRemovePathMatcher('url-map-1 --path-matcher-name my-matcher')

    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             region='us-west-1'))])


if __name__ == '__main__':
  test_case.main()
