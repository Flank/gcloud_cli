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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.create_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import create_utils
from googlecloudsdk.core import properties
from surface.privateca.roots import create as roots_create
from surface.privateca.subordinates import create as subordinates_create
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import mock


_DEFAULT_PROJECT = 'p1'
_DEFAULT_LOCATION = 'us-west1'
_DEFAULT_CA_ID = 'new-ca'
_CA_NAME = 'projects/{}/locations/{}/certificateAuthorities/{}'.format(
    _DEFAULT_PROJECT, _DEFAULT_LOCATION, _DEFAULT_CA_ID)


def _KmsKeyVersion(project=_DEFAULT_PROJECT,
                   location=_DEFAULT_LOCATION,
                   key_ring='kr1',
                   crypto_key='k1',
                   crypto_key_version='1'):
  return 'projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}/cryptoKeyVersions/{}'.format(
      project, location, key_ring, crypto_key, crypto_key_version)


class ParseCAResourceArgsTestMixin(object):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    properties.VALUES.core.project.Set(_DEFAULT_PROJECT)
    properties.VALUES.privateca.location.Set(_DEFAULT_LOCATION)
    # Child classes can set this to include irrelevant but required args.
    self.other_args = []

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseCertificateAuthorityWithFullResourceName(self, _):
    args = self.parser.parse_args([
        'projects/different/locations/us-east1/certificateAuthorities/new-ca',
        '--kms-key-version', _KmsKeyVersion(location='us-east1'),
    ] + self.other_args)
    ca_ref, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_ref.projectsId, 'different')
    self.assertEqual(ca_ref.locationsId, 'us-east1')
    self.assertEqual(ca_ref.certificateAuthoritiesId, 'new-ca')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseCertificateAuthorityWithComponentizedLocation(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--location=us-east1',
        '--kms-key-version', _KmsKeyVersion(location='us-east1'),
    ] + self.other_args)
    ca_ref, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_ref.locationsId, 'us-east1')
    self.assertEqual(ca_ref.certificateAuthoritiesId, 'new-ca')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseCertificateAuthorityWithImplicitLocation(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version', _KmsKeyVersion(),
    ] + self.other_args)
    ca_ref, _, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_ref.locationsId, _DEFAULT_LOCATION)
    self.assertEqual(ca_ref.certificateAuthoritiesId, 'new-ca')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testCertificateAuthorityInUnsupportedLocationRaisesException(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--location=us-central1',
        '--kms-key-version', _KmsKeyVersion(location='us-central1'),
    ] + self.other_args)
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'unsupported location'):
      create_utils._ParseCAResourceArgs(args)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseKmsKeyVersionWithFullResourceName(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version=projects/different/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1',
    ] + self.other_args)
    kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    self.assertEqual(kms_key_version_ref.projectsId, 'different')
    self.assertEqual(kms_key_version_ref.locationsId, 'us-west1')
    self.assertEqual(kms_key_version_ref.keyRingsId, 'kr1')
    self.assertEqual(kms_key_version_ref.cryptoKeysId, 'k1')
    self.assertEqual(kms_key_version_ref.cryptoKeyVersionsId, '1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseKmsKeyVersionWithComponentizedResourceName(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
        '--kms-location=us-west1',
        '--kms-project=different',
    ] + self.other_args)
    kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    self.assertEqual(kms_key_version_ref.projectsId, 'different')
    self.assertEqual(kms_key_version_ref.locationsId, 'us-west1')
    self.assertEqual(kms_key_version_ref.keyRingsId, 'kr1')
    self.assertEqual(kms_key_version_ref.cryptoKeysId, 'k1')
    self.assertEqual(kms_key_version_ref.cryptoKeyVersionsId, '1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseKmsKeyVersionDefaultsToCertificateAuthorityLocation(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--location=us-east1',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
    ] + self.other_args)
    kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    self.assertEqual(kms_key_version_ref.locationsId, 'us-east1')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testDevOpsTierDoesntSupportByoKmsKey(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--tier', 'devops',
        '--kms-key-version', _KmsKeyVersion()
    ] + self.other_args)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'DevOps tier does not support user-specified KMS keys'):
      create_utils.CreateCAFromArgs(args,
                                    # This is irrelevant here.
                                    is_subordinate=False)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testKmsKeyVersionInDifferentLocationRaisesException(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version=1',
        '--kms-key=k1',
        '--kms-keyring=kr1',
        '--kms-location=us-europe-west1',
    ] + self.other_args)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS key must be in the same location'):
      create_utils._ParseCAResourceArgs(args)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testSupportsMissingKmsKeyVersion(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--key-algorithm=rsa-pss-2048-sha256',
    ] + self.other_args)
    create_utils._ParseCAResourceArgs(args)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseSourceWithFullResourceName(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--from-ca=projects/foo/locations/us-west1/certificateAuthorities/source-root',
        '--kms-key-version',
        _KmsKeyVersion(),
    ] + self.other_args)
    _, ca_source_ref, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_source_ref.projectsId, 'foo')
    self.assertEqual(ca_source_ref.locationsId, 'us-west1')
    self.assertEqual(ca_source_ref.certificateAuthoritiesId, 'source-root')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseSourceWithComponentizedResourceFlags(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--kms-key-version', _KmsKeyVersion(),
        '--from-ca=source-root', '--from-ca-location=europe-west1',
        '--from-ca-project=bar'
    ] + self.other_args)
    _, ca_source_ref, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_source_ref.projectsId, 'bar')
    self.assertEqual(ca_source_ref.locationsId, 'europe-west1')
    self.assertEqual(ca_source_ref.certificateAuthoritiesId, 'source-root')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseSourceWithImplicitLocation(self, _):
    properties.VALUES.privateca.location.Set('europe-west1')
    args = self.parser.parse_args([
        'new-ca',
        '--location=us-west1',
        '--kms-key-version', _KmsKeyVersion(),
        '--from-ca=source-root',
    ] + self.other_args)
    _, ca_source_ref, _ = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(ca_source_ref.locationsId, 'europe-west1')
    self.assertEqual(ca_source_ref.certificateAuthoritiesId, 'source-root')


