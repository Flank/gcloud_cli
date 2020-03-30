# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise the 'gcloud kms keys versions import' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.kms import base


class ImportKeyVersionTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.rsa_aes_wrapped_key_path = self.Touch(
        self.temp_path,
        name='rsa_aes_wrapped_key_path',
        contents=b'Most secure key ever')
    self.import_job_name = self.project_name.ImportJob(
        'us-central1/my_kr/my_ij')
    self.version_name = self.project_name.Version('us-central1/my_kr/my_key/3')

  def testImportSuccess(self):
    self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Import.Expect(  # pylint: disable=line-too-long
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsImportRequest(  # pylint: disable=line-too-long
            parent=self.version_name.Parent().RelativeName(),
            importCryptoKeyVersionRequest=self.messages
            .ImportCryptoKeyVersionRequest(
                algorithm=self.messages.ImportCryptoKeyVersionRequest
                .AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
                importJob=self.import_job_name.RelativeName(),
                rsaAesWrappedKey=b'Most secure key ever')),
        self.messages.CryptoKeyVersion(name=self.version_name.RelativeName()))
    result = self.Run(
        'kms keys versions import --location={0} --keyring={1} --key={2} '
        '--import-job={3} --rsa-aes-wrapped-key-file={4} '
        '--algorithm=google-symmetric-encryption'
        .format(self.version_name.location_id, self.version_name.key_ring_id,
                self.version_name.crypto_key_id,
                self.import_job_name.RelativeName(),
                self.rsa_aes_wrapped_key_path))
    self.assertEqual(
        result,
        self.messages.CryptoKeyVersion(name=self.version_name.RelativeName()))

  def testMissingRsaAesWrappedKey(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.OneOfArgumentsRequiredException,
        'Either a pre-wrapped key or a key to be wrapped must be provided.'):
      self.Run('kms keys versions import --location={0} --keyring={1} '
               '--key={2} --import-job={3} '
               '--algorithm=google-symmetric-encryption'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id,
                   self.import_job_name.RelativeName()))

  def testMissingImportJob(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --import-job: Must be specified.'):
      self.Run(
          'kms keys versions import --location={0} --keyring={1} --key={2} '
          '--rsa-aes-wrapped-key-file={3} '
          '--algorithm=google-symmetric-encryption'.format(
              self.version_name.location_id, self.version_name.key_ring_id,
              self.version_name.crypto_key_id, self.rsa_aes_wrapped_key_path))

  def testMissingAlgorithm(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --algorithm: Must be specified.'):
      self.Run('kms keys versions import --location={0} --keyring={1} '
               '--key={2} --rsa-aes-wrapped-key-file={3} '
               '--import-job={4} '.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id,
                   self.rsa_aes_wrapped_key_path,
                   self.import_job_name.RelativeName()))

  def testRsaAesWrappedKeyTooLarge(self):
    long_rsa_aes_wrapped_key_path = self.Touch(
        self.temp_path, name='rsa_aes_wrapped_key_path',
        contents=b'a' * 65537)  # API limit is 65536
    with self.AssertRaisesExceptionMatches(
        exceptions.BadFileException,
        r'is larger than the maximum size of 65536 bytes.'):
      self.Run('kms keys versions import --location={0} --keyring={1} '
               '--key={2} --import-job={3} --rsa-aes-wrapped-key-file={4} '
               '--algorithm=google-symmetric-encryption'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id,
                   self.import_job_name.RelativeName(),
                   long_rsa_aes_wrapped_key_path))

  def testServerFailure(self):
    self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Import.Expect(  # pylint: disable=line-too-long
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsImportRequest(  # pylint: disable=line-too-long
            parent=self.version_name.Parent().RelativeName(),
            importCryptoKeyVersionRequest=self.messages
            .ImportCryptoKeyVersionRequest(
                algorithm=self.messages.ImportCryptoKeyVersionRequest
                .AlgorithmValueValuesEnum.GOOGLE_SYMMETRIC_ENCRYPTION,
                importJob=self.import_job_name.RelativeName(),
                rsaAesWrappedKey=b'Most secure key ever')),
        exception=http_error.MakeHttpError())
    with self.AssertRaisesExceptionMatches(exceptions.HttpException,
                                           'Invalid request'):
      self.Run('kms keys versions import --location={0} --keyring={1} '
               '--key={2} --import-job={3} --rsa-aes-wrapped-key-file={4} '
               '--algorithm=google-symmetric-encryption'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id,
                   self.import_job_name.RelativeName(),
                   self.rsa_aes_wrapped_key_path))


class ImportKeyVersionTestBeta(ImportKeyVersionTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ImportKeyVersionTestAlpha(ImportKeyVersionTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
