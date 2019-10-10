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
"""Tests for the url-maps list-cdn-cache-invalidations subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'beta')


INVALIDATION = messages.Operation(
    name='operation-1',
    status=messages.Operation.StatusValueValuesEnum.DONE,
    operationType='invalidateCache',
    insertTime='2014-09-04T09:55:33.679-07:00',
    description='/hello/*',
    targetId=12345,
)

URL_MAP = messages.UrlMap(
    id=12345,
    name='url-map',
)

EXPECTED_FILTER_EXPR = '(operationType eq invalidateCache) (targetId eq 12345)'


class UrlMapsListCacheInvalidationsTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[URL_MAP], [INVALIDATION]])

    self.Run("""
        beta compute url-maps list-cdn-cache-invalidations url-map
        --region us-west1
        """)

    self.CheckRequests(
        [(self.compute_beta.regionUrlMaps, 'Get',
          messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='url-map', region='us-west1'))],
        [(self.compute_beta.globalOperations, 'AggregatedList',
          messages.ComputeGlobalOperationsAggregatedListRequest(
              filter=EXPECTED_FILTER_EXPR,
              maxResults=500,
              orderBy='creationTimestamp desc',
              project='my-project'))])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            DESCRIPTION HTTP_STATUS STATUS TIMESTAMP
            /hello/*    200         DONE   2014-09-04T09:55:33.679-07:00
            """), normalize_space=True)

  def testLimit(self):
    self.make_requests.side_effect = iter([[URL_MAP], [INVALIDATION]])

    self.Run("""
        beta compute url-maps list-cdn-cache-invalidations url-map --limit 10
        --global
        """)

    self.CheckRequests(
        [(self.compute_beta.urlMaps, 'Get',
          messages.ComputeUrlMapsGetRequest(project='my-project',
                                            urlMap='url-map'))],
        [(self.compute_beta.globalOperations, 'AggregatedList',
          messages.ComputeGlobalOperationsAggregatedListRequest(
              filter=EXPECTED_FILTER_EXPR,
              maxResults=10,
              orderBy='creationTimestamp desc',
              project='my-project'))])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            DESCRIPTION HTTP_STATUS STATUS TIMESTAMP
            /hello/*    200         DONE   2014-09-04T09:55:33.679-07:00
            """), normalize_space=True)


class UrlMapsListCacheInvalidationsAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[URL_MAP], [INVALIDATION]])

    self.Run("""
        alpha compute url-maps list-cdn-cache-invalidations url-map
        --region us-west1
        """)

    self.CheckRequests(
        [(self.compute_alpha.regionUrlMaps, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='url-map', region='us-west1'))],
        [(self.compute_alpha.globalOperations, 'AggregatedList',
          self.messages.ComputeGlobalOperationsAggregatedListRequest(
              filter=EXPECTED_FILTER_EXPR,
              maxResults=500,
              orderBy='creationTimestamp desc',
              project='my-project'))])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            DESCRIPTION HTTP_STATUS STATUS TIMESTAMP
            /hello/*    200         DONE   2014-09-04T09:55:33.679-07:00
            """),
        normalize_space=True)

  def testLimit(self):
    self.make_requests.side_effect = iter([[URL_MAP], [INVALIDATION]])

    self.Run("""
        alpha compute url-maps list-cdn-cache-invalidations url-map --limit 10
        --global
        """)

    self.CheckRequests(
        [(self.compute_alpha.urlMaps, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='url-map'))],
        [(self.compute_alpha.globalOperations, 'AggregatedList',
          self.messages.ComputeGlobalOperationsAggregatedListRequest(
              filter=EXPECTED_FILTER_EXPR,
              maxResults=10,
              orderBy='creationTimestamp desc',
              project='my-project'))])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            DESCRIPTION HTTP_STATUS STATUS TIMESTAMP
            /hello/*    200         DONE   2014-09-04T09:55:33.679-07:00
            """),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
