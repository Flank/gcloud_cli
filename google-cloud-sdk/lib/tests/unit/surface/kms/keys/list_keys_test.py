# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests that exercise the 'gcloud kms keys list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysListTest(base.KmsMockTest):

  def testListSuccess(self, track):
    self.track = track
    ckv_1 = self.project_name.Descendant('global/my_kr/my_key1/my_version1')
    ckv_2 = self.project_name.Descendant('global/my_kr/my_key2/my_version2')
    key_with_labels = self.project_name.Descendant('global/my_kr/my_key')

    self.kms.projects_locations_keyRings_cryptoKeys.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysListRequest(
            pageSize=100, parent=ckv_1.Parent().Parent().RelativeName()),
        self.messages.ListCryptoKeysResponse(cryptoKeys=[
            self.messages.CryptoKey(
                name=ckv_1.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                primary=self.messages.CryptoKeyVersion(
                    name=ckv_1.RelativeName(),
                    state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                    ENABLED)),
            self.messages.CryptoKey(
                name=ckv_2.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                primary=self.messages.CryptoKeyVersion(
                    name=ckv_2.RelativeName(),
                    state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                    ENABLED)),
            self.messages.CryptoKey(
                name=key_with_labels.RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k-2', value='v-2')
                    ]))
        ]))

    self.Run('kms keys list --location={0} --keyring {1}'.format(
        ckv_1.location_id, ckv_1.key_ring_id))
    self.AssertOutputContains(
        """NAME PURPOSE LABELS PRIMARY_ID PRIMARY_STATE
{0} ENCRYPT_DECRYPT my_version1 ENABLED
{1} ENCRYPT_DECRYPT my_version2 ENABLED
{2} ENCRYPT_DECRYPT k-2=v-2,k1=v1
""".format(ckv_1.Parent().RelativeName(),
           ckv_2.Parent().RelativeName(), key_with_labels.RelativeName()),
        normalize_space=True)

  def testListParentFlagSuccess(self, track):
    self.track = track
    key_1 = self.project_name.Descendant('global/my_kr/my_key1')

    self.kms.projects_locations_keyRings_cryptoKeys.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysListRequest(
            pageSize=100, parent=key_1.Parent().RelativeName()),
        self.messages.ListCryptoKeysResponse(cryptoKeys=[
            self.messages.CryptoKey(
                name=key_1.RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT)
        ]))

    self.Run('kms keys list --keyring {}'.format(key_1.Parent().RelativeName()))
    self.AssertOutputContains(
        """NAME PURPOSE LABELS PRIMARY_ID PRIMARY_STATE
{} ENCRYPT_DECRYPT
""".format(key_1.RelativeName()),
        normalize_space=True)


class CryptokeysListAlphaTest(base.KmsMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testListAlphaSuccess(self):
    # Set Up.
    ckv_1 = self.project_name.Descendant('global/my_kr/my_key1/my_version1')
    ckv_2 = self.project_name.Descendant('global/my_kr/my_key2/my_version2')
    key = self.project_name.Descendant('global/my_kr/my_key')

    # Test List.
    self.kms.projects_locations_keyRings_cryptoKeys.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysListRequest(
            pageSize=100, parent=ckv_1.Parent().Parent().RelativeName()),
        self.messages.ListCryptoKeysResponse(cryptoKeys=[
            self.messages.CryptoKey(
                name=ckv_1.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ASYMMETRIC_SIGN,
                versionTemplate=self.messages.CryptoKeyVersionTemplate(
                    algorithm=self.messages.CryptoKeyVersionTemplate.
                    AlgorithmValueValuesEnum.RSA_SIGN_PKCS1_2048_SHA256,
                    protectionLevel=self.messages.CryptoKeyVersionTemplate.
                    ProtectionLevelValueValuesEnum.HSM)),
            self.messages.CryptoKey(
                name=ckv_2.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ASYMMETRIC_SIGN,
                versionTemplate=self.messages.CryptoKeyVersionTemplate(
                    algorithm=self.messages.CryptoKeyVersionTemplate.
                    AlgorithmValueValuesEnum.RSA_SIGN_PSS_3072_SHA256,
                    protectionLevel=self.messages.CryptoKeyVersionTemplate.
                    ProtectionLevelValueValuesEnum.SOFTWARE)),
            self.messages.CryptoKey(
                name=key.RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ASYMMETRIC_DECRYPT,
                versionTemplate=self.messages.CryptoKeyVersionTemplate(
                    algorithm=self.messages.CryptoKeyVersionTemplate.
                    AlgorithmValueValuesEnum.RSA_DECRYPT_OAEP_2048_SHA256,
                    protectionLevel=self.messages.CryptoKeyVersionTemplate.
                    ProtectionLevelValueValuesEnum.SOFTWARE))
        ]))

    self.Run('kms keys list --location={0} --keyring {1}'.format(
        ckv_1.location_id, ckv_1.key_ring_id))
    self.AssertOutputContains(
        """NAME PURPOSE ALGORITHM PROTECTION_LEVEL LABELS PRIMARY_ID \
PRIMARY_STATE
{0} ASYMMETRIC_SIGN RSA_SIGN_PKCS1_2048_SHA256 HSM
{1} ASYMMETRIC_SIGN RSA_SIGN_PSS_3072_SHA256 SOFTWARE
{2} ASYMMETRIC_DECRYPT RSA_DECRYPT_OAEP_2048_SHA256 SOFTWARE
""".format(ckv_1.Parent().RelativeName(),
           ckv_2.Parent().RelativeName(), key.RelativeName()),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
