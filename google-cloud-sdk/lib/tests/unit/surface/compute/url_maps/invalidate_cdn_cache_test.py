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
import textwrap

from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock

messages = apis.GetMessagesModule('compute', 'v1')

INVALIDATION = messages.Operation(
    name='operation-1',
    status=messages.Operation.StatusValueValuesEnum.DONE,
    operationType='invalidateCache',
    insertTime='2014-09-04T09:55:33.679-07:00',
    description='/oops/*',
    targetId=12345,
    targetLink='http://example.com/target',
    selfLink='http://example.com/self')


class UrlMapsInvalidateCacheTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute url-maps invalidate-cdn-cache my-url-map --path /oops.html
        """)

    self.CheckRequests([(
        self.compute.urlMaps, 'InvalidateCache',
        self.messages.ComputeUrlMapsInvalidateCacheRequest(
            project='my-project',
            urlMap='my-url-map',
            cacheInvalidationRule=self.messages.CacheInvalidationRule(
                path='/oops.html')))])

  def testWithoutPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'
        ):
      self.Run("""
          compute url-maps invalidate-cdn-cache my-url-map
          """)
    self.CheckRequests()

  def testBogusPath(self):
    error_msg = 'path must begin with /'
    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((400, error_msg))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.Run("""
          compute url-maps invalidate-cdn-cache my-url-map
              --path http://bogus/path
          """)

    self.CheckRequests([(
        self.compute.urlMaps, 'InvalidateCache',
        self.messages.ComputeUrlMapsInvalidateCacheRequest(
            project='my-project',
            urlMap='my-url-map',
            cacheInvalidationRule=self.messages.CacheInvalidationRule(
                path='http://bogus/path')))])

  def testHostInvalidation(self):
    self.Run("""
        compute url-maps invalidate-cdn-cache my-url-map
             --path /oops.html --host oops.com
        """)

    self.CheckRequests([(
        self.compute.urlMaps, 'InvalidateCache',
        self.messages.ComputeUrlMapsInvalidateCacheRequest(
            project='my-project',
            urlMap='my-url-map',
            cacheInvalidationRule=self.messages.CacheInvalidationRule(
                path='/oops.html', host='oops.com')))])


class UrlMapsInvalidateCacheAsyncTest(test_base.BaseTest):

  def SetUp(self):
    make_batch_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_batch_requests_patcher.stop)
    self.make_batch_requests = make_batch_requests_patcher.start()
    self.make_batch_requests.side_effect = iter([([], [])])

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
    self.make_batch_requests.side_effect = iter([([INVALIDATION], [])])
    self.Run("""
        compute url-maps invalidate-cdn-cache my-url-map --path /oops.html
             --async
        """)
    self.CheckBatchRequests([(
        self.compute.urlMaps, 'InvalidateCache',
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
      self.Run("""
          compute url-maps invalidate-cdn-cache my-url-map --async
          """)
    self.CheckBatchRequests()

  def testBogusPath(self):
    error_msg = 'path must begin with /'
    self.make_batch_requests.side_effect = iter([([], [(400, error_msg)])])

    with self.AssertRaisesToolExceptionRegexp(error_msg):
      self.Run("""
          compute url-maps invalidate-cdn-cache my-url-map
              --path http://bogus/path --async
          """)

    self.CheckBatchRequests([(
        self.compute.urlMaps, 'InvalidateCache',
        self.messages.ComputeUrlMapsInvalidateCacheRequest(
            project='my-project',
            urlMap='my-url-map',
            cacheInvalidationRule=self.messages.CacheInvalidationRule(
                path='http://bogus/path')))])

  def testHostInvalidation(self):
    self.make_batch_requests.side_effect = iter([([INVALIDATION], [])])
    self.Run("""
        compute url-maps invalidate-cdn-cache my-url-map --path /oops.html
             --host oops.com --async
        """)
    self.CheckBatchRequests([(
        self.compute.urlMaps, 'InvalidateCache',
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
