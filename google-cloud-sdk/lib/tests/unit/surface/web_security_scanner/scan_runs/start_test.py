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
"""Tests for `gcloud web-security-scanner scan-runs start`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class ScanRunsStartTestAlpha(base.WebSecurityScannerScanRunsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testStart(self):
    self.client.projects_scanConfigs.Start.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsStartRequest(
            name=self.scan_config_name), self.scan_run)

    result = self.Run(('web-security-scanner scan-runs start {} '
                       '--project {}').format(self.scan_config_id,
                                              self.Project()))

    self.assertEqual(result, self.scan_run)

  def testStart_RelativeName(self):
    self.client.projects_scanConfigs.Start.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsStartRequest(
            name=self.scan_config_name), self.scan_run)

    result = self.Run(('web-security-scanner scan-runs start {}').format(
        self.scan_config_name))

    self.assertEqual(result, self.scan_run)


if __name__ == '__main__':
  test_case.main()
