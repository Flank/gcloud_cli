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
"""Tests for the url-maps invalidate-cdn-cache subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock


class UrlMapsInvalidateCacheTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._url_maps_api = self.compute.urlMaps

  def RunInvalidateCache(self, command):
    self.Run('compute url-maps invalidate-cdn-cache ' + command)

  def testSimpleCase(self):
    self.RunInvalidateCache('my-url-map --path /oops.html')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html')))])

  def testWithoutPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'):
      self.RunInvalidateCache('my-url-map')
    self.CheckRequests()

  def testBogusPath(self):
    error_msg = 'path must begin with /'

    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((400, error_msg))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.RunInvalidateCache('my-url-map --path http://bogus/path')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='http://bogus/path')))])

  def testHostInvalidation(self):
    self.RunInvalidateCache('my-url-map --path /oops.html --host oops.com')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html', host='oops.com')))])


class UrlMapsInvalidateCacheAlphaTest(UrlMapsInvalidateCacheTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute_alpha.urlMaps

  def RunInvalidateCache(self, command):
    self.Run('alpha compute url-maps invalidate-cdn-cache --global ' + command)


class RegionUrlMapsInvalidateCacheTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute.regionUrlMaps

  def RunInvalidateCache(self, command):
    self.Run('alpha compute url-maps invalidate-cdn-cache --region us-west-1 ' +
             command)

  def testSimpleCase(self):
    self.RunInvalidateCache('my-url-map --path /oops.html')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeRegionUrlMapsInvalidateCacheRequest(
              project='my-project',
              region='us-west-1',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html')))])

  def testWithoutPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'):
      self.RunInvalidateCache('my-url-map')
    self.CheckRequests()

  def testBogusPath(self):
    error_msg = 'path must begin with /'

    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((400, error_msg))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.RunInvalidateCache('my-url-map --path http://bogus/path')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeRegionUrlMapsInvalidateCacheRequest(
              project='my-project',
              region='us-west-1',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='http://bogus/path')))])

  def testHostInvalidation(self):
    self.RunInvalidateCache('my-url-map --path /oops.html --host oops.com')

    self.CheckRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeRegionUrlMapsInvalidateCacheRequest(
              project='my-project',
              region='us-west-1',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html', host='oops.com')))])


class UrlMapsInvalidateCacheAsyncTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._url_maps_api = self.compute.urlMaps
    make_batch_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_batch_requests_patcher.stop)
    self.make_batch_requests = make_batch_requests_patcher.start()
    self.make_batch_requests.side_effect = iter([([], [])])
    self.invalidation = self.messages.Operation(
        name='operation-1',
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        operationType='invalidateCache',
        insertTime='2014-09-04T09:55:33.679-07:00',
        description='/oops/*',
        targetId=12345,
        targetLink='http://example.com/target',
        selfLink='http://example.com/self')

  def RunInvalidateCache(self, command):
    self.Run('compute url-maps invalidate-cdn-cache --async ' + command)

  def CheckBatchRequests(self, *request_sets):
    """Ensures that the given requests were made to the server."""
    expected_calls = []
    for requests in request_sets:
      expected_calls.append(mock.call(requests=requests,
                                      http=self.mock_http(),
                                      batch_url=self.batch_url))
    self.AssertEqual(expected=expected_calls,
                     actual=self.make_batch_requests.call_args_list)

  def testSimpleCase(self):
    self.make_batch_requests.side_effect = iter([([self.invalidation], [])])
    self.RunInvalidateCache('my-url-map --path /oops.html')
    self.CheckBatchRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html')))])

    self.AssertErrEquals(
        textwrap.dedent("""\
            Invalidation pending for [http://example.com/target]
            Monitor its progress at [http://example.com/self]
            """))

  def testWithoutPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'
        ):
      self.RunInvalidateCache('my-url-map')
    self.CheckBatchRequests()

  def testBogusPath(self):
    error_msg = 'path must begin with /'
    self.make_batch_requests.side_effect = iter([([], [(400, error_msg)])])

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.RunInvalidateCache('my-url-map --path http://bogus/path')

    self.CheckBatchRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='http://bogus/path')))])

  def testHostInvalidation(self):
    self.make_batch_requests.side_effect = iter([([self.invalidation], [])])
    self.RunInvalidateCache('my-url-map --path /oops.html --host oops.com')

    self.CheckBatchRequests(
        [(self._url_maps_api, 'InvalidateCache',
          self.messages.ComputeUrlMapsInvalidateCacheRequest(
              project='my-project',
              urlMap='my-url-map',
              cacheInvalidationRule=self.messages.CacheInvalidationRule(
                  path='/oops.html', host='oops.com')))])

    self.AssertErrEquals(
        textwrap.dedent("""\
            Invalidation pending for [http://example.com/target]
            Monitor its progress at [http://example.com/self]
            """))


if __name__ == '__main__':
  test_case.main()
