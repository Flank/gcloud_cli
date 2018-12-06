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
"""Tests for the url-maps add-host-rule subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UrlMapsAddHostRuleTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._url_maps_collection = self.compute_v1.urlMaps
    self._backend_services_uri_prefix = (
        'https://www.googleapis.com/compute/%s/projects/my-project/'
        'global/backendServices/' % self._api)
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

  def _RunAddHostRule(self, command):
    self.Run("""
        compute url-maps add-host-rule """ + command)

  def testAddHostRule(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self._RunAddHostRule("""
        url-map-1
          --description new
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                description='new',
                hosts=['a.b.com', 'c.d.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

    self.CheckRequests([(self._url_maps_collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))],
                       [(self._url_maps_collection, 'Update',
                         self.messages.ComputeUrlMapsUpdateRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             urlMapResource=expected_url_map))])

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self._RunAddHostRule("""
          https://www.googleapis.com/compute/%s/projects/my-project/global/urlMaps/url-map-1
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """ % self._api)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                hosts=['a.b.com', 'c.d.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

    self.CheckRequests([(self._url_maps_collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))],
                       [(self._url_maps_collection, 'Update',
                         self.messages.ComputeUrlMapsUpdateRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             urlMapResource=expected_url_map))])

  def testHostsRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --hosts: Must be specified.'):
      self._RunAddHostRule("""
          url-map-1
            --description new
            --path-matcher-name youtube
          """)

    self.CheckRequests()

  def testPathMatcherRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path-matcher-name: Must be specified.'):
      self._RunAddHostRule("""
          url-map-1
            --description new
            --hosts a.b.com,c.d.com
          """)

    self.CheckRequests()


class UrlMapsAddHostRuleTestAlpha(UrlMapsAddHostRuleTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_collection = self.compute_alpha.urlMaps
    self._backend_services_uri_prefix = (
        'https://www.googleapis.com/compute/%s/projects/my-project/'
        'global/backendServices/' % self._api)
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

  def _RunAddHostRule(self, command):
    self.Run("""
        alpha compute url-maps add-host-rule --global """ + command)


class RegionalUrlMapsAddHostRuleTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_collection = self.compute_alpha.regionUrlMaps
    self._backend_services_uri_prefix = (
        'https://www.googleapis.com/compute/alpha/projects/my-project/'
        'regions/us-west-1/backendServices/')
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        region='us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

  def _RunAddHostRule(self, command):
    self.Run("""
        alpha compute url-maps add-host-rule --region us-west-1 """ + command)

  def testAddHostRule(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self._RunAddHostRule("""
        url-map-1
          --description new
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        region='us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                description='new',
                hosts=['a.b.com', 'c.d.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

    self.CheckRequests(
        [(self._url_maps_collection, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              urlMap='url-map-1', project='my-project', region='us-west-1'))],
        [(self._url_maps_collection, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              region='us-west-1',
              urlMapResource=expected_url_map))])

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self._RunAddHostRule("""
          https://www.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/urlMaps/url-map-1
          --hosts a.b.com,c.d.com
          --path-matcher-name youtube
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'default-service',
        region='us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                hosts=['a.b.com', 'c.d.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=self._backend_services_uri_prefix +
                'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=self._backend_services_uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=self._backend_services_uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=self._backend_services_uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._backend_services_uri_prefix +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._backend_services_uri_prefix +
                        'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=self._backend_services_uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=self._backend_services_uri_prefix + 'youtube-default'),
        ])

    self.CheckRequests(
        [(self._url_maps_collection, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              urlMap='url-map-1', project='my-project', region='us-west-1'))],
        [(self._url_maps_collection, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              region='us-west-1',
              urlMapResource=expected_url_map))])

  def testHostsRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --hosts: Must be specified.'):
      self._RunAddHostRule("""
          url-map-1
            --description new
            --path-matcher-name youtube
          """)

    self.CheckRequests()

  def testPathMatcherRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path-matcher-name: Must be specified.'):
      self._RunAddHostRule("""
          url-map-1
            --description new
            --hosts a.b.com,c.d.com
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
