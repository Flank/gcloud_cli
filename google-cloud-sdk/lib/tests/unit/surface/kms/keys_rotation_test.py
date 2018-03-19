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
"""Tests that exercise rotation-related 'gcloud kms keys *' commands."""

from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysRotationTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testSetNextOnly(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                nextRotationTime='2017-10-12T12:34:56.123Z'),
            updateMask='nextRotationTime'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            nextRotationTime='2017-10-12T12:34:56.1234Z'))

    self.Run('kms keys set-rotation-schedule '
             '--location={0} --keyring={1} {2} '
             '--next-rotation-time=2017-10-12T12:34:56.1234Z'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testSetPeriodOnly(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(rotationPeriod='1296000s'),
            updateMask='rotationPeriod'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(), rotationPeriod='1296000s'))

    self.Run('kms keys set-rotation-schedule '
             '--location={0} --keyring={1} {2} '
             '--rotation-period=15d'.format(self.key_name.location_id,
                                            self.key_name.key_ring_id,
                                            self.key_name.crypto_key_id))

  def testSetBoth(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                nextRotationTime='2017-10-12T12:00:00.000Z',
                rotationPeriod='1296000s'),
            updateMask='rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            nextRotationTime='2017-10-12T12:00:00.000Z',
            rotationPeriod='1296000s'))

    self.Run('kms keys set-rotation-schedule '
             '--location={0} --keyring={1} {2} '
             '--next-rotation-time="2017-10-12 12:00 UTC" '
             '--rotation-period=15d'.format(self.key_name.location_id,
                                            self.key_name.key_ring_id,
                                            self.key_name.crypto_key_id))

  def testRemove(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(),
            updateMask='rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(name=self.key_name.RelativeName()))

    self.Run('kms keys remove-rotation-schedule '
             '--location={0} --keyring={1} {2} '.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))


if __name__ == '__main__':
  test_case.main()
