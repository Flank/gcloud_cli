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
"""Tests that exercise the 'gcloud kms keys update' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.kms import base


class CryptoKeysUpdateTest(base.KmsMockTest):

  def SetUp(self):
    self.version_name = self.project_name.Descendant('global/my_kr/my_key/3')
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testLabelsOnly(self):
    # Test update labels.
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1')])),
            updateMask='labels'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1')])))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--update-labels=k1=v1'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

    # Test remove labels.
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName(),
        ),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k2', value='v2')])))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k2', value='v2')])),
            updateMask='labels'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--remove-labels=k1'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

    # Test clear labels.
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName(),
        ),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1'),
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k2', value='v2')])))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[])),
            updateMask='labels'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--clear-labels'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testUpdateNextRotationTimeOnly(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                nextRotationTime='2017-10-12T12:34:56.123Z'),
            updateMask='nextRotationTime'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            nextRotationTime='2017-10-12T12:34:56.1234Z'))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--next-rotation-time=2017-10-12T12:34:56.1234Z'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testUpdateRotationPeriodOnly(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(rotationPeriod='1296000s'),
            updateMask='rotationPeriod'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(), rotationPeriod='1296000s'))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--rotation-period=15d'.format(self.key_name.location_id,
                                            self.key_name.key_ring_id,
                                            self.key_name.crypto_key_id))

  def testUpdateBothRotationPeriodAndNextRotationTime(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

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

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--next-rotation-time="2017-10-12 12:00 UTC" '
             '--rotation-period=15d'.format(self.key_name.location_id,
                                            self.key_name.key_ring_id,
                                            self.key_name.crypto_key_id))

  def testUpdateBothRotationAndLabels(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                nextRotationTime='2017-10-12T12:00:00.000Z',
                rotationPeriod='1296000s',
                labels=self.messages.CryptoKey.LabelsValue(
                    additionalProperties=[
                        self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                            key='k1', value='v1')])),
            updateMask='labels,rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName(),
            nextRotationTime='2017-10-12T12:00:00.000Z',
            rotationPeriod='1296000s',
            labels=self.messages.CryptoKey.LabelsValue(
                additionalProperties=[
                    self.messages.CryptoKey.LabelsValue.AdditionalProperty(
                        key='k1', value='v1')])))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} '
             '--next-rotation-time="2017-10-12 12:00 UTC" '
             '--rotation-period=15d --update-labels=k1=v1'
             .format(self.key_name.location_id,
                     self.key_name.key_ring_id,
                     self.key_name.crypto_key_id))

  def testRemoveRotationSchedule(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(),
            updateMask='rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(name=self.key_name.RelativeName()))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} --remove-rotation-schedule'
             .format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))

  def testUpdatePrimaryVersion(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId=self.version_name.version_id))),
        self.messages.CryptoKey(name=self.version_name.Parent().RelativeName()))

    self.Run('kms keys update '
             '--location={0} --keyring={1} {2} --primary-version={3}'.format(
                 self.version_name.location_id, self.version_name.key_ring_id,
                 self.version_name.crypto_key_id, self.version_name.version_id))

  def testUpdatePrimaryVersionAndRemoveRotationSchedule(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId=self.version_name.version_id))),
        self.messages.CryptoKey(name=self.version_name.Parent().RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(),
            updateMask='rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(name=self.key_name.RelativeName()))

    self.Run('kms keys update --remove-rotation-schedule '
             '--location={0} --keyring={1} {2} --primary-version={3}'.format(
                 self.version_name.location_id, self.version_name.key_ring_id,
                 self.version_name.crypto_key_id, self.version_name.version_id))

  def testUpdatePrimaryVersionFailedRaisesError(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId='10'))),
        exception=http_error.MakeHttpError()
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'An Error occurred: Failed to update field \'primaryVersion\'.'):
      self.Run('kms keys update '
               '--location={0} --keyring={1} {2} --primary-version=10'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id))

  def testRaisesErrorWhenUpdatesArePartiallyFailed(self):
    # When primary-version is failed to update while other updates succeed.
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId='10'))),
        exception=http_error.MakeHttpError())

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(),
            updateMask='rotationPeriod,nextRotationTime'),
        self.messages.CryptoKey(name=self.key_name.RelativeName()))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'An Error occurred: Failed to update field \'primaryVersion\'. '
        'Field(s) \'rotationPeriod\', \'nextRotationTime\' were updated.'):
      self.Run('kms keys update --remove-rotation-schedule '
               '--location={0} --keyring={1} {2} --primary-version=10'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id))

    # When primary-version is updated while other updates fail.
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId=self.version_name.version_id))),
        self.messages.CryptoKey(name=self.version_name.Parent().RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                rotationPeriod='864000s'),
            updateMask='rotationPeriod'),
        exception=http_error.MakeHttpError())

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'An Error occurred: Field \'primaryVersion\' was updated. '
        'Failed to update field(s) \'rotationPeriod\'.'):
      self.Run('kms keys update --rotation-period=10d '
               '--location={0} --keyring={1} {2} --primary-version={3}'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, self.version_name.version_id
               ))

  def testRaisesErrorWhenAllUpdatesFailed(self):
    self.kms.projects_locations_keyRings_cryptoKeys.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=self.key_name.RelativeName()),
        self.messages.CryptoKey(
            name=self.key_name.RelativeName()))

    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId='10'))),
        exception=http_error.MakeHttpError())

    self.kms.projects_locations_keyRings_cryptoKeys.Patch.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
            name=self.key_name.RelativeName(),
            cryptoKey=self.messages.CryptoKey(
                rotationPeriod='864000s'
            ),
            updateMask='rotationPeriod'),
        exception=http_error.MakeHttpError())

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'An Error occurred: Failed to update field \'primaryVersion\'. '
        'Failed to update field(s) \'rotationPeriod\'.'):
      self.Run('kms keys update --rotation-period=10d '
               '--location={0} --keyring={1} {2} --primary-version=10'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id))

  def testSetAndRemoveRotationScheduleRaisesError(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'You cannot set and remove rotation schedule at the same time.'):
      self.Run('kms keys update '
               '--location={0} --keyring={1} {2} '
               '--next-rotation-time=2017-10-12T12:34:56.1234Z '
               '--remove-rotation-schedule'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'You cannot set and remove rotation schedule at the same time.'):
      self.Run('kms keys update '
               '--location={0} --keyring={1} {2} '
               '--rotation-period=7d '
               '--remove-rotation-schedule'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'You cannot set and remove rotation schedule at the same time.'):
      self.Run('kms keys update '
               '--location={0} --keyring={1} {2} '
               '--next-rotation-time=2017-10-12T12:34:56.1234Z '
               '--rotation-period=7d '
               '--remove-rotation-schedule'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

  def testNoUpdateFieldsSpecifiedRaisesError(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'At least one of --primary-version or --update-labels or --remove-'
        'labels or --clear-labels or --rotation-period or --next-rotation-time '
        'or --remove-rotation-schedule must be specified.'):
      self.Run('kms keys update --location={0} --keyring={1} {2}'.format(
          self.key_name.location_id, self.key_name.key_ring_id,
          self.key_name.crypto_key_id))

if __name__ == '__main__':
  test_case.main()
