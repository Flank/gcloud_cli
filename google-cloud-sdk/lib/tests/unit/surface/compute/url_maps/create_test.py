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
"""Tests for the url-maps create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class URLMapsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._url_maps_api = self.compute_v1.urlMaps

  def RunCreate(self, command):
    self.Run('compute url-maps create ' + command)

  def testSimpleBackendServiceCase(self):
    self.RunCreate("""
        my-url-map
          --default-service my-service
        """)

    self.CheckRequests(
        [(self._url_maps_api,
          'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-service') % {
                          'api': self._api},
                  name='my-url-map')))],
    )

  def testSimpleBackendBucketCase(self):
    self.RunCreate("""
        my-url-map
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api,
          'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
                  name='my-url-map')))],
    )

  def testBackendBucketWithDescription(self):
    self.RunCreate("""
        my-url-map
          --description "My URL map"
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api,
          'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
                  description='My URL map',
                  name='my-url-map')))],
    )

  def testWithoutDefaultServiceOrBucket(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--default-backend-bucket | --default-service) '
        'must be specified.'):
      self.RunCreate("""
          my-url-map
          """)

    self.CheckRequests()

  def testWithDefaultServiceAndDefaultBucket(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --default-backend-bucket: Exactly one of '
        '(--default-backend-bucket | --default-service) must be specified.'):
      self.RunCreate("""
          my-url-map
            --default-backend-bucket my-backend-bucket
            --default-service my-service
          """)

    self.CheckRequests()

  def testUriSupportBackendService(self):
    self.RunCreate("""
        https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
          --default-service https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-service
        """ % {'api': self._api})

    self.CheckRequests(
        [(self._url_maps_api,
          'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-service') % {
                          'api': self._api},
                  name='my-url-map')))],
    )

  def testUriSupportBackendBucket(self):
    self.RunCreate("""
        https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
          --default-backend-bucket https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        """ % {'api': self._api})

    self.CheckRequests(
        [(self._url_maps_api,
          'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
                  name='my-url-map')))],
    )


class URLMapsCreateAlphaTest(URLMapsCreateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.urlMaps

  def RunCreate(self, command):
    self.Run('alpha compute url-maps create ' + command)


class URLMapsCreateBetaTest(URLMapsCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.urlMaps

  def RunCreate(self, command):
    self.Run('beta compute url-maps create ' + command)


if __name__ == '__main__':
  test_case.main()
