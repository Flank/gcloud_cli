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
"""Tests that exercise the 'gcloud kms keys versions list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysVersionsListTest(base.KmsMockTest):

  def testList(self, track):
    self.track = track
    version_1 = self.project_name.Descendant('global/my_kr/my_key/1')
    version_2 = self.project_name.Descendant('global/my_kr/my_key/2')

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.List.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsListRequest(
            pageSize=100,
            parent=version_1.Parent().RelativeName()),
        self.messages.ListCryptoKeyVersionsResponse(cryptoKeyVersions=[
            self.messages.CryptoKeyVersion(
                name=version_1.RelativeName(),
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                ENABLED),
            self.messages.CryptoKeyVersion(
                name=version_2.RelativeName(),
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                DISABLED)
        ]))

    self.Run('kms keys versions list --location={0} --keyring {1} '
             '--key {2}'.format(version_1.location_id, version_1.key_ring_id,
                                version_1.crypto_key_id))
    self.AssertOutputContains(
        """NAME STATE
{0} ENABLED
{1} DISABLED
""".format(version_1.RelativeName(), version_2.RelativeName()),
        normalize_space=True)

  def testListParentFlag(self, track):
    self.track = track
    version_1 = self.project_name.Descendant('global/my_kr/my_key/1')

    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.List.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsListRequest(
            pageSize=100, parent=version_1.Parent().RelativeName()),
        self.messages.ListCryptoKeyVersionsResponse(cryptoKeyVersions=[
            self.messages.CryptoKeyVersion(
                name=version_1.RelativeName(),
                state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                ENABLED)
        ]))

    self.Run('kms keys versions list --key {0}'.format(
        version_1.Parent().RelativeName()))
    self.AssertOutputContains(
        """NAME STATE
{0} ENABLED
""".format(version_1.RelativeName()),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
