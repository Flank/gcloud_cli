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
"""Tests that exercise the 'gcloud kms keys create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import maps
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


class KeysCreateTestGa(base.KmsMockTest, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key')
    self.version_name = self.project_name.Version('global/my_kr/my_key/1')

  def testCreateSuccess(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate
        .AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
        protectionLevel=self.messages.CryptoKeyVersionTemplate
        .ProtectionLevelValueValuesEnum.SOFTWARE)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum
                .ENCRYPT_DECRYPT,
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k-2', value='v-2'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='smile', value='happy')
                    ]),
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum
            .ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(additionalProperties=[
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k1', value='v1'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k-2', value='v-2'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='smile', value='happy')
            ]),
            versionTemplate=ckvt))

    self.Run('kms keys create '
             '--location={0} --keyring={1} {2} --purpose=encryption '
             '--labels=k1=v1,k-2=v-2 --labels=smile=happy'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testCreateFullNameSuccess(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate
        .AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
        protectionLevel=self.messages.CryptoKeyVersionTemplate
        .ProtectionLevelValueValuesEnum.SOFTWARE)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum
                .ENCRYPT_DECRYPT,
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k-2', value='v-2'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='smile', value='happy')
                    ]),
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum
            .ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(additionalProperties=[
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k1', value='v1'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k-2', value='v-2'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='smile', value='happy')
            ]),
            versionTemplate=ckvt))

    self.Run('kms keys create {} --purpose=encryption --labels=k1=v1,k-2=v-2 '
             '--labels=smile=happy'.format(self.key_name.RelativeName()))

  @parameterized.parameters(
      ('asymmetric-signing', 'ec-sign-p256-sha256'),
      ('asymmetric-signing', 'ec-sign-p384-sha384'),
      ('asymmetric-signing', 'rsa-sign-pss-2048-sha256'),
      ('asymmetric-signing', 'rsa-sign-pss-3072-sha256'),
      ('asymmetric-signing', 'rsa-sign-pss-4096-sha256'),
      ('asymmetric-signing', 'rsa-sign-pss-4096-sha512'),
      ('asymmetric-signing', 'rsa-sign-pkcs1-2048-sha256'),
      ('asymmetric-signing', 'rsa-sign-pkcs1-3072-sha256'),
      ('asymmetric-signing', 'rsa-sign-pkcs1-4096-sha256'),
      ('asymmetric-signing', 'rsa-sign-pkcs1-4096-sha256'),
      ('asymmetric-encryption', 'rsa-decrypt-oaep-2048-sha256'),
      ('asymmetric-encryption', 'rsa-decrypt-oaep-3072-sha256'),
      ('asymmetric-encryption', 'rsa-decrypt-oaep-4096-sha256'),
      ('asymmetric-encryption', 'rsa-decrypt-oaep-4096-sha512'))
  def testCreateAsymmetricKeySuccess(self, purpose, algorithm):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=maps.ALGORITHM_MAPPER.GetEnumForChoice(algorithm),
        protectionLevel=self.messages.CryptoKeyVersionTemplate.
        ProtectionLevelValueValuesEnum.SOFTWARE)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=maps.PURPOSE_MAP[purpose], versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=maps.PURPOSE_MAP[purpose],
            versionTemplate=ckvt,
            primary=self.messages.CryptoKeyVersion(
                name=self.version_name.RelativeName(), attestation=None)))
    self.Run('kms keys create --location={0} --keyring={1} {2} '
             '--purpose={3} --default-algorithm={4}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, purpose, algorithm))

  @parameterized.parameters(
      ('asymmetric-signing', 'google-symmetric-encryption'),
      ('asymmetric-signing', 'rsa-decrypt-oaep-3072-sha256'),
      ('asymmetric-encryption', 'google-symmetric-encryption'),
      ('asymmetric-encryption', 'rsa-sign-pss-2048-sha256'),
      ('encryption', 'ec-sign-p256-sha256'),
      ('encryption', 'rsa-decrypt-oaep-3072-sha256'))
  def testCreateAsymmetricKeyInvalidCombo(self, purpose, algorithm):
    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'Default algorithm and purpose are incompatible.'):
      self.Run('kms keys create --location={0} --keyring={1} {2} '
               '--purpose={3} --default-algorithm={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, purpose, algorithm))

  def testCreateSymmetricKeyWithoutAlgorithmSuccess(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate.
        AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
        protectionLevel=self.messages.CryptoKeyVersionTemplate.
        ProtectionLevelValueValuesEnum.SOFTWARE)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            versionTemplate=ckvt))
    self.Run('kms keys create '
             '--location={0} --keyring={1} {2} --purpose=encryption'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testCreateAsymmetricKeyMissingAlgorithm(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException, '--default-algorithm needs to be specified '
        'when creating a key with --purpose=asymmetric-signing'):
      self.Run('kms keys create --location={0} --keyring={1} {2} '
               '--purpose=asymmetric-signing'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

  def testCreateKeyMissingPurpose(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --purpose: Must be specified.'):
      self.Run('kms keys create --location={0} --keyring={1} {2} '
               '--default-algorithm=ec-sign-p256-sha256'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

  def testCreateKeyInvalidPurpose(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, '--purpose: Invalid choice: '
        '\'bad-purpose\'.\n\nValid choices are [asymmetric-encryption, '
        'asymmetric-signing, encryption].'):
      self.Run('kms keys create --location={0} --keyring={1} {2} '
               '--purpose=bad-purpose'.format(self.key_name.location_id,
                                              self.key_name.key_ring_id,
                                              self.key_name.crypto_key_id))

  def testCreateHsmKeySuccess(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate.
        AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
        protectionLevel=self.messages.CryptoKeyVersionTemplate.
        ProtectionLevelValueValuesEnum.HSM)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            versionTemplate=ckvt,
            primary=self.messages.CryptoKeyVersion(
                name=self.version_name.RelativeName(), attestation=None)))
    self.Run(
        'kms keys create --location={0} --keyring={1} {2} '
        '--purpose=encryption --default-algorithm=google-symmetric-encryption '
        '--protection-level=hsm'.format(self.key_name.location_id,
                                        self.key_name.key_ring_id,
                                        self.key_name.crypto_key_id))

  def testCreateHsmAsymmetricKeySuccess(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate.
        AlgorithmValueValuesEnum.RSA_DECRYPT_OAEP_2048_SHA256,
        protectionLevel=self.messages.CryptoKeyVersionTemplate.
        ProtectionLevelValueValuesEnum.HSM)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ASYMMETRIC_DECRYPT,
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ASYMMETRIC_DECRYPT,
            versionTemplate=ckvt,
            primary=self.messages.CryptoKeyVersion(
                name=self.version_name.RelativeName(), attestation=None)))
    self.Run('kms keys create --location={0} --keyring={1} {2} '
             '--purpose=asymmetric-encryption '
             '--default-algorithm=rsa-decrypt-oaep-2048-sha256 '
             '--protection-level=hsm'.format(self.key_name.location_id,
                                             self.key_name.key_ring_id,
                                             self.key_name.crypto_key_id))


class KeysCreateTestBeta(KeysCreateTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateSuccessSkipInitialVersion(self):
    ckvt = self.messages.CryptoKeyVersionTemplate(
        algorithm=self.messages.CryptoKeyVersionTemplate
        .AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
        protectionLevel=self.messages.CryptoKeyVersionTemplate
        .ProtectionLevelValueValuesEnum.SOFTWARE)

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
            skipInitialVersionCreation=True,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum
                .ENCRYPT_DECRYPT,
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k-2', value='v-2'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='smile', value='happy')
                    ]),
                versionTemplate=ckvt)),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum
            .ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(additionalProperties=[
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k1', value='v1'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k-2', value='v-2'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='smile', value='happy')
            ]),
            versionTemplate=ckvt))

    self.Run('kms keys create '
             '--location={0} --keyring={1} {2} --purpose=encryption '
             '--labels=k1=v1,k-2=v-2 --labels=smile=happy '
             '--skip-initial-version-creation'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))


class KeysCreateTestAlpha(KeysCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
