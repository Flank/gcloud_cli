# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for parallel Google Cloud Storage operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os
import re

from dateutil import tz

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


_DUMMY_X509_CERT_CONTENTS = """\
-----BEGIN CERTIFICATE-----
BEEFDEAD
-----END CERTIFICATE-----
"""
_DUMMY_RSA_FILE_CONTENTS = """\
-----BEGIN CERTIFICATE-----
DEADBEEF
-----END CERTIFICATE-----
"""
_DUMMY_ECDSA_FILE_CONTENTS = """\
-----BEGIN PUBLIC KEY-----
FACECAFE
-----END PUBLIC KEY-----
"""


class ParseCredentialsTest(test_case.Base):

  def SetUp(self):
    self.messages = devices.GetMessagesModule(
        devices.GetClientInstance(no_http=True))
    self.StartObjectPatch(times, 'LOCAL', tz.tzutc())

    self.format_enum = self.messages.PublicKeyCredential.FormatValueValuesEnum

    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)

    self.rsa_key_path = self.Touch(self.temp_path, 'id_rsa.pub',
                                   contents=_DUMMY_RSA_FILE_CONTENTS)
    self.ecdsa_key_path = self.Touch(self.temp_path, 'id_ecdsa.pub',
                                     contents=_DUMMY_ECDSA_FILE_CONTENTS)
    self.bad_key_path = os.path.join(self.temp_path, 'bad.pub')

  def testParseCredentials_Empty(self):
    self.assertEqual(
        util.ParseCredentials([], messages=self.messages),
        [])

  def testParseCredentials_TooManyValues(self):
    with self.assertRaisesRegex(
        util.InvalidPublicKeySpecificationError,
        re.escape('Too many public keys specified: [4] given, '
                  'but maximum [3] allowed.')):
      util.ParseCredentials([
          {'type': 'rsa-x509-pem', 'path': self.rsa_key_path},
          {'type': 'es256-pem', 'path': self.ecdsa_key_path},
          {'type': 'rsa-x509-pem', 'path': self.rsa_key_path},
          {'type': 'es256-pem', 'path': self.ecdsa_key_path}
      ], messages=self.messages)

  def testParseCredentials_MissingRequiredKey(self):
    with self.assertRaisesRegex(
        util.InvalidPublicKeySpecificationError,
        re.escape('--public-key argument missing value for `path`')):
      util.ParseCredentials([
          {'type': 'rsa-x509-pem'}
      ], messages=self.messages)

    with self.assertRaisesRegex(
        util.InvalidPublicKeySpecificationError,
        re.escape('--public-key argument missing value for `type`')):
      util.ParseCredentials([
          {'path': self.rsa_key_path}
      ], messages=self.messages)

  def testParseCredentials_ExtraInvalidKeys(self):
    with self.assertRaisesRegex(
        TypeError,
        (r'Unrecognized keys \[badkey[12], badkey[12]] for public key '
         r'specification')):
      util.ParseCredentials([
          {'type': 'rsa-x509-pem', 'path': self.rsa_key_path,
           'badkey1': None, 'badkey2': None},
      ], messages=self.messages)

  def testParseCredentials_BadKeyType(self):
    with self.assertRaisesRegex(
        ValueError,
        re.escape('Invalid key type [invalid-type]')):
      util.ParseCredentials([
          {'type': 'invalid-type', 'path': self.rsa_key_path},
      ], messages=self.messages)

  def testParseCredentials_OneKey(self):
    self.assertEqual(
        util.ParseCredentials([
            {'type': 'rsa-x509-pem', 'path': self.rsa_key_path}
        ], messages=self.messages),
        [
            self.messages.DeviceCredential(
                publicKey=self.messages.PublicKeyCredential(
                    format=self.format_enum.RSA_X509_PEM,
                    key=_DUMMY_RSA_FILE_CONTENTS
                )
            )
        ])

  def testParseCredentials_RsaKeyUnreadableKeyFile(self):
    with self.assertRaisesRegex(
        util.InvalidKeyFileError,
        re.escape(
            ('Could not read key file [{}]:').format(self.bad_key_path))):
      util.ParseCredentials(
          [{'type': 'rsa-x509-pem', 'path': self.bad_key_path}],
          messages=self.messages)

  def testParseCredentials_MultipleKeys(self):
    self.assertEqual(
        util.ParseCredentials([
            {'type': 'es256-pem', 'path': self.ecdsa_key_path},
            {'type': 'rsa-x509-pem', 'path': self.rsa_key_path}
        ], messages=self.messages),
        [
            self.messages.DeviceCredential(
                publicKey=self.messages.PublicKeyCredential(
                    format=self.format_enum.ES256_PEM,
                    key=_DUMMY_ECDSA_FILE_CONTENTS
                )
            ),
            self.messages.DeviceCredential(
                publicKey=self.messages.PublicKeyCredential(
                    format=self.format_enum.RSA_X509_PEM,
                    key=_DUMMY_RSA_FILE_CONTENTS
                )
            )
        ])


