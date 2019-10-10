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
"""Tests for `gcloud web-security-scanner scan-configs update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class ScanConfigsUpdateTestAlpha(base.WebSecurityScannerScanConfigsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.base_scan_config = self.messages.ScanConfig(
        name=self.scan_config_name,
        displayName='Default',
        startingUrls=['http://example.com/'])

    # Scan config with flag default values set.
    # They wont affect the update operation, unless the mask is set.
    self.default_scan_config = self.messages.ScanConfig(
        exportToSecurityCommandCenter=self.export['ENABLED'],
        targetPlatforms=[
            self.platforms['app_engine'], self.platforms['compute']
        ],
        riskLevel=self.risk_level['normal'])

  def testUpdate_changeDisplayName(self):
    response = copy.deepcopy(self.base_scan_config)
    response.displayName = 'New Name'
    modified = copy.deepcopy(self.default_scan_config)
    modified.displayName = 'New Name'
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='displayName'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--display-name="New Name"').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeStartingUrls(self):
    response = copy.deepcopy(self.base_scan_config)
    response.startingUrls = ['http://example.com/new']
    modified = copy.deepcopy(self.default_scan_config)
    modified.startingUrls = ['http://example.com/new']
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='startingUrls'), response)

    result = self.Run(('web-security-scanner scan-configs update {} '
                       '--starting-urls=http://example.com/new').format(
                           self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeMaxQps(self):
    response = copy.deepcopy(self.base_scan_config)
    response.maxQps = 10
    modified = copy.deepcopy(self.default_scan_config)
    modified.maxQps = 10
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='maxQps'), response)

    result = self.Run(('web-security-scanner scan-configs update {} '
                       '--max-qps=10').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeExportToSecurityScanner(self):
    response = copy.deepcopy(self.base_scan_config)
    response.exportToSecurityCommandCenter = self.export['DISABLED']
    modified = copy.deepcopy(self.default_scan_config)
    modified.exportToSecurityCommandCenter = self.export['DISABLED']
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='exportToSecurityCommandCenter'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--no-export-to-security-center').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeBlacklistPatterns(self):
    response = copy.deepcopy(self.base_scan_config)
    response.blacklistPatterns = ['http://*/']
    modified = copy.deepcopy(self.default_scan_config)
    modified.blacklistPatterns = ['http://*/']
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='blacklistPatterns'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--blacklist-patterns=http://*/').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeScheduleInterval(self):
    response = copy.deepcopy(self.base_scan_config)
    response.schedule = self.messages.Schedule(intervalDurationDays=3)
    modified = copy.deepcopy(self.default_scan_config)
    modified.schedule = self.messages.Schedule(intervalDurationDays=3)
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='schedule.intervalDurationDays'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--schedule-interval-days=3').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeScheduleTime(self):
    time = '2019-01-01T00:00:00Z'
    response = copy.deepcopy(self.base_scan_config)
    response.schedule = self.messages.Schedule(scheduleTime=time)
    modified = copy.deepcopy(self.default_scan_config)
    modified.schedule = self.messages.Schedule(scheduleTime=time)
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='schedule.scheduleTime'), response)

    result = self.Run(('web-security-scanner scan-configs update {} '
                       '--schedule-next-start={}').format(
                           self.scan_config_name, time))

    self.assertEqual(result, response)

  def testUpdate_changeTargetPlatforms(self):
    response = copy.deepcopy(self.base_scan_config)
    response.targetPlatforms = [self.platforms['compute']]
    modified = copy.deepcopy(self.default_scan_config)
    modified.targetPlatforms = [self.platforms['compute']]
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='targetPlatforms'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--target-platforms=compute').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeUserAgent(self):
    response = copy.deepcopy(self.base_scan_config)
    response.userAgent = self.user_agent['chrome_android']
    modified = copy.deepcopy(self.default_scan_config)
    modified.userAgent = self.user_agent['chrome_android']
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='userAgent'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         '--user-agent=chrome_android').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeRiskLevel(self):
    response = copy.deepcopy(self.base_scan_config)
    response.riskLevel = self.risk_level['low']
    modified = copy.deepcopy(self.default_scan_config)
    modified.riskLevel = self.risk_level['low']
    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='riskLevel'), response)

    result = self.Run(('web-security-scanner scan-configs update {} '
                       '--risk-level=low').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeAuthToCustom(self):
    response = copy.deepcopy(self.base_scan_config)
    response.authentication = self.messages.Authentication(
        customAccount=self.messages.CustomAccount(
            username='username',
            loginUrl='http://example.com/login',
        ))

    modified = copy.deepcopy(self.default_scan_config)
    modified.authentication = self.messages.Authentication(
        customAccount=self.messages.CustomAccount(
            username='username',
            password='password',
            loginUrl='http://example.com/login',
        ))

    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='authentication'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         ' --auth-type=custom'
         ' --auth-user=username'
         ' --auth-password=password'
         ' --auth-url=http://example.com/login').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeAuthToGoogle(self):
    response = copy.deepcopy(self.base_scan_config)
    response.authentication = self.messages.Authentication(
        googleAccount=self.messages.GoogleAccount(
            username='username@gmail.com',))

    modified = copy.deepcopy(self.default_scan_config)
    modified.authentication = self.messages.Authentication(
        googleAccount=self.messages.GoogleAccount(
            username='username@gmail.com',
            password='password',
        ))

    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='authentication'), response)

    result = self.Run(
        ('web-security-scanner scan-configs update {} '
         ' --auth-type=google'
         ' --auth-user=username@gmail.com'
         ' --auth-password=password').format(self.scan_config_name))

    self.assertEqual(result, response)

  def testUpdate_changeAuthToNone(self):
    response = copy.deepcopy(self.base_scan_config)
    modified = copy.deepcopy(self.default_scan_config)

    self.client.projects_scanConfigs.Patch.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
            name=self.scan_config_name,
            scanConfig=modified,
            updateMask='authentication'), response)

    result = self.Run(('web-security-scanner scan-configs update {} '
                       ' --auth-type=none').format(self.scan_config_name))

    self.assertEqual(result, response)


if __name__ == '__main__':
  test_case.main()
