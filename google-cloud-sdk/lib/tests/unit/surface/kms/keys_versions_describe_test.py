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
"""Tests that exercise 'gcloud kms keys versions describe'."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysVersionsDescribeTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key/')
    self.version_name = self.key_name.Descendant('3')

  def testDescribe(self, track):
    self.track = track
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    ckv.Get.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()),
        self.messages.CryptoKeyVersion(name=self.version_name.RelativeName()))

    self.Run('kms keys versions describe {0} --location={1} '
             '--keyring={2} --key={3}'.format(
                 self.version_name.version_id, self.version_name.location_id,
                 self.version_name.key_ring_id,
                 self.version_name.crypto_key_id))

    self.AssertOutputContains(
        'name: {0}'.format(self.version_name.RelativeName()),
        normalize_space=True)

  def testMissingId(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [version]: version id must be non-empty.'):
      self.Run('kms keys versions describe {0}/cryptoKeyVersions/'
               .format(self.key_name.RelativeName()))

if __name__ == '__main__':
  test_case.main()