class SourceCAOverridesTestMixin(object):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    properties.VALUES.core.project.Set(_DEFAULT_PROJECT)
    properties.VALUES.privateca.location.Set(_DEFAULT_LOCATION)
    # Child classes can set this to include irrelevant but required args.
    self.other_args = []

    self.mock_client = api_mock.Client(
        privateca_base.GetClientClass(),
        real_client=privateca_base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = privateca_base.GetMessagesModule()

    self.source_ca = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED,
        lifetime='10s',
        config=self.messages.CertificateConfig(
            reusableConfig=self.messages.ReusableConfigWrapper(
                reusableConfig='my-reusable-config'),
            subjectConfig=self.messages.SubjectConfig(
                commonName='foobar',
                subject=self.messages.Subject(organization='foo'))),
        issuingOptions=self.messages.IssuingOptions(),
        keySpec=self.messages.KeyVersionSpec(
            cloudKmsKeyVersion=_KmsKeyVersion()),
        gcsBucket='my-bucket',
    )

    self.request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
        name=_CA_NAME)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testSubjectFromSourceCa(self, _):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', _KmsKeyVersion(), '--from-ca', _CA_NAME
    ] + self.other_args)
    new_ca, _, _ = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertEqual(new_ca.config.subjectConfig.commonName,
                     self.source_ca.config.subjectConfig.commonName)
    self.assertEqual(new_ca.config.subjectConfig.subject.organization,
                     self.source_ca.config.subjectConfig.subject.organization)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testSubjectOverridesSourceCa(self, _):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--subject',
        'C=US, ST=Washington, L=Kirkland, O=Google LLC, CN=google.com, OU=Cloud, postalCode=98033, streetAddress=6th Ave',
        '--kms-key-version', _KmsKeyVersion(), '--from-ca', _CA_NAME
    ] + self.other_args)

    new_ca, _, _ = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertNotEqual(new_ca.config.subjectConfig.commonName,
                        self.source_ca.config.subjectConfig.commonName)
    self.assertNotEqual(
        new_ca.config.subjectConfig.subject.organization,
        self.source_ca.config.subjectConfig.subject.organization)

    self.assertEqual(new_ca.config.subjectConfig.commonName, 'google.com')
    self.assertEqual(new_ca.config.subjectConfig.subject.organization,
                     'Google LLC')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testReusableConfigFromSourceCa(self, _):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', _KmsKeyVersion(), '--from-ca', _CA_NAME
    ] + self.other_args)
    new_ca, _, _, = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertEqual(new_ca.config.reusableConfig.reusableConfig,
                     self.source_ca.config.reusableConfig.reusableConfig)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testReusableConfigOverridesSourceCa(self, _):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    reusable_config_id = 'projects/foo/locations/us-west1/reusableConfigs/rc1'
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', _KmsKeyVersion(), '--from-ca',
        _CA_NAME, '--reusable-config', reusable_config_id
    ] + self.other_args)
    new_ca, _, _ = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertNotEqual(new_ca.config.reusableConfig.reusableConfig,
                        self.source_ca.config.reusableConfig.reusableConfig)
    self.assertEqual(new_ca.config.reusableConfig.reusableConfig,
                     reusable_config_id)


