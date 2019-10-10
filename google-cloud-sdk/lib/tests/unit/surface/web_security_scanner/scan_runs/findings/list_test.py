# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud web-security-scanner scan-runs finding list <parent>`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class ScanRunsFindingsListTestAlpha(base.WebSecurityScannerScanRunFindingsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    # When user_output_enabled is True,
    # we can compare std out with expected values
    properties.VALUES.core.user_output_enabled.Set(True)

  def testList(self):

    finding_type_stats_list_request = \
      self.makeScanConfigsScanRunsFindingTypeStatsListRequest()
    finding_type_stats_list_response = \
      self.makeListFindingTypeStatsResponse([
          (self.outdated_lib, 1),
          (self.xss, 2)
      ])

    self.client.projects_scanConfigs_scanRuns_findingTypeStats.List.Expect(
        finding_type_stats_list_request, finding_type_stats_list_response)

    outdated_lib_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.outdated_lib)
    outdated_lib_findings_list_response = \
      self.makeListFindingsResponse(self.outdated_lib, 1)
    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        outdated_lib_findings_list_request, outdated_lib_findings_list_response
    )

    xss_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.xss)
    xss_findings_list_response = self.makeListFindingsResponse(self.xss, 2)
    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        xss_findings_list_request, xss_findings_list_response
    )

    result = self.Run('web-security-scanner scan-runs findings list {}'
                      .format(self.scan_run_name))

    self.assertEqual(len(result), 3)
    self.assertEqual(result[0].findingType, self.outdated_lib)
    self.assertEqual(result[2].findingType, self.xss)

  def testList_WithLimit(self):

    finding_type_stats_list_request = \
      self.makeScanConfigsScanRunsFindingTypeStatsListRequest()
    finding_type_stats_list_response = self.makeListFindingTypeStatsResponse([
        (self.outdated_lib, 1),
        (self.xss, 5)
    ])

    self.client.projects_scanConfigs_scanRuns_findingTypeStats.List.Expect(
        finding_type_stats_list_request, finding_type_stats_list_response)

    outdated_lib_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.outdated_lib)
    outdated_lib_findings_list_response = \
      self.makeListFindingsResponse(self.outdated_lib, 1)
    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        outdated_lib_findings_list_request, outdated_lib_findings_list_response
    )

    xss_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.xss)
    xss_findings_list_response = self.makeListFindingsResponse(self.xss, 5)

    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        xss_findings_list_request, xss_findings_list_response
    )

    self.Run('web-security-scanner scan-runs findings list {} '
             '--limit=2'
             .format(self.scan_run_name))

    self.AssertOutputEquals(
        textwrap.dedent("""\
          ---
          findingType: OUTDATED_LIBRARY
          ---
          findingType: XSS_CALLBACK
          """), normalize_space=True)

  def testList_WithFilter(self):

    finding_type_stats_list_request = \
      self.makeScanConfigsScanRunsFindingTypeStatsListRequest()
    finding_type_stats_list_response = self.makeListFindingTypeStatsResponse([
        (self.outdated_lib, 3),
        (self.xss, 2)
    ])

    self.client.projects_scanConfigs_scanRuns_findingTypeStats.List.Expect(
        finding_type_stats_list_request, finding_type_stats_list_response)

    outdated_lib_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.outdated_lib)
    outdated_lib_findings_list_response = \
      self.makeListFindingsResponse(self.outdated_lib, 3)
    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        outdated_lib_findings_list_request, outdated_lib_findings_list_response
    )

    xss_findings_list_request = \
      self.makeScanConfigsScanRunsFindingsListRequest(self.xss)
    xss_findings_list_response = self.makeListFindingsResponse(self.xss, 2)
    self.client.projects_scanConfigs_scanRuns_findings.List.Expect(
        xss_findings_list_request, xss_findings_list_response
    )

    self.Run('web-security-scanner scan-runs findings list {} '
             '--filter="findingType: {}"'
             .format(self.scan_run_name, self.xss))

    self.AssertOutputEquals(
        textwrap.dedent("""\
          ---
          findingType: XSS_CALLBACK
          ---
          findingType: XSS_CALLBACK
          """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
