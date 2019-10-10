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

"""Tests of the 'cmek-settings update' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class CmekSettingsUpdateTest(base.LoggingTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdateSuccess(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='projects/p/locations/l/keyRings/k/cryptoKeys/c')
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        expected_settings)
    self.RunLogging(
        'cmek-settings update --organization=organizations/123 '
        '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c')

  def testUpdateKeyPartsSuccess(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='projects/p/locations/l/keyRings/k/cryptoKeys/c')
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        expected_settings)
    self.RunLogging(
        'cmek-settings update --organization=organizations/123 '
        '--kms-project=p --kms-location=l --kms-keyring=k --kms-key-name=c')

  def testUpdateSuccessClearCmekKey(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='')
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        expected_settings)
    self.RunLogging(
        'cmek-settings update --organization=organizations/123 '
        '--clear-kms-key')

  def testGetCmekSettingsOrgCompletion(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='projects/p/locations/l/keyRings/k/cryptoKeys/c')
    # Organization arg 123 is expanded to organizations/123
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        expected_settings)
    self.RunLogging(
        'cmek-settings update --organization=123 '
        '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c')

  def testUpdateMissingRequiredFlag(self):
    with self.AssertRaisesArgumentErrorRegexp('Exactly one of'):
      self.RunLogging(
          'cmek-settings update --organization=organizations/123')
    self.AssertErrContains('Exactly one of')

  def testUpdateTooManyFlags(self):
    with self.AssertRaisesArgumentErrorRegexp('Exactly one of'):
      self.RunLogging(
          'cmek-settings update --organization=organizations/123'
          '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c'
          '--clear-kms-key')
    self.AssertErrContains('Exactly one of')

  def testUpdateMissingOrganization(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='projects/p/locations/l/keyRings/k/cryptoKeys/c')
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        exception=http_error.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches('not found'):
      self.RunLogging(
          'cmek-settings update --organization=organizations/123 '
          '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c')
    self.AssertErrContains('not found')

  def testListNoPerms(self):
    expected_settings = self.msgs.CmekSettings(
        kmsKeyName='projects/p/locations/l/keyRings/k/cryptoKeys/c')
    self.mock_client_v2.organizations.UpdateCmekSettings.Expect(
        # NOTE: Due to a limitation of generated API client for singletons, name
        # in the request will not include the desired '/cmekSettings' suffix.
        self.msgs.LoggingOrganizationsUpdateCmekSettingsRequest(
            name='organizations/123',
            updateMask='kms_key_name',
            cmekSettings=expected_settings),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'cmek-settings update --organization=organizations/123 '
        '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c')

  def testListNoAuth(self):
    self.RunWithoutAuth(
        'cmek-settings update --organization=organizations/123 '
        '--kms-key-name=projects/p/locations/l/keyRings/k/cryptoKeys/c')


if __name__ == '__main__':
  test_case.main()