class ParseRootCAResourceArgsTest(ParseCAResourceArgsTestMixin,
                                  cli_test_base.CliTestBase,
                                  sdk_test_base.WithFakeAuth):

  def SetUp(self):
    super(ParseRootCAResourceArgsTest, self).SetUp()
    roots_create.Create.Args(self.parser)


class ParseSubordinateCAResourceArgsTest(ParseCAResourceArgsTestMixin,
                                         cli_test_base.CliTestBase,
                                         sdk_test_base.WithFakeAuth):

  def SetUp(self):
    super(ParseSubordinateCAResourceArgsTest, self).SetUp()
    subordinates_create.Create.Args(self.parser)
    self.other_args = ['--create-csr', '--csr-output-file=/tmp/foo']

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseIssuerWithComponentizedResourceName(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--issuer=my-root',
        '--issuer-location=us-west1',
        '--kms-key-version', _KmsKeyVersion(),
    ])
    _, _, issuer_ref = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(issuer_ref.locationsId, 'us-west1')
    self.assertEqual(issuer_ref.certificateAuthoritiesId, 'my-root')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testParseIssuerWithFullResourceName(self, _):
    args = self.parser.parse_args([
        'new-ca',
        '--issuer=projects/different/locations/us-west1/certificateAuthorities/my-root',
        '--kms-key-version', _KmsKeyVersion(),
    ])
    _, _, issuer_ref = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(issuer_ref.projectsId, 'different')
    self.assertEqual(issuer_ref.locationsId, 'us-west1')
    self.assertEqual(issuer_ref.certificateAuthoritiesId, 'my-root')

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testIssuerInDifferentLocationWorks(self, location_mock):
    args = self.parser.parse_args([
        'new-ca',
        '--issuer=my-root',
        '--issuer-location=europe-west1',
        '--kms-key-version', _KmsKeyVersion(),
    ])
    _, _, issuer_ref = create_utils._ParseCAResourceArgs(args)
    self.assertEqual(issuer_ref.locationsId, 'europe-west1')
    self.assertEqual(issuer_ref.certificateAuthoritiesId, 'my-root')


class SourceCAOverridesRootsTest(SourceCAOverridesTestMixin,
                                 cli_test_base.CliTestBase,
                                 sdk_test_base.WithFakeAuth):

  def SetUp(self):
    super(SourceCAOverridesRootsTest, self).SetUp()
    roots_create.Create.Args(self.parser)


class SourceCAOverridesSubordinatesTest(SourceCAOverridesTestMixin,
                                        cli_test_base.CliTestBase,
                                        sdk_test_base.WithFakeAuth):

  def SetUp(self):
    super(SourceCAOverridesSubordinatesTest, self).SetUp()
    subordinates_create.Create.Args(self.parser)
    self.other_args = ['--create-csr', '--csr-output-file=/tmp/foo']


if __name__ == '__main__':
  test_case.main()