class ParseCredentialTest(test_case.Base):

  def SetUp(self):
    self.messages = devices.GetMessagesModule(
        devices.GetClientInstance(no_http=True))
    self.StartObjectPatch(times, 'LOCAL', tz.tzutc())

    self.format_enum = self.messages.PublicKeyCredential.FormatValueValuesEnum

    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)

    self.rsa_key_path = self.Touch(self.temp_path, 'id_rsa.pub',
                                   contents=_DUMMY_RSA_FILE_CONTENTS)
    self.ecdsa_key_path = self.Touch(self.temp_path, 'id_ecdsa.pub',
                                     contents=_DUMMY_ECDSA_FILE_CONTENTS)
    self.bad_key_path = os.path.join(self.temp_path, 'bad.pub')

  def testParseCredential_MissingRequiredKey(self):
    with self.assertRaisesRegex(ValueError, 'path is required'):
      util.ParseCredential(None, 'rsa-x509-pem', messages=self.messages)

    with self.assertRaisesRegex(ValueError,
                                re.escape('Invalid key type [None]')):
      util.ParseCredential(self.rsa_key_path, None, messages=self.messages)

  def testParseCredential_BadKeyType(self):
    with self.assertRaisesRegex(
        ValueError,
        re.escape('Invalid key type [invalid-type]')):
      util.ParseCredential(self.rsa_key_path, 'invalid-type',
                           messages=self.messages)

  def testParseCredential_RsaKey(self):
    self.assertEqual(
        util.ParseCredential(self.rsa_key_path, 'rsa-x509-pem',
                             messages=self.messages),
        self.messages.DeviceCredential(
            publicKey=self.messages.PublicKeyCredential(
                format=self.format_enum.RSA_X509_PEM,
                key=_DUMMY_RSA_FILE_CONTENTS)))

  def testParseCredential_RsaKeyExpirationTime(self):
    self.assertEqual(
        util.ParseCredential(self.rsa_key_path, 'rsa-x509-pem',
                             expiration_time=datetime.datetime(2017, 1, 1),
                             messages=self.messages),
        self.messages.DeviceCredential(
            expirationTime='2017-01-01T00:00:00.000',
            publicKey=self.messages.PublicKeyCredential(
                format=self.format_enum.RSA_X509_PEM,
                key=_DUMMY_RSA_FILE_CONTENTS)))

  def testParseCredential_RsaKeyUnreadableKeyFile(self):
    with self.assertRaisesRegex(
        util.InvalidKeyFileError,
        re.escape(
            ('Could not read key file [{}]:').format(self.bad_key_path))):
      util.ParseCredential(self.bad_key_path, 'rsa-x509-pem',
                           messages=self.messages)

  def testParseCredential_EcdsaKey(self):
    self.assertEqual(
        util.ParseCredential(self.ecdsa_key_path, 'es256-pem',
                             messages=self.messages),
        self.messages.DeviceCredential(
            publicKey=self.messages.PublicKeyCredential(
                format=self.format_enum.ES256_PEM,
                key=_DUMMY_ECDSA_FILE_CONTENTS)))

  def testParseCredential_EcdsaKeyExpirationTime(self):
    self.assertEqual(
        util.ParseCredential(self.ecdsa_key_path, 'es256-pem',
                             expiration_time=datetime.datetime(2017, 1, 1),
                             messages=self.messages),
        self.messages.DeviceCredential(
            expirationTime='2017-01-01T00:00:00.000',
            publicKey=self.messages.PublicKeyCredential(
                format=self.format_enum.ES256_PEM,
                key=_DUMMY_ECDSA_FILE_CONTENTS)))

  def testParseCredential_EcdsaKeyUnreadableKeyFile(self):
    with self.assertRaisesRegex(
        util.InvalidKeyFileError,
        re.escape(
            ('Could not read key file [{}]:').format(self.bad_key_path))):
      util.ParseCredential(self.bad_key_path, 'es256-pem',
                           messages=self.messages)


class ParseRegistryCredentialsTest(test_case.Base):

  def SetUp(self):
    self.messages = devices.GetMessagesModule(
        devices.GetClientInstance(no_http=True))

    self.format_enum = self.messages.PublicKeyCertificate.FormatValueValuesEnum

    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)

  def _CreateRegistryCredential(self, contents):
    return self.messages.RegistryCredential(
        publicKeyCertificate=self.messages.PublicKeyCertificate(
            certificate=contents,
            format=self.format_enum.X509_CERTIFICATE_PEM))

  def testParseRegistryCredential_UnreadableKeyFile(self):
    bad_key_path = os.path.join(self.temp_path, 'bad.pub')
    with self.assertRaisesRegex(
        util.InvalidKeyFileError,
        re.escape(
            ('Could not read key file [{}]:').format(bad_key_path))):
      util.ParseRegistryCredential(bad_key_path, messages=self.messages)

  def testParseRegistryCredential(self):
    public_key_path = self.Touch(self.temp_path, 'cert1.pub',
                                 contents=_DUMMY_X509_CERT_CONTENTS)
    self.assertEqual(
        self._CreateRegistryCredential(_DUMMY_X509_CERT_CONTENTS),
        util.ParseRegistryCredential(public_key_path,
                                     messages=self.messages))


