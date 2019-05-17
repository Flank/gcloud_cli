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
"""Base classes for all gcloud web-security-scanner tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class WebSecurityScannerBase(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase,
                             sdk_test_base.WithLogCapture):
  """Base class for Cloud Web Security Scanner unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        client_class=apis.GetClientClass('websecurityscanner', 'v1beta'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('websecurityscanner', 'v1beta')


class WebSecurityScannerScanConfigsBase(WebSecurityScannerBase):
  """Base class for Cloud Web Security Scanner scan configs unit tests."""

  def SetUp(self):
    self.scan_config_id = '123456'
    self.scan_config_name = ('projects/{}/'
                             'scanConfigs/{}').format(self.Project(),
                                                      self.scan_config_id)
    self.scan_config = self.messages.ScanConfig(name=self.scan_config_name)

    self.platforms = {
        'app_engine':
            self.messages.ScanConfig.TargetPlatformsValueListEntryValuesEnum
            .APP_ENGINE,
        'compute':
            self.messages.ScanConfig.TargetPlatformsValueListEntryValuesEnum
            .COMPUTE,
    }
    self.export = {
        'ENABLED':
            self.messages.ScanConfig
            .ExportToSecurityCommandCenterValueValuesEnum.ENABLED,
        'DISABLED':
            self.messages.ScanConfig
            .ExportToSecurityCommandCenterValueValuesEnum.DISABLED,
    }
    self.user_agent = {
        'chrome_linux':
            self.messages.ScanConfig.UserAgentValueValuesEnum.CHROME_LINUX,
        'chrome_android':
            self.messages.ScanConfig.UserAgentValueValuesEnum.CHROME_ANDROID,
        'safari_iphone':
            self.messages.ScanConfig.UserAgentValueValuesEnum.SAFARI_IPHONE,
    }

  def makeScanConfigs(self, size=10):
    scan_configs = []
    for i in range(size):
      scan_config_name = ('projects/{}/'
                          'scanConfigs/{}').format(self.Project(), i)
      scan_config = self.messages.ScanConfig(name=scan_config_name)
      scan_configs.append(scan_config)
    return self.messages.ListScanConfigsResponse(scanConfigs=scan_configs)


class WebSecurityScannerScanRunsBase(WebSecurityScannerScanConfigsBase):
  """Base class for Cloud Web Security Scanner scan configs unit tests."""

  def SetUp(self):
    self.scan_run_id = '11223344'
    self.scan_run_name = self.scan_config_name + '/scanRuns/' + self.scan_run_id
    self.scan_run = self.messages.ScanRun(name=self.scan_run_name)

  def makeScanRuns(self, size=10):
    scan_runs = []
    for i in range(size):
      scan_run_name = self.scan_config_name + '/scanRuns/' + str(i)
      scan_run = self.messages.ScanRun(name=scan_run_name)
      scan_runs.append(scan_run)
    return self.messages.ListScanRunsResponse(scanRuns=scan_runs)

  def makeCrawledUrls(self, size=10):
    crawled_urls = []
    for i in range(size):
      crawled_url = self.messages.CrawledUrl(
          url='http://www.irrelevant.com/' + str(i), httpMethod='GET')
      crawled_urls.append(crawled_url)
    return self.messages.ListCrawledUrlsResponse(crawledUrls=crawled_urls)


class WebSecurityScannerScanRunFindingsBase(WebSecurityScannerScanRunsBase):
  """Base class for Cloud Web Security Scanner scan runs findings unit tests."""

  def SetUp(self):
    self.xss = 'XSS_CALLBACK'
    self.outdated_lib = 'OUTDATED_LIBRARY'

  def makeScanConfigsScanRunsFindingTypeStatsListRequest(self):
    return self.messages\
      .WebsecurityscannerProjectsScanConfigsScanRunsFindingTypeStatsListRequest(
          parent=self.scan_run_name
      )

  def makeListFindingTypeStatsResponse(self, finding_type_data):
    finding_type_stats = []
    for finding_type, count in finding_type_data:
      finding_type_stats.append(self.messages.FindingTypeStats(
          findingType=finding_type,
          findingCount=count
      ))

    return self.messages.ListFindingTypeStatsResponse(
        findingTypeStats=finding_type_stats
    )

  def makeScanConfigsScanRunsFindingsListRequest(self, finding_type):
    return self.messages\
      .WebsecurityscannerProjectsScanConfigsScanRunsFindingsListRequest(
          parent=self.scan_run_name,
          filter='finding_type=' + finding_type
      )

  def makeListFindingsResponse(self, finding_type, size):
    findings = []

    for _ in range(size):
      finding = self.messages.Finding(findingType=finding_type)
      findings.append(finding)

    return self.messages.ListFindingsResponse(findings=findings)
