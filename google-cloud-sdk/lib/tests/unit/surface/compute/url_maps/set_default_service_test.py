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
"""Tests for the url-maps set-default-service subcommand."""

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UrlMapsSetDefaultServiceTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._url_maps_api = self.compute_v1.urlMaps
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',)

  def RunSetDefaultService(self, command):
    self.Run('compute url-maps set-default-service ' + command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunSetDefaultService("""
        url-map-1
          --default-service new-service
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_services_uri_prefix + 'new-service',)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(urlMap='url-map-1',
                                                 project='my-project'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              urlMapResource=expected_url_map))])

  def testNoChangeCase(self):
    self.make_requests.side_effect = [[self._url_map],]

    self.RunSetDefaultService("""
        url-map-1
          --default-backend-bucket default-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(urlMap='url-map-1',
                                                 project='my-project'))],
        )

    self.AssertErrEquals(
        'No change requested; skipping update for [url-map-1].\n',
        normalize_space=True)

  def testSimpleBackendBucketCase(self):
    self.make_requests.side_effect = iter([[self._url_map], [],])

    self.RunSetDefaultService("""
        url-map-1
          --default-backend-bucket new-bucket
        """)

    expected_url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'new-bucket',)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(urlMap='url-map-1',
                                                 project='my-project'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              urlMap='url-map-1',
              project='my-project',
              urlMapResource=expected_url_map))])

  def testDefaultServiceOrDefaultBackendBucketIsRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--default-backend-bucket | --default-service) '
        'must be specified.'):
      self.RunSetDefaultService("""
          url-map-1
          """)

    self.CheckRequests()

  def testBothDefaultServiceAndDefaultBackendBucket(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --default-backend-bucket: Exactly one of '
        '(--default-backend-bucket | --default-service) must be specified.'):
      self.RunSetDefaultService("""
          url-map-1
            --default-backend-bucket new-bucket
            --default-service new-service
          """)

    self.CheckRequests()


class UrlMapsSetDefaultServiceAlphaTest(UrlMapsSetDefaultServiceTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute_alpha.urlMaps
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',)

  def RunSetDefaultService(self, command):
    self.Run('alpha compute url-maps set-default-service ' + command)


class UrlMapsSetDefaultServiceBetaTest(UrlMapsSetDefaultServiceTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._url_maps_api = self.compute_beta.urlMaps
    self._backend_buckets_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendBuckets/')
    self._backend_services_uri_prefix = (
        self.compute_uri + '/projects/my-project/global/backendServices/')
    self._url_map = self.messages.UrlMap(
        name='url-map-1',
        defaultService=self._backend_buckets_uri_prefix + 'default-bucket',)

  def RunSetDefaultService(self, command):
    self.Run('beta compute url-maps set-default-service ' + command)


if __name__ == '__main__':
  test_case.main()
