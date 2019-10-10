# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Data Catalog crawler util tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.data_catalog.crawlers import util
from tests.lib import parameterized
from tests.lib import test_case


class CrawlersTest(test_case.TestCase, parameterized.TestCase):
  """Data Catalog crawler tests class."""

  def SetUp(self):
    self.messages = apis.GetMessagesModule('datacatalog', 'v1alpha3')

  def testSetRunOptionInRequest(self):
    request = self.messages.DatacatalogProjectsCrawlersPatchRequest(
        googleCloudDatacatalogV1alpha3Crawler=None)

    manual = util._SetRunOptionInRequest('manual', None, request, self.messages)
    self.assertEqual(
        manual.googleCloudDatacatalogV1alpha3Crawler.config.adHocRun,
        self.messages.GoogleCloudDatacatalogV1alpha3AdhocRun())

    daily = util._SetRunOptionInRequest(
        'scheduled', 'daily', request, self.messages)
    self.assertEqual(
        daily.googleCloudDatacatalogV1alpha3Crawler.config.scheduledRun,
        self.messages.GoogleCloudDatacatalogV1alpha3ScheduledRun(
            scheduledRunOption=(self.messages.
                                GoogleCloudDatacatalogV1alpha3ScheduledRun.
                                ScheduledRunOptionValueValuesEnum.DAILY)))

    weekly = util._SetRunOptionInRequest(
        'scheduled', 'weekly', request, self.messages)
    self.assertEqual(
        weekly.googleCloudDatacatalogV1alpha3Crawler.config.scheduledRun,
        self.messages.GoogleCloudDatacatalogV1alpha3ScheduledRun(
            scheduledRunOption=(self.messages.
                                GoogleCloudDatacatalogV1alpha3ScheduledRun.
                                ScheduledRunOptionValueValuesEnum.WEEKLY)))

  @parameterized.parameters(
      ('project', None, 'projectScope'),
      ('organization', None, 'organizationScope'),
      ('bucket', ['gs://bucket1', 'gs://bucket2'], 'bucketScope')
  )
  def testSetScopeInRequest(self, crawl_scope, bucket_names, scope_field):
    request = self.messages.DatacatalogProjectsCrawlersPatchRequest(
        googleCloudDatacatalogV1alpha3Crawler=None)
    buckets = [self.messages.GoogleCloudDatacatalogV1alpha3BucketSpec(bucket=b)
               for b in bucket_names] if bucket_names else None
    request = util._SetScopeInRequest(
        crawl_scope, buckets, request, self.messages)
    self.assertIsNotNone(
        request.googleCloudDatacatalogV1alpha3Crawler.config.field_by_name(
            scope_field))

  def testSetScopeInRequestNoBuckets(self):
    request = self.messages.DatacatalogProjectsCrawlersPatchRequest(
        googleCloudDatacatalogV1alpha3Crawler=None)
    with self.assertRaisesRegex(
        util.InvalidCrawlScopeError,
        'At least one bucket must be included in the crawl scope of a '
        'bucket-scoped crawler.'):
      util._SetScopeInRequest('bucket', [], request, self.messages)


if __name__ == '__main__':
  test_case.main()
