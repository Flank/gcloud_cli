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
"""Tests that exercise the 'gcloud kms keys describe' command."""

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysDescribeTest(base.KmsMockTest):

  def SetUp(self):
    self.kr_name = self.project_name.Descendant('global/my_kr')
    self.key_name = self.kr_name.Descendant('my_key')

  def testDescribe(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            parent=self.key_name.Parent().RelativeName(),
            cryptoKeyId=self.key_name.crypto_key_id,
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
            name=self.key_name.RelativeName(),
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
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k-2', value='v-2')])))

    self.Run('kms keys describe {0} --location={1} --keyring={2}'
             .format(self.key_name.crypto_key_id, self.key_name.location_id,
                     self.key_name.key_ring_id))

    self.AssertOutputContains(
        'name: {0}'.format(self.key_name.RelativeName()), normalize_space=True)

  def testMissingId(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [key]: key id must be non-empty.'):
      self.Run('kms keys describe {0}/cryptoKeys/'
               .format(self.kr_name.RelativeName()))

if __name__ == '__main__':
  test_case.main()
