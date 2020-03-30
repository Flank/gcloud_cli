# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.kms."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import cryptokeyversions
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.command_lib.privateca import kms
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case

import mock

_KEY_VERSION_NAME = 'projects/p1/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1'


def GetCryptoKeyVersionRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys.cryptoKeyVersions'
  )


class KmsUtilsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    privateca_messages = privateca_base.GetMessagesModule()
    self.privateca_key_type = privateca_messages.PublicKey.TypeValueValuesEnum
    self.kms_messages = cloudkms_base.GetMessagesModule()
    self.version_ref = GetCryptoKeyVersionRef(_KEY_VERSION_NAME)

  @mock.patch.object(cryptokeyversions, 'GetPublicKey', autospec=True)
  def testGetPublicKeySucceedsWithRsaKey(self, mock_fn):
    pem_public_key = 'pem-public-key'
    mock_fn.return_value = self.kms_messages.PublicKey(
        algorithm=self.kms_messages.PublicKey.AlgorithmValueValuesEnum
        .RSA_SIGN_PSS_2048_SHA256,
        pem=pem_public_key)

    result = kms.GetPublicKey(self.version_ref)
    self.assertEqual(result.key, pem_public_key.encode('utf-8'))
    self.assertEqual(result.type, self.privateca_key_type.PEM_RSA_KEY)

  @mock.patch.object(cryptokeyversions, 'GetPublicKey', autospec=True)
  def testGetPublicKeySucceedsWithEcKey(self, mock_fn):
    pem_public_key = 'pem-public-key'
    mock_fn.return_value = self.kms_messages.PublicKey(
        algorithm=self.kms_messages.PublicKey.AlgorithmValueValuesEnum
        .EC_SIGN_P256_SHA256,
        pem=pem_public_key)

    result = kms.GetPublicKey(self.version_ref)
    self.assertEqual(result.key, pem_public_key.encode('utf-8'))
    self.assertEqual(result.type, self.privateca_key_type.PEM_EC_KEY)

  @mock.patch.object(cryptokeyversions, 'GetPublicKey', autospec=True)
  def testGetPublicKeyFailsWithUnsupportedKeyType(self, mock_fn):
    pem_public_key = 'pem-public-key'
    mock_fn.return_value = self.kms_messages.PublicKey(
        algorithm=self.kms_messages.PublicKey.AlgorithmValueValuesEnum
        .GOOGLE_SYMMETRIC_ENCRYPTION,
        pem=pem_public_key)

    with self.assertRaises(exceptions.UnsupportedKmsKeyTypeException):
      kms.GetPublicKey(self.version_ref)


if __name__ == '__main__':
  test_case.main()
