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
"""Tests for `gcloud web-security-scanner scan-configs create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class ScanConfigsCreateTestAlpha(base.WebSecurityScannerScanConfigsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def createSchedule(self, interval, time):
    return self.messages.Schedule(
        intervalDurationDays=interval,
        scheduleTime=time,
    )

  def testCreate_missingRequiredDisplayName(self):
    with self.AssertRaisesArgumentErrorRegexp(r'--display-name'):
      self.Run(
          'web-security-scanner scan-configs create --starting-urls=http://example.com/ --project {}'
          .format(self.Project()))

  def testCreate_missingRequiredStartingUrls(self):
    with self.AssertRaisesArgumentErrorRegexp(r'--starting-urls'):
      self.Run(
          'web-security-scanner scan-configs create --display-name="display name" --project {}'
          .format(self.Project()))

  def testCreate_justRequiredFieldsAndDefaults(self):
    expected = self.messages.ScanConfig(
        displayName='Display',
        startingUrls=['http://example.com/'],
        targetPlatforms=[
            self.platforms['app_engine'], self.platforms['compute']
        ],  # Default
        exportToSecurityCommandCenter=self.export['ENABLED'],  # Default
    )
    response = self.messages.ScanConfig(
        name='/projects/{}/scanConfigs/123'.format(self.Project()),
        targetPlatforms=[
            self.platforms['app_engine'], self.platforms['compute']
        ],
        exportToSecurityCommandCenter=self.export['ENABLED'],
        displayName='Display',
        startingUrls=['http://example.com/'])
    self.client.projects_scanConfigs.Create.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsCreateRequest(
            parent='projects/{}'.format(self.Project()), scanConfig=expected),
        response)

    result = self.Run(
        ('web-security-scanner scan-configs create --project {} '
         '--display-name=Display --starting-urls=http://example.com/').format(
             self.Project()))

    self.assertEqual(result, response)

  def testCreate_setAllNonAuthFields(self):
    expected = self.messages.ScanConfig(
        displayName='Display',
        startingUrls=['http://example.com/'],
        targetPlatforms=[self.platforms['compute']],
        exportToSecurityCommandCenter=self.export['DISABLED'],
        blacklistPatterns=[
            'http://example.com/foo/*', 'http://example.com/bar/*'
        ],
        maxQps=1,
        schedule=self.createSchedule(7, '2019-01-01T00:00:00Z'),
        userAgent=self.user_agent['safari_iphone'],
    )
    response = self.messages.ScanConfig(
        displayName='Display',
        startingUrls=['http://example.com/'],
        targetPlatforms=[self.platforms['compute']],
        exportToSecurityCommandCenter=self.export['DISABLED'],
        blacklistPatterns=[
            'http://example.com/foo/*', 'http://example.com/bar/*'
        ],
        maxQps=1,
        schedule=self.createSchedule(7, '2019-01-01T00:00:00Z'),
        userAgent=self.user_agent['safari_iphone'],
        name='/projects/{}/scanConfigs/123'.format(self.Project()))
    self.client.projects_scanConfigs.Create.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsCreateRequest(
            parent='projects/{}'.format(self.Project()), scanConfig=expected),
        response)

    result = self.Run((
        'web-security-scanner scan-configs create --project {} '
        ' --display-name=Display'
        ' --starting-urls=http://example.com/'
        ' --target-platforms=compute'
        ' --no-export-to-security-center'
        ' --blacklist-patterns="http://example.com/foo/*,http://example.com/bar/*"'
        ' --max-qps=1'
        ' --schedule-interval-days=7'
        ' --schedule-next-start=2019-01-01T00:00:00Z'
        ' --user-agent=safari_iphone').format(self.Project()))

    self.assertEqual(result, response)

  def testCreate_CustomAuth(self):
    expected = self.messages.ScanConfig(
        displayName='Display',
        startingUrls=['http://example.com/'],
        authentication=self.messages.Authentication(
            customAccount=self.messages.CustomAccount(
                loginUrl='http://example.com/login',
                password='password',
                username='username',
            ),),
        targetPlatforms=[
            self.platforms['app_engine'], self.platforms['compute']
        ],  # Default
        exportToSecurityCommandCenter=self.export['ENABLED'],  # Default
    )
    response = copy.deepcopy(expected)
    response.authentication.customAccount.password = ''
    self.client.projects_scanConfigs.Create.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsCreateRequest(
            parent='projects/{}'.format(self.Project()), scanConfig=expected),
        response)

    result = self.Run(
        ('web-security-scanner scan-configs create --project {}'
         ' --display-name=Display'
         ' --starting-urls=http://example.com/'
         ' --auth-type=custom'
         ' --auth-user=username'
         ' --auth-password=password'
         ' --auth-url=http://example.com/login').format(self.Project()))

    self.assertEqual(result, response)

  def testCreate_GoogleAuth(self):
    expected = self.messages.ScanConfig(
        displayName='Display',
        startingUrls=['http://example.com/'],
        authentication=self.messages.Authentication(
            googleAccount=self.messages.GoogleAccount(
                password='password',
                username='username@gmail.com',
            ),),
        targetPlatforms=[
            self.platforms['app_engine'], self.platforms['compute']
        ],  # Default
        exportToSecurityCommandCenter=self.export['ENABLED'],  # Default
    )
    response = copy.deepcopy(expected)
    response.authentication.googleAccount.password = ''
    self.client.projects_scanConfigs.Create.Expect(
        self.messages.WebsecurityscannerProjectsScanConfigsCreateRequest(
            parent='projects/{}'.format(self.Project()), scanConfig=expected),
        response)

    result = self.Run(('web-security-scanner scan-configs create --project {}'
                       ' --display-name=Display'
                       ' --starting-urls=http://example.com/'
                       ' --auth-type=google'
                       ' --auth-user=username@gmail.com'
                       ' --auth-password=password').format(self.Project()))

    self.assertEqual(result, response)


if __name__ == '__main__':
  test_case.main()
