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
"""Tests that exercise the 'gcloud kms asymmetric-decrypt' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class AsymmetricDecryptTestGa(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.version_name = self.project_name.Version('global/my_kr/my_key/2')

  def testAsymmetricDecryptSuccess(self):
    ciphertext_path = self.Touch(
        self.temp_path, name='ciphertext', contents='foo bar')
    plaintext_path = self.Touch(self.temp_path, name='plaintext')

    (self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.
     AsymmetricDecrypt.Expect(
         self.messages.
         CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricDecryptRequest(  # pylint: disable=line-too-long
             name=self.version_name.RelativeName(),
             asymmetricDecryptRequest=self.messages.AsymmetricDecryptRequest(
                 ciphertext=b'foo bar')),
         response=self.messages.AsymmetricDecryptResponse(
             plaintext=b'Hello 2018\\o/\\o/\\o/')))

    self.Run('kms asymmetric-decrypt --location={location} --keyring={keyring}'
             ' --key={key} --version=2 --ciphertext-file={ciphertext} '
             '--plaintext-file={plaintext}'.format(
                 location=self.version_name.location_id,
                 keyring=self.version_name.key_ring_id,
                 key=self.version_name.crypto_key_id,
                 ciphertext=ciphertext_path,
                 plaintext=plaintext_path))

    self.AssertBinaryFileEquals(b'Hello 2018\\o/\\o/\\o/', plaintext_path)

  def testAsymmetricDecryptStdioSuccess(self):
    self.WriteBinaryInput(b'foo bar')

    (self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.
     AsymmetricDecrypt.Expect(
         self.messages.
         CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricDecryptRequest(  # pylint: disable=line-too-long
             name=self.version_name.RelativeName(),
             asymmetricDecryptRequest=self.messages.AsymmetricDecryptRequest(
                 ciphertext=b'foo bar')),
         response=self.messages.AsymmetricDecryptResponse(
             plaintext=b'Hello 2018\\o/\\o/\\o/')))

    self.Run('kms asymmetric-decrypt --location={location} '
             '--keyring={keyring} --key={key} --version=2 '
             '--ciphertext-file=- --plaintext-file=-'.format(
                 location=self.version_name.location_id,
                 keyring=self.version_name.key_ring_id,
                 key=self.version_name.crypto_key_id))

  def testAsymmetricDecryptMissingCipherFile(self):
    ciphertext_path = os.path.join(self.temp_path, 'file-that-does-not-exist')
    plaintext_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        'Failed to read ciphertext file.*No such file'):
      self.Run(
          'kms asymmetric-decrypt --location={location} '
          '--keyring={keyring} --key={key} --version=2 '
          '--ciphertext-file={ciphertext} --plaintext-file={plaintext}'.format(
              location=self.version_name.location_id,
              keyring=self.version_name.key_ring_id,
              key=self.version_name.crypto_key_id,
              ciphertext=ciphertext_path,
              plaintext=plaintext_path))

  def testAsymmetricDecryptMissingCiphertext(self):
    file_path = self.Touch(self.temp_path, name='foo')

    with self.AssertRaisesArgumentErrorMatches(
        'argument --ciphertext-file: Must be specified.'):
      self.Run('kms asymmetric-decrypt --location={location} '
               '--keyring={keyring} --key={key} --version=2 '
               '--plaintext-file={plaintext}'.format(
                   location=self.version_name.location_id,
                   keyring=self.version_name.key_ring_id,
                   key=self.version_name.crypto_key_id,
                   plaintext=file_path))

  def testAsymmetricDecryptMissingPlaintext(self):
    file_path = self.Touch(self.temp_path, name='foo')

    with self.AssertRaisesArgumentErrorMatches(
        'argument --plaintext-file: Must be specified.'):
      self.Run('kms asymmetric-decrypt --location={location} '
               '--keyring={keyring} --key={key} --version=2 '
               '--ciphertext-file={ciphertext}'.format(
                   location=self.version_name.location_id,
                   keyring=self.version_name.key_ring_id,
                   key=self.version_name.crypto_key_id,
                   ciphertext=file_path))


class AsymmetricDecryptTestBeta(AsymmetricDecryptTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class AsymmetricDecryptTestAlpha(AsymmetricDecryptTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
