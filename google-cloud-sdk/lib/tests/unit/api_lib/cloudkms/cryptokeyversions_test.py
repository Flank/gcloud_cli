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
"""Tests for google3.third_party.py.tests.api_lib.cloudkms.cryptokeyversions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import cryptokeyversions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case


def GetCryptoKeyVersionRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys.cryptoKeyVersions'
  )


class CryptoKeyVersionsApiTest(sdk_test_base.WithFakeAuth):
  _VERSION_NAME = 'projects/my-project/locations/my-location/keyRings/my-key-ring/cryptoKeys/my-crypto-key/cryptoKeyVersions/1'

  def SetUp(self):
    self.messages = cloudkms_base.GetMessagesModule()
    self.mock_client = mock.Client(
        apis.GetClientClass(
            cloudkms_base.DEFAULT_API_NAME,
            cloudkms_base.DEFAULT_API_VERSION),
        real_client=cloudkms_base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.version_ref = GetCryptoKeyVersionRef(self._VERSION_NAME)

  def testGetCryptoKeyVersion(self):
    expected = self.messages.CryptoKeyVersion(name=self._VERSION_NAME)
    self.mock_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Get.Expect(
        request=self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self._VERSION_NAME),
        response=expected)

    actual = cryptokeyversions.Get(self.version_ref)
    self.assertEqual(actual.name, expected.name)

  def testGetPublicKey(self):
    expected = self.messages.PublicKey(
        pem='pem-public-key',
        algorithm=self.messages.PublicKey.AlgorithmValueValuesEnum
        .RSA_SIGN_PSS_2048_SHA256)
    self.mock_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        request=self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
            name=self._VERSION_NAME),
        response=expected)

    actual = cryptokeyversions.GetPublicKey(self.version_ref)
    self.assertEqual(actual.pem, expected.pem)
    self.assertEqual(actual.algorithm, expected.algorithm)


if __name__ == '__main__':
  test_case.main()
