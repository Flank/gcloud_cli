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
"""Tests for `gcloud web-security-scanner scan-runs list-crawled-urls`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class ScanRunsListCrawledUrlsTestAlpha(base.WebSecurityScannerScanRunsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    # When user_output_enabled is false, return value of self.Run() is a list
    # of crawled urls.
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListCrawledUrls(self):
    crawled_urls = self.makeCrawledUrls(10)
    self.client.projects_scanConfigs_scanRuns_crawledUrls.List.Expect(
        self.messages
        .WebsecurityscannerProjectsScanConfigsScanRunsCrawledUrlsListRequest(
            parent=self.scan_run_name), crawled_urls)

    result = self.Run(
        ('web-security-scanner scan-runs list-crawled-urls --scan-run {} '
         '--scan-config {} '
         '--project {}').format(self.scan_run_id, self.scan_config_id,
                                self.Project()))

    self.assertEqual(result, crawled_urls.crawledUrls)

  def testListCrawledUrls_RelativeName(self):
    crawled_urls = self.makeCrawledUrls(10)
    self.client.projects_scanConfigs_scanRuns_crawledUrls.List.Expect(
        self.messages
        .WebsecurityscannerProjectsScanConfigsScanRunsCrawledUrlsListRequest(
            parent=self.scan_run_name), crawled_urls)

    result = self.Run(
        ('web-security-scanner scan-runs list-crawled-urls --scan-run {}'
        ).format(self.scan_run_name))

    self.assertEqual(result, crawled_urls.crawledUrls)

  def testListCrawledUrls_withLimit(self):
    crawled_urls = self.makeCrawledUrls(10)
    self.client.projects_scanConfigs_scanRuns_crawledUrls.List.Expect(
        self.messages
        .WebsecurityscannerProjectsScanConfigsScanRunsCrawledUrlsListRequest(
            parent=self.scan_run_name), crawled_urls)

    limit_value = 5
    result = self.Run(
        ('web-security-scanner scan-runs list-crawled-urls --scan-run {} '
         '--scan-config {} '
         '--project {} '
         '--limit {}').format(self.scan_run_id, self.scan_config_id,
                              self.Project(), limit_value))

    self.assertEqual(len(result), limit_value)


if __name__ == '__main__':
  test_case.main()
