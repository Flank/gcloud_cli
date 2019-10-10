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
"""Tests that exercise the 'gcloud kms decrypt' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class KeysDecryptTest(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key')

  def testDecrypt(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents='foo bar')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    self.kms.projects_locations_keyRings_cryptoKeys.Decrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDecryptRequest(
            name=self.key_name.RelativeName(),
            decryptRequest=self.messages.DecryptRequest(ciphertext=b'foo bar')),
        response=self.messages.DecryptResponse(plaintext=b'decrypted foo bar'))

    self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path))

    self.AssertBinaryFileEquals(b'decrypted foo bar', pt_path)

  def testDecryptWithAad(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents=b'foo bar')
    aad_path = self.Touch(self.temp_path, name='aad', contents=b'authed data')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    self.kms.projects_locations_keyRings_cryptoKeys.Decrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDecryptRequest(
            name=self.key_name.RelativeName(),
            decryptRequest=self.messages.DecryptRequest(
                ciphertext=b'foo bar',
                additionalAuthenticatedData=b'authed data')),
        response=self.messages.DecryptResponse(plaintext=b'decrypted foo bar'))

    self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4} '
             '--additional-authenticated-data-file={5}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path, aad_path))

    self.AssertBinaryFileEquals(b'decrypted foo bar', pt_path)

  def testDecryptStdio(self):
    self.WriteBinaryInput(b'foo bar')

    self.kms.projects_locations_keyRings_cryptoKeys.Decrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDecryptRequest(
            name=self.key_name.RelativeName(),
            decryptRequest=self.messages.DecryptRequest(ciphertext=b'foo bar')),
        response=self.messages.DecryptResponse(plaintext=b'decrypted foo bar'))

    self.Run(
        'kms decrypt --location={0} --keyring={1} --key={2} --plaintext-file=- '
        '--ciphertext-file=-'.format(self.key_name.location_id,
                                     self.key_name.key_ring_id,
                                     self.key_name.crypto_key_id))

    self.AssertOutputBytesEquals(b'decrypted foo bar')

  def testDecryptMissingCiphertextFile(self):
    ct_path = os.path.join(self.temp_path, 'file-that-does-not-exist')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegex(
        exceptions.BadFileException,
        'Failed to read ciphertext file.*No such file'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testDecryptMissingAadFile(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents=b'foo bar')
    aad_path = os.path.join(self.temp_path, 'file-that-does-not-exist')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegex(
        exceptions.BadFileException,
        'Failed to read additional authenticated data file.*No such file'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4} '
               '--additional-authenticated-data-file={5}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path, aad_path))

  def testDecryptUnwritableOutput(self):
    ct_path = self.Touch(self.temp_path, name='plaintext', contents='foo bar')
    pt_path = os.path.join(self.temp_path, 'nested', 'nonexistent', 'file')

    self.kms.projects_locations_keyRings_cryptoKeys.Decrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDecryptRequest(
            name=self.key_name.RelativeName(),
            decryptRequest=self.messages.DecryptRequest(ciphertext=b'foo bar')),
        response=self.messages.DecryptResponse(plaintext=b'decrypted foo bar'))

    with self.AssertRaisesToolExceptionMatches('No such file or directory'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testDecryptMissingCiphertext(self):
    file_path = self.Touch(self.temp_path, name='foo')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --ciphertext-file: Must be specified.'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, file_path))

  def testDecryptMissingPlaintext(self):
    file_path = self.Touch(self.temp_path, name='foo')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --plaintext-file: Must be specified.'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--ciphertext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, file_path))

  def testDecryptTooLarge(self):
    contents = b'a' * 3 * 65536  # arbitrarily selected limit is 2*65536
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents=contents)
    pt_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegex(
        exceptions.BadFileException,
        r'is larger than the maximum size of 131072 bytes.'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path, ct_path))

  def testRejectCiphertextAndAadFromStdin(self):
    pt_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'--ciphertext-file.*--additional-authenticated-data-file'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--ciphertext-file=- --additional-authenticated-data-file=- '
               '--plaintext-file={3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, pt_path))

  def trestDecryptEmpty(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents='')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    self.kms.projects_locations_keyRings_cryptoKeys.Decrypt.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDecryptRequest(
            name=self.key_name.RelativeName(),
            decryptRequest=self.messages.DecryptRequest(ciphertext='')),
        response=self.messages.DecryptResponse(plaintext=''))

    self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
             '--plaintext-file={3} --ciphertext-file={4}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, pt_path, ct_path))

  def testInvalidDecryptWithCryptoKeyVersion(self):
    ct_path = self.Touch(self.temp_path, name='ciphertext', contents='')
    pt_path = self.Touch(self.temp_path, name='plaintext')

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for.*my_key/cryptoKeyVersions/1 includes '
        'cryptoKeyVersion which is not valid for decrypt.'):
      self.Run('kms decrypt --location={0} --keyring={1} --key={2} '
               '--plaintext-file={3} --ciphertext-file={4}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id + '/cryptoKeyVersions/1',
                   pt_path, ct_path))


class KeysDecryptTestBeta(KeysDecryptTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class KeysDecryptTestAlpha(KeysDecryptTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
