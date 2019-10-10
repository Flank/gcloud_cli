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

"""Unit tests for kms flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.kms import flags
from tests.lib import completer_test_base
from tests.lib.surface.kms import base


class CompletionTest(base.KmsMockTest, completer_test_base.CompleterBase):

  def testLocationCompletion(self):
    glbl = self.project_name.Location('global')
    east = self.project_name.Location('us-east1')

    self.kms.projects_locations.List.Expect(
        self.messages.CloudkmsProjectsLocationsListRequest(
            name='projects/'+self.Project(), pageSize=100),
        self.messages.ListLocationsResponse(locations=[
            self.messages.Location(
                locationId='global', name=glbl.RelativeName()),
            self.messages.Location(
                locationId='us-east1', name=east.RelativeName()),
        ]))

    self.RunCompleter(
        flags.LocationCompleter,
        expected_command=[
            'kms',
            'locations',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        args={
            '--unrelated': 'junk',
        },
        expected_completions=['global', 'us-east1'],
        cli=self.cli,
    )

  def testKeyRingCompleterCommand(self):
    kr_1 = self.project_name.KeyRing('global/my_kr1')
    kr_2 = self.project_name.KeyRing('global/my_kr2')

    self.kms.projects_locations_keyRings.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsListRequest(
            pageSize=100,
            parent=kr_1.Parent().RelativeName()),
        self.messages.ListKeyRingsResponse(keyRings=[
            self.messages.KeyRing(name=kr_1.RelativeName()),
            self.messages.KeyRing(name=kr_2.RelativeName())
        ]))

    self.RunCompleter(
        flags.KeyRingCompleter,
        expected_command=[
            'kms',
            'keyrings',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--location=global',
        ],
        args={
            '--location': 'global',
            '--unrelated': 'junk',
        },
        expected_completions=['my_kr1', 'my_kr2'],
        cli=self.cli,
    )

  def testImportJobCompleterCommand(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

    ij_1 = self.project_name.ImportJob('global/my_kr/my_ij1')
    ij_2 = self.project_name.ImportJob('global/my_kr/my_ij2')

    self.kms.projects_locations_keyRings_importJobs.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsListRequest(
            pageSize=100, parent=ij_1.Parent().RelativeName()),
        self.messages.ListImportJobsResponse(importJobs=[
            self.messages.ImportJob(
                name=ij_1.RelativeName(),
                state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_3072_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM),
            self.messages.ImportJob(
                name=ij_2.RelativeName(),
                state=self.messages.ImportJob.StateValueValuesEnum.EXPIRED,
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_4096_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM)
        ]))

    self.RunCompleter(
        flags.ImportJobCompleter,
        expected_command=[
            u'beta', u'kms', u'import-jobs', u'list', u'--uri', u'--quiet',
            u'--format=disable', u'--location=global', u'--keyring=my_kr'
        ],
        args={
            '--location': ij_1.location_id,
            '--keyring': ij_1.key_ring_id,
            '--unrelated': 'junk',
        },
        expected_completions=['my_ij1', 'my_ij2'],
        cli=self.cli,
    )

  def testKeyCompleterCommand(self):
    key_1 = self.project_name.CryptoKey('global/my_kr/my_key1')
    key_2 = self.project_name.Version('global/my_kr/my_key2/my_version2')

    self.kms.projects_locations_keyRings_cryptoKeys.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysListRequest(
            pageSize=100, parent=key_1.Parent().RelativeName()),
        self.messages.ListCryptoKeysResponse(cryptoKeys=[
            self.messages.CryptoKey(
                name=key_1.RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT),
            self.messages.CryptoKey(
                name=key_2.Parent().RelativeName(),
                purpose=self.messages.CryptoKey.PurposeValueValuesEnum.
                ENCRYPT_DECRYPT,
                primary=self.messages.CryptoKeyVersion(
                    name=key_2.RelativeName(),
                    state=self.messages.CryptoKeyVersion.StateValueValuesEnum.
                    ENABLED))
        ]))

    self.RunCompleter(
        flags.KeyCompleter,
        expected_command=[
            'kms',
            'keys',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--location=' + key_1.location_id,
            '--keyring=' + key_1.key_ring_id,
        ],
        args={
            '--location': key_1.location_id,
            '--keyring': key_1.key_ring_id,
            '--unrelated': 'junk',
        },
        expected_completions=['my_key1', 'my_key2'],
        cli=self.cli,
    )

  def testKeyVersionCompleterCommand(self):
    version_1 = self.project_name.Version('global/my_kr/my_key/1')
    version_2 = self.project_name.Version('global/my_kr/my_key/2')

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

    self.RunCompleter(
        flags.KeyVersionCompleter,
        expected_command=[
            'kms',
            'keys',
            'versions',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--location=' + version_1.location_id,
            '--key=' + version_1.crypto_key_id,
            '--keyring=' + version_1.key_ring_id,
        ],
        args={
            '--location': version_1.location_id,
            '--keyring': version_1.key_ring_id,
            '--key': version_1.crypto_key_id,
            '--unrelated': 'junk',
        },
        expected_completions=['1', '2'],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
