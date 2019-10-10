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
"""Tests for the url-maps add-path-matcher subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UrlMapsAddPathMatcherGaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')

    self._url_maps_api = self.compute_v1.urlMaps

    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
        ],)

  def RunAddPathMatcher(self, command):
    self.Run('compute url-maps add-path-matcher ' + command)

  def _MakeExpectedUrlMapGetRequest(self):
    return self.messages.ComputeUrlMapsGetRequest(
        urlMap='url-map-1', project='my-project')

  def _MakeExpectedUrlMapUpdateRequest(self, expected_url_map):
    return self.messages.ComputeUrlMapsUpdateRequest(
        urlMap='url-map-1',
        project='my-project',
        urlMapResource=expected_url_map)

  def testWithPathRules(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --description new
          --path-matcher-name my-matcher
          --path-rules /images/*=images-service
          --backend-service-path-rules /search=search-service,/search/*=search-service
          --backend-bucket-path-rules /static/*=static-bucket
          --new-hosts google.com
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'],
                                   pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(self._backend_services_uri_prefix +
                                'my-default-service'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(paths=['/images/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'images-service')),
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'search-service')),
                    self.messages.PathRule(paths=['/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                ],),
        ],)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testWithPathRulesBackendBucket(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunAddPathMatcher("""
        url-map-1
          --default-backend-bucket my-default-bucket
          --description new
          --path-matcher-name my-matcher
          --path-rules /images/*=images-service
          --backend-service-path-rules /search=search-service,/search/*=search-service
          --backend-bucket-path-rules /static/*=static-bucket
          --new-hosts google.com
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'],
                                   pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(self._backend_buckets_uri_prefix +
                                'my-default-bucket'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(paths=['/images/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'images-service')),
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'search-service')),
                    self.messages.PathRule(paths=['/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                ],),
        ],)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testWithNoNewHostsOrExistingHost(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --description new
          --path-matcher-name my-matcher
          --backend-service-path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          --backend-bucket-path-rules /static/*=static-bucket
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
            self.messages.HostRule(hosts=['*'],
                                   pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(self._backend_services_uri_prefix +
                                'my-default-service'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(paths=['/images/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'images-service')),
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'search-service')),
                    self.messages.PathRule(paths=['/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                ],),
        ],)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testUriSupport(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunAddPathMatcher("""
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-1
          --default-service https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-default-service
          --path-matcher-name my-matcher
          --backend-service-path-rules /search=https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search-service,/search/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search-service,/images/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/images-service
          --backend-bucket-path-rules /static/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/static-bucket
          --new-hosts google.com
        """ % {'api': self._api})

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'],
                                   pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(self._backend_services_uri_prefix +
                                'my-default-service'),
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(paths=['/images/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'images-service')),
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'search-service')),
                    self.messages.PathRule(paths=['/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                ],),
        ],)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testDefaultServiceOrDefaultBucketRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--default-backend-bucket | --default-service) '
        'must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --description new
            --path-matcher-name my-matcher
            --path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testDefaultServiceAndDefaultBucketInvalid(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --default-backend-bucket: Exactly one of '
        '(--default-backend-bucket | --default-service) must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --default-backend-bucket my-default-bucket
            --description new
            --path-matcher-name my-matcher
            --path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testPathMatcherNameRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path-matcher-name: Must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --description new
            --backend-service-path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testDeletionOfOrphanedPathMatcher(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --path-matcher-name my-matcher
          --existing-host youtube.com
          --delete-orphaned-path-matcher
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(defaultService=(
                self._backend_services_uri_prefix + 'my-default-service'),
                                      name='my-matcher'),
        ],)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testFailureWithOrphanedPathMatcher(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    with self.AssertRaisesToolExceptionRegexp(
        r'This operation will orphan the path matcher \[my-matcher\]. To '
        r'delete the orphan path matcher, rerun this command with '
        r'\[--delete-orphaned-path-matcher\] or use \[gcloud compute url-maps '
        r'edit\] to modify the URL map by hand.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --existing-host youtube.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)

  def testExistingHostWithNonExistentHost(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    with self.AssertRaisesToolExceptionRegexp(
        r'No host rule with host \[google.com\] exists. Check your spelling or '
        r'use \[--new-hosts\] to create a new host rule'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --existing-host google.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)

  def testNewHostsWithHostsThatAlreadyExist(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot create a new host rule with host \[\*.youtube.com\] because '
        r'the host is already part of a host rule that references the path '
        r'matcher \[youtube\].'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --new-hosts youtube.com,*.youtube.com,google.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)


class UrlMapsAddPathMatcherBetaTest(UrlMapsAddPathMatcherGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')

    self._url_maps_api = self.compute_beta.urlMaps

    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
        ],
    )

  def RunAddPathMatcher(self, command):
    self.Run('beta compute url-maps add-path-matcher --global' + command)


class UrlMapsAddPathMatcherAlphaTest(UrlMapsAddPathMatcherGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')

    self._url_maps_api = self.compute_alpha.urlMaps

    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        hostRules=[
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=
                                           (self._backend_services_uri_prefix +
                                            'youtube-search')),
                    self.messages.PathRule(paths=['/static', '/static/*'],
                                           service=
                                           (self._backend_buckets_uri_prefix +
                                            'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
        ],)

  def RunAddPathMatcher(self, command):
    self.Run('alpha compute url-maps add-path-matcher --global' + command)


class RegionUrlMapsAddPathMatcherBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._backend_services_uri_prefix = (
        self.compute_uri +
        '/projects/my-project/regions/us-west-1/backendServices/')
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')

    self._url_maps_api = self.compute_beta.regionUrlMaps

    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri +'/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    self._backend_services_uri_prefix + 'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
        ],
    )

  def _MakeExpectedUrlMapGetRequest(self):
    return self.messages.ComputeRegionUrlMapsGetRequest(
        urlMap='url-map-1', project='my-project', region='us-west-1')

  def _MakeExpectedUrlMapUpdateRequest(self, expected_url_map):
    return self.messages.ComputeRegionUrlMapsUpdateRequest(
        urlMap='url-map-1',
        project='my-project',
        urlMapResource=expected_url_map,
        region='us-west-1')

  def RunAddPathMatcher(self, command):
    self.Run('beta compute url-maps add-path-matcher --region us-west-1 ' +
             command)

  def testWithPathRules(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --description new
          --path-matcher-name my-matcher
          --path-rules /images/*=images-service
          --backend-service-path-rules /search=search-service,/search/*=search-service
          --backend-bucket-path-rules /static/*=static-bucket
          --new-hosts google.com
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                hosts=['google.com'], pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    self._backend_services_uri_prefix + 'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(
                    self._backend_services_uri_prefix + 'my-default-service'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/images/*'],
                        service=(self._backend_services_uri_prefix +
                                 'images-service')),
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'search-service')),
                    self.messages.PathRule(
                        paths=['/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                ],
            ),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testWithPathRulesBackendBucket(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunAddPathMatcher("""
        url-map-1
          --default-backend-bucket my-default-bucket
          --description new
          --path-matcher-name my-matcher
          --path-rules /images/*=images-service
          --backend-service-path-rules /search=search-service,/search/*=search-service
          --backend-bucket-path-rules /static/*=static-bucket
          --new-hosts google.com
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                hosts=['google.com'], pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    self._backend_services_uri_prefix + 'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(
                    self._backend_buckets_uri_prefix + 'my-default-bucket'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/images/*'],
                        service=(self._backend_services_uri_prefix +
                                 'images-service')),
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'search-service')),
                    self.messages.PathRule(
                        paths=['/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                ],
            ),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testWithNoNewHostsOrExistingHost(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --description new
          --path-matcher-name my-matcher
          --backend-service-path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          --backend-bucket-path-rules /static/*=static-bucket
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(hosts=['*'], pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    self._backend_services_uri_prefix + 'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(
                    self._backend_services_uri_prefix + 'my-default-service'),
                description='new',
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/images/*'],
                        service=(self._backend_services_uri_prefix +
                                 'images-service')),
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'search-service')),
                    self.messages.PathRule(
                        paths=['/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                ],
            ),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunAddPathMatcher("""
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/url-map-1
          --default-service https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/my-default-service
          --path-matcher-name my-matcher
          --backend-service-path-rules /search=https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/search-service,/search/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/search-service,/images/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/images-service
          --backend-bucket-path-rules /static/*=https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/static-bucket
          --new-hosts google.com
        """ % {'api': self._api})

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
            self.messages.HostRule(
                hosts=['google.com'], pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    self._backend_services_uri_prefix + 'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
            self.messages.PathMatcher(
                defaultService=(
                    self._backend_services_uri_prefix + 'my-default-service'),
                name='my-matcher',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/images/*'],
                        service=(self._backend_services_uri_prefix +
                                 'images-service')),
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'search-service')),
                    self.messages.PathRule(
                        paths=['/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                ],
            ),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testDefaultServiceOrDefaultBucketRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--default-backend-bucket | --default-service) '
        'must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --description new
            --path-matcher-name my-matcher
            --path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testDefaultServiceAndDefaultBucketInvalid(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --default-backend-bucket: Exactly one of '
        '(--default-backend-bucket | --default-service) must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --default-backend-bucket my-default-bucket
            --description new
            --path-matcher-name my-matcher
            --path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testPathMatcherNameRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path-matcher-name: Must be specified.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --description new
            --backend-service-path-rules /search=search-service,/search/*=search-service,/images/*=images-service
          """)

    self.CheckRequests()

  def testDeletionOfOrphanedPathMatcher(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    self.RunAddPathMatcher("""
        url-map-1
          --default-service my-default-service
          --path-matcher-name my-matcher
          --existing-host youtube.com
          --delete-orphaned-path-matcher
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='my-matcher'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                defaultService=(
                    self._backend_services_uri_prefix + 'my-default-service'),
                name='my-matcher'),
        ],
    )

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],
        [(self._url_maps_api, 'Update',
          self._MakeExpectedUrlMapUpdateRequest(expected_url_map))])

  def testFailureWithOrphanedPathMatcher(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'This operation will orphan the path matcher \[my-matcher\]. To '
        r'delete the orphan path matcher, rerun this command with '
        r'\[--delete-orphaned-path-matcher\] or use \[gcloud compute url-maps '
        r'edit\] to modify the URL map by hand.'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --existing-host youtube.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)

  def testExistingHostWithNonExistentHost(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No host rule with host \[google.com\] exists. Check your spelling or '
        r'use \[--new-hosts\] to create a new host rule'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --existing-host google.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)

  def testNewHostsWithHostsThatAlreadyExist(self):
    self.make_requests.side_effect = iter([
        [self._url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot create a new host rule with host \[\*.youtube.com\] because '
        r'the host is already part of a host rule that references the path '
        r'matcher \[youtube\].'):
      self.RunAddPathMatcher("""
          url-map-1
            --default-service my-default-service
            --path-matcher-name my-matcher
            --new-hosts youtube.com,*.youtube.com,google.com
          """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get', self._MakeExpectedUrlMapGetRequest())],)


class RegionUrlMapsAddPathMatcherAlphaTest(RegionUrlMapsAddPathMatcherBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._backend_services_uri_prefix = (
        self.compute_uri +
        '/projects/my-project/regions/us-west-1/backendServices/')
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')

    self._url_maps_api = self.compute_alpha.regionUrlMaps

    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',
        region=self.compute_uri + '/projects/my-project/regions/us-west-1',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(self._backend_services_uri_prefix +
                                'youtube-default'),
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/static', '/static/*'],
                        service=(self._backend_buckets_uri_prefix +
                                 'static-bucket')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=(self._backend_services_uri_prefix +
                                 'youtube-watch')),
                ]),
        ],
    )

  def RunAddPathMatcher(self, command):
    self.Run('alpha compute url-maps add-path-matcher --region us-west-1 ' +
             command)


if __name__ == '__main__':
  test_case.main()
