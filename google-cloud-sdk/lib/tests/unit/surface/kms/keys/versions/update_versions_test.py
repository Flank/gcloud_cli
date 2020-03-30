# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests that exercise the 'gcloud kms versions update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptoKeyVersionsUpdateTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key/')
    self.version_name = self.key_name.Version('3')

  def testNoUpdateFieldsSpecifiedRaisesError(self):
    with self.AssertRaisesExceptionMatches(exceptions.ToolException, ''):
      self.Run(
          'kms keys versions update {0} --location={1} --keyring={2} --key={3}'
          .format(self.version_name.version_id, self.version_name.location_id,
                  self.version_name.key_ring_id,
                  self.version_name.crypto_key_id))

  def testUpdateExternalKeyUriFailsOnNonExternalVersion(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.SOFTWARE))
    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'External key URI updates are only available for key versions '
        'with EXTERNAL protection level'):
      self.Run(
          'kms keys versions update {0} --location={1} --keyring={2} --key={3} '
          '--external-key-uri=https://example.kms/v0/some/other/key/path'
          .format(self.version_name.version_id, self.version_name.location_id,
                  self.version_name.key_ring_id,
                  self.version_name.crypto_key_id))

  def testUpdateExternalKeyUriSucceeds(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions

    original_uri = 'https://example.kms/v0/some/key/path'
    modified_uri = 'https://example.kms/v0/some/other/key/path'

    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            externalProtectionLevelOptions=self.messages
            .ExternalProtectionLevelOptions(externalKeyUri=original_uri),
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.EXTERNAL))

    ckv.Patch.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
            name=self.version_name.RelativeName(),
            cryptoKeyVersion=self.messages.CryptoKeyVersion(
                externalProtectionLevelOptions=self.messages
                .ExternalProtectionLevelOptions(externalKeyUri=modified_uri)),
            updateMask='externalProtectionLevelOptions.externalKeyUri'),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            externalProtectionLevelOptions=self.messages
            .ExternalProtectionLevelOptions(externalKeyUri=modified_uri)))

    self.Run(
        'kms keys versions update {0} --location={1} --keyring={2} --key={3} '
        '--external-key-uri={4}'.format(self.version_name.version_id,
                                        self.version_name.location_id,
                                        self.version_name.key_ring_id,
                                        self.version_name.crypto_key_id,
                                        modified_uri))

  def testEnableDisabledKeyVersion(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.DISABLED))

    ckv.Patch.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
            name=self.version_name.RelativeName(),
            cryptoKeyVersion=self.messages.CryptoKeyVersion(
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum
                .ENABLED,
                externalProtectionLevelOptions=self.messages
                .ExternalProtectionLevelOptions(externalKeyUri=None),
            ),
            updateMask='state'),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.ENABLED))

    self.Run(
        'kms keys versions update {0} --location={1} --keyring={2} --key={3} '
        '--state=enabled'.format(self.version_name.version_id,
                                 self.version_name.location_id,
                                 self.version_name.key_ring_id,
                                 self.version_name.crypto_key_id))

  def testDisableEnabledKeyVersion(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.ENABLED))

    ckv.Patch.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
            name=self.version_name.RelativeName(),
            cryptoKeyVersion=self.messages.CryptoKeyVersion(
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum
                .DISABLED,
                externalProtectionLevelOptions=self.messages
                .ExternalProtectionLevelOptions(externalKeyUri=None),
            ),
            updateMask='state'),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.DISABLED))

    self.Run(
        'kms keys versions update {0} --location={1} --keyring={2} --key={3} '
        '--state=disabled'.format(self.version_name.version_id,
                                  self.version_name.location_id,
                                  self.version_name.key_ring_id,
                                  self.version_name.crypto_key_id))

  def testUpdateStateAndKeyUri(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions

    original_uri = 'https://example.kms/v0/some/key/path'
    modified_uri = 'https://example.kms/v0/some/other/key/path'

    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.ENABLED,
            externalProtectionLevelOptions=self.messages
            .ExternalProtectionLevelOptions(externalKeyUri=original_uri),
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.EXTERNAL))

    ckv.Patch.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
            name=self.version_name.RelativeName(),
            cryptoKeyVersion=self.messages.CryptoKeyVersion(
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum
                .DISABLED,
                externalProtectionLevelOptions=self.messages
                .ExternalProtectionLevelOptions(externalKeyUri=modified_uri)),
            updateMask='externalProtectionLevelOptions.externalKeyUri,state'),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.DISABLED,
            externalProtectionLevelOptions=self.messages
            .ExternalProtectionLevelOptions(externalKeyUri=modified_uri)))

    self.Run(
        'kms keys versions update {0} --location={1} --keyring={2} --key={3} '
        '--external-key-uri={4} --state=disabled'.format(
            self.version_name.version_id, self.version_name.location_id,
            self.version_name.key_ring_id, self.version_name.crypto_key_id,
            modified_uri))


if __name__ == '__main__':
  test_case.main()
