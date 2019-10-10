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
"""Tests for the url-maps remove-host-rule subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UrlMapsRemoveHostRuleTest(test_base.BaseTest):

  _V1_URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def RunRemoveHostRule(self, command):
    self.Run('compute url-maps remove-host-rule ' + command)

  def SetUp(self):
    self._collection = self.compute_v1.urlMaps

    self.url_map = self.messages.UrlMap(
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

  def testWithNoOrphaningOfPathMatchers(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunRemoveHostRule('url-map-1 --host *-youtube.com')

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
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

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))],
                       [(self._collection, 'Update',
                         self.messages.ComputeUrlMapsUpdateRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             urlMapResource=expected_url_map))])

  def testWithOrphaningOfPathMatcherAndDeleteOrphanedPathMatcherOption(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunRemoveHostRule("""url-map-1
        --host google.com
        --delete-orphaned-path-matcher
    """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
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
                        service=(self._BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-watch'),
                ]),
        ],
    )

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))],
                       [(self._collection, 'Update',
                         self.messages.ComputeUrlMapsUpdateRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             urlMapResource=expected_url_map))])

  def testWithOrphaningOfPathMatcherAndNoDeleteOrphanedPathMatcherOption(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'This operation will orphan the path matcher \[youtube\]. To delete '
        r'the orphan path matcher, rerun this command with '
        r'\[--delete-orphaned-path-matcher\] or use \[gcloud compute url-maps '
        r'edit\] to modify the URL map by hand.'):
      self.RunRemoveHostRule('url-map-1 --host google.com')

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))])

  def testWithNonExistentHost(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No host rule contains the host \[goooooogle.com\].'):
      self.RunRemoveHostRule('url-map-1 --host goooooogle.com')

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             urlMap='url-map-1', project='my-project'))])


class UrlMapsRemoveHostRuleBetaTest(UrlMapsRemoveHostRuleTest):

  _V1_URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def SetUp(self):
    self.SelectApi('beta')
    self._collection = self.compute_beta.urlMaps

    self.url_map = self.messages.UrlMap(
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

  def RunRemoveHostRule(self, command):
    self.Run('beta compute url-maps remove-host-rule --global ' + command)


class UrlMapsRemoveHostRuleAlphaTest(UrlMapsRemoveHostRuleTest):

  _V1_URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def SetUp(self):
    self.SelectApi('alpha')
    self._collection = self.compute_alpha.urlMaps

    self.url_map = self.messages.UrlMap(
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

  def RunRemoveHostRule(self, command):
    self.Run('alpha compute url-maps remove-host-rule --global ' + command)


class RegionUrlMapsRemoveHostRuleBetaTest(test_base.BaseTest):

  _V1_URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def RunRemoveHostRule(self, command):
    self.Run('beta compute url-maps remove-host-rule --region us-west1 ' +
             command)

  def SetUp(self):
    self.SelectApi('beta')
    self._collection = self.compute_beta.regionUrlMaps

    self.url_map = self.messages.UrlMap(
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

  def testWithNoOrphaningOfPathMatchers(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunRemoveHostRule('url-map-1 --host *-youtube.com')

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
            self.messages.HostRule(hosts=['google.com'], pathMatcher='google'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='youtube',
                defaultService=self._BACKEND_SERVICES_URI_PREFIX +
                'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=(self._BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
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

    self.CheckRequests(
        [(self._collection, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              urlMap='url-map-1', project='my-project', region='us-west1'))],
        [(self._collection, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              region='us-west1',
              urlMapResource=expected_url_map))])

  def testWithOrphaningOfPathMatcherAndDeleteOrphanedPathMatcherOption(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunRemoveHostRule("""url-map-1
        --host google.com
        --delete-orphaned-path-matcher
    """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._BACKEND_SERVICES_URI_PREFIX + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com'], pathMatcher='youtube'),
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
                        service=(self._BACKEND_SERVICES_URI_PREFIX +
                                 'youtube-search')),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=self._BACKEND_SERVICES_URI_PREFIX +
                        'youtube-watch'),
                ]),
        ],
    )

    self.CheckRequests(
        [(self._collection, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              urlMap='url-map-1', project='my-project', region='us-west1'))],
        [(self._collection, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              region='us-west1',
              urlMapResource=expected_url_map))])

  def testWithOrphaningOfPathMatcherAndNoDeleteOrphanedPathMatcherOption(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'This operation will orphan the path matcher \[youtube\]. To delete '
        r'the orphan path matcher, rerun this command with '
        r'\[--delete-orphaned-path-matcher\] or use \[gcloud compute url-maps '
        r'edit\] to modify the URL map by hand.'):
      self.RunRemoveHostRule('url-map-1 --host google.com')

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             region='us-west1'))])

  def testWithNonExistentHost(self):
    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No host rule contains the host \[goooooogle.com\].'):
      self.RunRemoveHostRule('url-map-1 --host goooooogle.com')

    self.CheckRequests([(self._collection, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             urlMap='url-map-1',
                             project='my-project',
                             region='us-west1'))])


class RegionUrlMapsRemoveHostRuleAlphaTest(RegionUrlMapsRemoveHostRuleBetaTest):

  _V1_URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
  _BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'

  def RunRemoveHostRule(self, command):
    self.Run('alpha compute url-maps remove-host-rule --region us-west1 ' +
             command)

  def SetUp(self):
    self.SelectApi('alpha')
    self._collection = self.compute_alpha.regionUrlMaps

    self.url_map = self.messages.UrlMap(
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


if __name__ == '__main__':
  test_case.main()
