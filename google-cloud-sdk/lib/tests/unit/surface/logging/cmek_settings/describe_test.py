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

"""Tests of the 'cmek-settings describe' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class OrganizationGetCmekSettingsTest(base.LoggingTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testGetCmekSettings(self):
    mock_settings_response = self.msgs.CmekSettings(
        name='foo',
        serviceAccountId='bar',
        kmsKeyName='baz')
    self.mock_client_v2.organizations.GetCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsGetCmekSettingsRequest(
            name='organizations/123'),
        mock_settings_response)
    self.RunLogging('cmek-settings describe --organization=organizations/123')
    self.AssertOutputContains(mock_settings_response.name)
    self.AssertOutputContains(mock_settings_response.serviceAccountId)
    self.AssertOutputContains('kmsKeyName:')
    self.AssertOutputContains(mock_settings_response.kmsKeyName)

  def testGetCmekSettingsNoKeyReturned(self):
    settings_response = self.msgs.CmekSettings(
        name='foo',
        serviceAccountId='bar')
    self.mock_client_v2.organizations.GetCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsGetCmekSettingsRequest(
            name='organizations/123'),
        settings_response)
    self.RunLogging('cmek-settings describe --organization=organizations/123')
    self.AssertOutputContains(settings_response.name)
    self.AssertOutputContains(settings_response.serviceAccountId)
    self.AssertOutputNotContains('kmsKeyName:')

  def testGetCmekSettingsOrgCompletion(self):
    # Organization arg 123 is expanded to organizations/123
    self.mock_client_v2.organizations.GetCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsGetCmekSettingsRequest(
            name='organizations/123'),
        self.msgs.CmekSettings())
    self.RunLogging('cmek-settings describe --organization=123')

  def testGetCmekSettingsNoPerms(self):
    self.mock_client_v2.organizations.GetCmekSettings.Expect(
        self.msgs.LoggingOrganizationsGetCmekSettingsRequest(
            name='organizations/123'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'cmek-settings describe --organization=organizations/123')

  def testGetCmekSettingsNoAuth(self):
    self.RunWithoutAuth(
        'cmek-settings describe --organization=organizations/123')


if __name__ == '__main__':
  test_case.main()