class ParseMetadataTest(test_case.Base, parameterized.TestCase):

  def SetUp(self):
    self.messages = devices.GetMessagesModule(
        devices.GetClientInstance(no_http=True))

    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)

  def _CreateMetadataValueFile(self, file_name, contents):
    return self.Touch(self.temp_path, file_name, contents=contents)

  def _CreateAdditionalProperty(self, key, value):
    return self.messages.Device.MetadataValue.AdditionalProperty(key=key,
                                                                 value=value)

  @parameterized.parameters(
      (None, None),
      (None, {}),
      ({}, None),
      ({}, {}),
  )
  def testParseMetadata_Empty(self, metadata, metadata_from_file):
    self.assertEqual(
        None, util.ParseMetadata(metadata, metadata_from_file, self.messages))

  def testParseMetadata_TooManyKeys(self):
    metadata = dict([(str(i), str(i)) for i in range(501)])
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Maximum number of metadata key-value pairs is 500.'):
      util.ParseMetadata(metadata, None, self.messages)

  def testParseMetadata_OverlappingKeys(self):
    metadata = {'key1': 'value1', 'key2': 'value2'}
    metadata_from_file = {'key1': 'value3', 'key3': 'value4'}
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Cannot specify the same key in both '
        r'--metadata and --metadata-from-file'):
      util.ParseMetadata(metadata, metadata_from_file, self.messages)

  def testParseMetadata_ValueTooBig(self):
    value = 'a' * (32 * 1024 + 1)  # Value must be <= 32 KB in size.
    metadata = {'key': value}
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Maximum size of metadata values are 32KB'):
      util.ParseMetadata(metadata, None, self.messages)

  def testParseMetadata_ValueFromFileTooBig(self):
    value = 'a' * (32 * 1024 + 1)  # Value must be <= 32 KB in size.
    path = self._CreateMetadataValueFile('value.txt', value)
    metadata_from_file = {'key': path}
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Maximum size of metadata values are 32KB'):
      util.ParseMetadata(None, metadata_from_file, self.messages)

  def testParseMetadata_ValueFromEmptyFile(self):
    value = ''
    path = self._CreateMetadataValueFile('value.txt', value)
    metadata_from_file = {'key': path}
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Metadata value cannot be empty'):
      util.ParseMetadata(None, metadata_from_file, self.messages)

  def testParseMetadata_FileDoesntExist(self):
    path = 'fake/value.txt'
    metadata_from_file = {'key': path}
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Could not read value file'):
      util.ParseMetadata(None, metadata_from_file, self.messages)

  def testParseMetadata_TotalSizeTooBig(self):
    value = 'a' * (26 * 1024)
    metadata = dict([(str(i), value) for i in range(10)])
    with self.assertRaisesRegex(
        util.InvalidMetadataError,
        r'Maximum size of metadata key-value pairs is 256KB'):
      util.ParseMetadata(metadata, None, self.messages)

  def testParseMetadata_NoFromFile(self):
    metadata = {'key': 'value'}
    result = util.ParseMetadata(metadata, None, self.messages)
    expected = self.messages.Device.MetadataValue(
        additionalProperties=[
            self._CreateAdditionalProperty('key', 'value')])
    self.assertEqual(result, expected)

  def testParseMetadata_OnlyFromFile(self):
    path = self._CreateMetadataValueFile('value.txt', 'value')
    metadata_from_file = {'key': path}
    result = util.ParseMetadata(None, metadata_from_file, self.messages)
    expected = self.messages.Device.MetadataValue(
        additionalProperties=[
            self._CreateAdditionalProperty('key', 'value')])
    self.assertEqual(result, expected)

  def testParseMetadata_FromBothSources(self):
    metadata = {'key1': 'value'}
    path = self._CreateMetadataValueFile('value.txt', 'file_value')
    metadata_from_file = {'key2': path}
    result = util.ParseMetadata(metadata, metadata_from_file, self.messages)
    expected = self.messages.Device.MetadataValue(
        additionalProperties=[
            self._CreateAdditionalProperty('key1', 'value'),
            self._CreateAdditionalProperty('key2', 'file_value')])
    self.assertEqual(result, expected)


if __name__ == '__main__':
  test_case.main()
