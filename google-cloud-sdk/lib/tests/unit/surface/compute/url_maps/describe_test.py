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
import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


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
            defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
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
            - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
              name: www
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
              - paths:
                - /search/ads
                - /search/ads/*
                service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
              - paths:
                - /images
                service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/images
            - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
              name: youtube
              pathRules:
              - paths:
                - /search
                - /search/*
                service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
              - paths:
                - /watch
                - /view
                - /preview
                service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
            selfLink: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-1
            tests:
            - host: www.google.com
              path: /search/ads/inline?q=flowers
              service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
            - host: youtube.com
              path: /watch/this
              service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
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
            defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/default-bucket
            name: url-map-4
            selfLink: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-4
            """ % {'api': self._api}))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.URL_MAPS)
    uri_list = [
        'url-map-2',
        'url-map-4',
        'url-map-1',
        'url-map-3',
    ]
    self.RunCompletion('compute url-maps describe ', uri_list)


class URLMapsDescribeBetaTest(URLMapsDescribeTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.urlMaps
    self._url_maps = test_resources.URL_MAPS_BETA

  def RunDescribe(self, command):
    self.Run('beta compute url-maps describe ' + command)


class URLMapsDescribeAlphaTest(URLMapsDescribeTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.urlMaps
    self._url_maps = test_resources.URL_MAPS_ALPHA

  def RunDescribe(self, command):
    self.Run('alpha compute url-maps describe ' + command)


if __name__ == '__main__':
  test_case.main()
