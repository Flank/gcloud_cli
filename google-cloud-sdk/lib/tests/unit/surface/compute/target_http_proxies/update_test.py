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
"""Tests for the target-http-proxies update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHTTPProxiesUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_v1.targetHttpProxies

  def RunUpdate(self, command):
    self.Run('compute target-http-proxies update ' + command)

  def testSimpleCase(self):
    self.RunUpdate('target-http-proxy-1 --url-map my-map')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'SetUrlMap',
          self.messages.ComputeTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=self.messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/global/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

  def testUriSupport(self):
    self.RunUpdate("""
          https://www.googleapis.com/compute/%(api)s/projects/my-project/global/targetHttpProxies/target-http-proxy-1
          --url-map https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-map
        """ % {'api': self._api})

    self.CheckRequests(
        [(self._target_http_proxies_api, 'SetUrlMap',
          self.messages.ComputeTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=self.messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/global/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.RunUpdate('my-proxy')

    self.CheckRequests()


class TargetHTTPProxiesUpdateAlphaTest(TargetHTTPProxiesUpdateTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.targetHttpProxies

  def RunUpdate(self, command):
    self.Run('alpha compute target-http-proxies update --global ' + command)


class RegionTargetHTTPProxiesUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.regionTargetHttpProxies

  def RunUpdate(self, command):
    self.Run('alpha compute target-http-proxies update --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.RunUpdate('target-http-proxy-1 --url-map my-map')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'SetUrlMap',
          self.messages.ComputeRegionTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              region='us-west-1',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=self.messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/regions/us-west-1/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

  def testUriSupport(self):
    self.RunUpdate("""
          https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/targetHttpProxies/target-http-proxy-1
          --url-map https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west-1/urlMaps/my-map
        """ % {'api': self._api})

    self.CheckRequests(
        [(self._target_http_proxies_api, 'SetUrlMap',
          self.messages.ComputeRegionTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              region='us-west-1',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=self.messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/%(api)s/projects/'
                          'my-project/regions/us-west-1/urlMaps/my-map' % {
                              'api': self._api
                          }))))],)

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.RunUpdate('my-proxy')

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
