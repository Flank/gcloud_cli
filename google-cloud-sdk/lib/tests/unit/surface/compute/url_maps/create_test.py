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
"""Tests for the url-maps create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class URLMapsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = ''
    self._url_maps_api = self.compute_v1.urlMaps
    self._region_name = 'us-west-1'

  def RunCreate(self, command):
    self.Run(self._api + ' compute url-maps create ' + command)

  def testSimpleBackendServiceCase(self):
    self.RunCreate("""
        my-url-map
          --default-service my-service
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-service') %
                  {'api': self.api},
                  name='my-url-map')))],)

  def testSimpleBackendBucketCase(self):
    self.RunCreate("""
        my-url-map
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  name='my-url-map')))],)

  def testBackendBucketWithDescription(self):
    self.RunCreate("""
        my-url-map
          --description "My URL map"
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  description='My URL map',
                  name='my-url-map')))],)

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
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
          --default-service https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-service
        """ % {'api': self.api})

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-service') %
                  {'api': self.api},
                  name='my-url-map')))],)

  def testUriSupportBackendBucket(self):
    self.RunCreate("""
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
          --default-backend-bucket https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        """ % {'api': self.api})

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeUrlMapsInsertRequest(
              project='my-project',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  name='my-url-map')))],)


class URLMapsCreateBetaTest(URLMapsCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.urlMaps


class URLMapsCreateAlphaTest(URLMapsCreateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.urlMaps


class RegionURLMapsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = ''
    self._url_maps_api = self.compute_v1.regionUrlMaps

  def RunCreate(self, command):
    self.Run(self._api + ' compute url-maps create --region us-west-1 ' +
             command)

  def testSimpleBackendServiceCase(self):
    self.RunCreate("""
        my-url-map
          --default-service my-service
        """)

    self.CheckRequests([(
        self._url_maps_api, 'Insert',
        self.messages.ComputeRegionUrlMapsInsertRequest(
            project='my-project',
            region='us-west-1',
            urlMap=self.messages.UrlMap(
                defaultService=(
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west-1/backendServices/my-service') %
                {'api': self.api},
                name='my-url-map')))],)

  def testSimpleBackendBucketCase(self):
    self.RunCreate("""
        my-url-map
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeRegionUrlMapsInsertRequest(
              project='my-project',
              region='us-west-1',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  name='my-url-map')))],)

  def testBackendBucketWithDescription(self):
    self.RunCreate("""
        my-url-map
          --description "My URL map"
          --default-backend-bucket my-backend-bucket
        """)

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeRegionUrlMapsInsertRequest(
              project='my-project',
              region='us-west-1',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  description='My URL map',
                  name='my-url-map')))],)

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
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/my-url-map
          --default-service https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/backendServices/my-service
        """ % {'api': self.api})

    self.CheckRequests([(
        self._url_maps_api, 'Insert',
        self.messages.ComputeRegionUrlMapsInsertRequest(
            project='my-project',
            region='us-west-1',
            urlMap=self.messages.UrlMap(
                defaultService=(
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west-1/backendServices/my-service') %
                {'api': self.api},
                name='my-url-map')))],)

  def testUriSupportBackendBucket(self):
    self.RunCreate("""
        https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/my-url-map
          --default-backend-bucket https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        """ % {'api': self.api})

    self.CheckRequests(
        [(self._url_maps_api, 'Insert',
          self.messages.ComputeRegionUrlMapsInsertRequest(
              project='my-project',
              region='us-west-1',
              urlMap=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
                  name='my-url-map')))],)


class RegionURLMapsCreateBetaTest(RegionURLMapsCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.regionUrlMaps


class RegionURLMapsCreateAlphaTest(RegionURLMapsCreateBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.regionUrlMaps


if __name__ == '__main__':
  test_case.main()
