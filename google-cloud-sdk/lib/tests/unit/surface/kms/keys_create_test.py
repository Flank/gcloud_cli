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
"""Tests that exercise the 'gcloud kms keys create' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class KeysCreateTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')
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
                            key='k1', value='v1'),
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='smile', value='happy')]))),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
            ENCRYPT_DECRYPT,
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k-2', value='v-2'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='smile', value='happy')])))

  def testCreate(self, track):
    self.track = track
    self.Run('kms keys create '
             '--location={0} --keyring={1} {2} --purpose=encryption '
             '--labels=k1=v1,k-2=v-2 --labels=smile=happy'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testCreateFullName(self, track):
    self.track = track
    self.Run('kms keys create {0} --purpose=encryption --labels=k1=v1,k-2=v-2 '
             '--labels=smile=happy'.format(self.key_name.RelativeName()))


if __name__ == '__main__':
  test_case.main()
