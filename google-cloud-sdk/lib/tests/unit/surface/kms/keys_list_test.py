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

from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysListTest(base.KmsMockTest):

  def testList(self):
    key_1 = self.project_name.Descendant('global/my_kr/my_key1')
    key_2 = self.project_name.Descendant('global/my_kr/my_key2/my_version2')
    key_with_labels = self.project_name.Descendant('global/my_kr/my_key')

    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=key_with_labels.Parent().RelativeName(),
            cryptoKeyId=key_with_labels.crypto_key_id,
            cryptoKey=self.messages.CryptoKey(
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k-2', value='v-2'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1')]))),
        self.messages.CryptoKey(
            name=key_with_labels.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k-2', value='v-2')])))

    self.Run('kms keys create '
             '--location={0} --keyring={1} {2} --purpose=encryption '
             '--labels=k1=v1,k-2=v-2'.format(
                 key_with_labels.location_id, key_with_labels.key_ring_id,
                 key_with_labels.crypto_key_id))

    self.kms.projects_locations_keyRings_cryptoKeys.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysListRequest(
            pageSize=100, parent=key_1.Parent().RelativeName()),
        self.messages.ListCryptoKeysResponse(cryptoKeys=[
            self.messages.CryptoKey(
                name=key_1.RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT),
            self.messages.CryptoKey(
                name=key_2.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                primary=self.messages.CryptoKeyVersion(
                    name=key_2.RelativeName(),
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
                            key='k-2', value='v-2')]))
        ]))

    self.Run('kms keys list --location={0} --keyring {1}'.format(
        key_1.location_id, key_1.key_ring_id))
    self.AssertOutputContains(
        """NAME PURPOSE LABELS PRIMARY_ID PRIMARY_STATE
{0} ENCRYPT_DECRYPT
{1} ENCRYPT_DECRYPT my_version2 ENABLED
{2} ENCRYPT_DECRYPT k-2=v-2,k1=v1
""".format(key_1.RelativeName(), key_2.Parent().RelativeName(),
           key_with_labels.RelativeName()), normalize_space=True)

  def testListParentFlag(self):
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

    self.Run(
        'kms keys list --keyring {0}'.format(key_1.Parent().RelativeName()))
    self.AssertOutputContains(
        """NAME PURPOSE LABELS PRIMARY_ID PRIMARY_STATE
{0} ENCRYPT_DECRYPT
""".format(key_1.RelativeName()),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
