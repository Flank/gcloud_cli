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
"""Tests that exercise the 'gcloud kms keys describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysDescribeTest(base.KmsMockTest):

  def SetUp(self):
    self.kr_name = self.project_name.Descendant('global/my_kr')
    self.key_name = self.kr_name.Descendant('my_key')
    self.version_name = self.project_name.Descendant('global/my_kr/my_key/1')

  def testDescribeSuccess(self, track):
    self.track = track

    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(additionalProperties=[
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k1', value='v1'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k-2', value='v-2')
            ])))

    self.Run('kms keys describe {0} --location={1} --keyring={2}'.format(
        self.key_name.crypto_key_id, self.key_name.location_id,
        self.key_name.key_ring_id))

    self.AssertOutputContains(
        'name: {}'.format(self.key_name.RelativeName()), normalize_space=True)
    # assert that the attestation field is empty.
    self.AssertOutputNotContains('attestation: ')

  def testMissingId(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [key]: key id must be non-empty.'):
      self.Run('kms keys describe {}/cryptoKeys/'
               .format(self.kr_name.RelativeName()))


class CryptokeysDescribeAlphaTest(base.KmsMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.kr_name = self.project_name.Descendant('global/my_kr')
    self.key_name = self.kr_name.Descendant('my_key')
    self.version_name = self.project_name.Descendant('global/my_kr/my_key/1')

  def testDescribeHsmKeySuccess(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(additionalProperties=[
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k1', value='v1'),
                self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                    key='k-2', value='v-2')
            ]),
            primary=self.messages.CryptoKeyVersion(
                name=self.version_name.RelativeName(),
                algorithm=self.messages.CryptoKeyVersion.
                AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
                protectionLevel=self.messages.CryptoKeyVersion.
                ProtectionLevelValueValuesEnum.HSM,
                attestation=self.messages.KeyOperationAttestation(
                    format=self.messages.KeyOperationAttestation.
                    FormatValueValuesEnum.CAVIUM_V1_COMPRESSED,
                    content=b'attestation content'))))

    self.Run('kms keys describe {0} --location={1} --keyring={2}'.format(
        self.key_name.crypto_key_id, self.key_name.location_id,
        self.key_name.key_ring_id))

    self.AssertOutputContains('protectionLevel: HSM')
    self.AssertOutputContains('algorithm: GOOGLE_SYMMETRIC_ENCRYPTION')
    self.AssertOutputNotContains('format:')
    self.AssertOutputNotContains('content:')


if __name__ == '__main__':
  test_case.main()
