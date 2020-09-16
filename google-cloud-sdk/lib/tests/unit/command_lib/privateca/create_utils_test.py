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
from googlecloudsdk.command_lib.privateca import create_utils
from surface.privateca.roots import create
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import mock


class CreateTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  _CA_NAME = 'projects/my-project/locations/my-location/certificateAuthorities/my-ca'
  _KMS_KEY_NAME = 'projects/p1/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1'

  def SetUp(self):
    self.parser = util.ArgumentParser()
    create.Create.Args(self.parser)

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
            cloudKmsKeyVersion=self._KMS_KEY_NAME),
        gcsBucket='my-bucket',
    )

    self.request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
        name=self._CA_NAME)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testSubjectFromSourceCa(self, location_mock):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', self._KMS_KEY_NAME, '--from-ca',
        self._CA_NAME
    ])
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
  def testSubjectOverridesSourceCa(self, location_mock):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--subject',
        'C=US, ST=Washington, L=Kirkland, O=Google LLC, CN=google.com, OU=Cloud, postalCode=98033, streetAddress=6th Ave',
        '--kms-key-version', self._KMS_KEY_NAME, '--from-ca', self._CA_NAME
    ])

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
  def testReusableConfigFromSourceCa(self, location_mock):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', self._KMS_KEY_NAME, '--from-ca',
        self._CA_NAME
    ])
    new_ca, _, _, = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertEqual(new_ca.config.reusableConfig.reusableConfig,
                     self.source_ca.config.reusableConfig.reusableConfig)

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testReusableConfigOverridesSourceCa(self, location_mock):
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.request, response=self.source_ca)
    reusable_config_id = 'projects/foo/locations/us-west1/reusableConfigs/rc1'
    args = self.parser.parse_args([
        'new-ca', '--kms-key-version', self._KMS_KEY_NAME, '--from-ca',
        self._CA_NAME, '--reusable-config', reusable_config_id
    ])
    new_ca, _, _ = create_utils.CreateCAFromArgs(args, is_subordinate=False)
    self.assertNotEqual(new_ca.config.reusableConfig.reusableConfig,
                        self.source_ca.config.reusableConfig.reusableConfig)
    self.assertEqual(new_ca.config.reusableConfig.reusableConfig,
                     reusable_config_id)


if __name__ == '__main__':
  test_case.main()
