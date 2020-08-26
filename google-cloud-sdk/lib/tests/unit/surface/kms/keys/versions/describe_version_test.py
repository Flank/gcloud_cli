# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests that exercise 'gcloud kms keys versions describe'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysVersionsDescribeTestGa(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key/')
    self.version_name = self.key_name.Version('3')
    self.attestation = self.messages.KeyOperationAttestation(
        format=self.messages.KeyOperationAttestation.FormatValueValuesEnum
        .CAVIUM_V1_COMPRESSED,
        content=b'attestation content',
        certChains=self.messages.CertificateChains(
            caviumCerts=('cavium_partition_cert', 'cavium_card_cert'),
            googleCardCerts=('google_card_cert',),
            googlePartitionCerts=('google_partition_cert',)))

  def testDescribe(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(name=self.version_name.RelativeName()))

    self.Run('kms keys versions describe {0} --location={1} '
             '--keyring={2} --key={3}'.format(self.version_name.version_id,
                                              self.version_name.location_id,
                                              self.version_name.key_ring_id,
                                              self.version_name.crypto_key_id))

    self.AssertOutputContains(
        'name: {0}'.format(self.version_name.RelativeName()),
        normalize_space=True)

  def testMissingId(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [version]: version id must be non-empty.'):
      self.Run('kms keys versions describe {0}/cryptoKeyVersions/'.format(
          self.key_name.RelativeName()))

  def testDescribeHsmKeyVersionWithAttestation(self):
    attestation_file_path = self.Touch(self.temp_path)

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            algorithm=self.messages.CryptoKeyVersion.AlgorithmValueValuesEnum
            .GOOGLE_SYMMETRIC_ENCRYPTION,
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.HSM,
            attestation=self.attestation))

    self.Run(
        'kms keys versions describe {0} --location={1} --keyring={2} --key={3} '
        '--attestation-file={4}'.format(self.version_name.version_id,
                                        self.version_name.location_id,
                                        self.version_name.key_ring_id,
                                        self.version_name.crypto_key_id,
                                        attestation_file_path))

    self.AssertOutputContains(
        'name: {}'.format(self.key_name.RelativeName()), normalize_space=True)

    self.AssertOutputContains('format: CAVIUM_V1_COMPRESSED')
    # The attestation 'content' subfield should be omitted from the output,
    # since it's written to the file instead.
    self.AssertOutputNotContains('content:')
    # The attestation 'certChains' subfield should be omitted from the output,
    # since they are retrieved using the get-certificate-chain command.
    self.AssertOutputNotContains('certChains:')

    self.AssertBinaryFileEquals(b'attestation content', attestation_file_path)

  def testDescribeHsmKeyVersionWithoutAttestationFlag(self):
    attestation_file_path = self.Touch(self.temp_path)

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            algorithm=self.messages.CryptoKeyVersion.AlgorithmValueValuesEnum
            .GOOGLE_SYMMETRIC_ENCRYPTION,
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.HSM,
            attestation=self.attestation))

    self.Run(
        'kms keys versions describe {0} --location={1} --keyring={2} --key={3}'
        .format(self.version_name.version_id, self.version_name.location_id,
                self.version_name.key_ring_id, self.version_name.crypto_key_id))

    self.AssertOutputContains(
        'name: {}'.format(self.key_name.RelativeName()), normalize_space=True)

    self.AssertOutputContains('format: CAVIUM_V1_COMPRESSED')
    # The attestation 'content' subfield should be omitted from the output.
    self.AssertOutputNotContains('content:')
    # The attestation 'certChains' subfield should be omitted from the output,
    self.AssertOutputNotContains('certChains:')

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribeSoftwareKeyVersionWithAttestationThrowsException(self):
    attestation_file_path = self.Touch(self.temp_path)

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            algorithm=self.messages.CryptoKeyVersion.AlgorithmValueValuesEnum
            .GOOGLE_SYMMETRIC_ENCRYPTION,
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.SOFTWARE))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'Attestations are only available for HSM key versions.'):
      self.Run('kms keys versions describe {0} --location={1} --keyring={2} '
               '--key={3} --attestation-file={4}'.format(
                   self.version_name.version_id, self.version_name.location_id,
                   self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, attestation_file_path))

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribePendingKeyVersionWithAttestationThrowsException(self):
    attestation_file_path = self.Touch(self.temp_path)

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            algorithm=self.messages.CryptoKeyVersion.AlgorithmValueValuesEnum
            .GOOGLE_SYMMETRIC_ENCRYPTION,
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.HSM,
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum
            .PENDING_GENERATION))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'The attestation is unavailable until the version is generated.'):
      self.Run('kms keys versions describe {0} --location={1} --keyring={2} '
               '--key={3} --attestation-file={4}'.format(
                   self.version_name.version_id, self.version_name.location_id,
                   self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, attestation_file_path))

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribeKeyVersionWithInvalidAttestationFile(self):
    attestation_file_path = os.path.join(self.temp_path, 'nested',
                                         'nonexistent', 'file')

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(
            name=self.version_name.RelativeName(),
            algorithm=self.messages.CryptoKeyVersion.AlgorithmValueValuesEnum
            .GOOGLE_SYMMETRIC_ENCRYPTION,
            protectionLevel=self.messages.CryptoKeyVersion
            .ProtectionLevelValueValuesEnum.HSM,
            state=self.messages.CryptoKeyVersion.StateValueValuesEnum.ENABLED,
            attestation=self.attestation))

    with self.AssertRaisesExceptionMatches(exceptions.BadFileException,
                                           attestation_file_path):
      self.Run('kms keys versions describe {0} --location={1} --keyring={2} '
               '--key={3} --attestation-file={4}'.format(
                   self.version_name.version_id, self.version_name.location_id,
                   self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, attestation_file_path))


class CryptokeysVersionsDescribeTestBeta(CryptokeysVersionsDescribeTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CryptokeysVersionsDescribeTestAlpha(CryptokeysVersionsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
