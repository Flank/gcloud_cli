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
"""Tests for the roots create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import create_utils
from surface.privateca.roots import create
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import mock


class CreateFlagsTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    create.Create.Args(self.parser)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseInlineKmsKeyVersion(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--subject=CN=test,O=Google',
        '--kms-key-version=projects/foo/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1',
    ])
    kms_key_version_ref, _, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(kms_key_version_ref.projectsId, 'foo')
    self.assertEqual(kms_key_version_ref.locationsId, 'us-west1')
    self.assertEqual(kms_key_version_ref.keyRingsId, 'kr1')
    self.assertEqual(kms_key_version_ref.cryptoKeysId, 'k1')
    self.assertEqual(kms_key_version_ref.cryptoKeyVersionsId, '1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseComponentizedKmsKeyVersion(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--subject=CN=test,O=Google',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
        '--kms-location=us-west1',
        '--kms-project=foo',
    ])
    kms_key_version_ref, _, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(kms_key_version_ref.projectsId, 'foo')
    self.assertEqual(kms_key_version_ref.locationsId, 'us-west1')
    self.assertEqual(kms_key_version_ref.keyRingsId, 'kr1')
    self.assertEqual(kms_key_version_ref.cryptoKeysId, 'k1')
    self.assertEqual(kms_key_version_ref.cryptoKeyVersionsId, '1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testKmsKeyVersionInUnsupportedLocationsRaisesException(
      self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--subject=CN=test,O=Google',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
        '--kms-location=us',
    ])
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'unsupported location'):
      create_utils._ParseCAResourceArgs(args)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testCertificateAuthorityUsesLocationFromKeyVersion(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--subject=CN=test,O=Google',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
        '--kms-location=us-west1',
    ])
    _, ca_ref, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_ref.locationsId, 'us-west1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testCertificateAuthorityInDifferentLocationRaisesException(
      self, location_mock):
    args = self.parser.parse_args([
        'projects/foo/locations/us-east1/certificateAuthorities/new-ca',
        '--subject=CN=test,O=Google',
        '--kms-key-version=projects/foo/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1',
    ])
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'same location'):
      create_utils._ParseCAResourceArgs(args)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseInlineSourceCertificateAuthority(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--from-ca=projects/foo/locations/us-west1/certificateAuthorities/source-root',
        '--kms-key-version=projects/foo/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1',
    ])
    _, _, ca_source_ref, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_source_ref.projectsId, 'foo')
    self.assertEqual(ca_source_ref.locationsId, 'us-west1')
    self.assertEqual(ca_source_ref.certificateAuthoritiesId, 'source-root')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseComponentizedCertificateAuthority(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version=projects/foo/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1',
        '--from-ca=source-root', '--from-ca-location=us-west1',
        '--from-ca-project=bar'
    ])
    _, _, ca_source_ref, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_source_ref.projectsId, 'bar')
    self.assertEqual(ca_source_ref.locationsId, 'us-west1')
    self.assertEqual(ca_source_ref.certificateAuthoritiesId, 'source-root')


if __name__ == '__main__':
  test_case.main()
