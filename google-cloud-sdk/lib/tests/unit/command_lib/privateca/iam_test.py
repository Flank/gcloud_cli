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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.iam."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.command_lib.privateca import iam
from googlecloudsdk.command_lib.projects import util as projects_command_util
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


def GetCryptoKeyRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys')


class IamUtilsTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  _KMS_KEY_NAME = 'projects/my-project/locations/my-location/keyRings/my-key-ring/cryptoKeys/my-crypto-key'
  _PROJECT_NAME = 'my-project'

  def SetUp(self):
    self.cloudresourcemanager_messages = projects_util.GetMessages()
    self.cloudresourcemanager_mockclient = mock.Client(
        apis.GetClientClass(projects_util._API_NAME,
                            projects_util.DEFAULT_API_VERSION),
        real_client=projects_util.GetClient())
    self.cloudresourcemanager_mockclient.Mock()
    self.addCleanup(self.cloudresourcemanager_mockclient.Unmock)

    self.kms_messages = cloudkms_base.GetMessagesModule()
    self.kms_mockclient = mock.Client(
        apis.GetClientClass(cloudkms_base.DEFAULT_API_NAME,
                            cloudkms_base.DEFAULT_API_VERSION),
        real_client=cloudkms_base.GetClientInstance())
    self.kms_mockclient.Mock()
    self.addCleanup(self.kms_mockclient.Unmock)

  def _ExpectKmsIamCall(self, key_ref, requested_permissions,
                        returned_permissions):
    self.kms_mockclient.projects_locations_keyRings_cryptoKeys.TestIamPermissions.Expect(
        self.kms_messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysTestIamPermissionsRequest(
            resource=key_ref.RelativeName(),
            testIamPermissionsRequest=self.kms_messages
            .TestIamPermissionsRequest(permissions=requested_permissions)),
        self.kms_messages.TestIamPermissionsResponse(
            permissions=returned_permissions))

  def _ExpectProjectIamCall(self, project_ref, requested_permissions,
                            returned_permissions):
    self.cloudresourcemanager_mockclient.projects.TestIamPermissions.Expect(
        self.cloudresourcemanager_messages
        .CloudresourcemanagerProjectsTestIamPermissionsRequest(
            resource=project_ref.Name(),
            testIamPermissionsRequest=self.cloudresourcemanager_messages
            .TestIamPermissionsRequest(permissions=requested_permissions)),
        self.cloudresourcemanager_messages.TestIamPermissionsResponse(
            permissions=returned_permissions))

  def testCreateCertificatePermissionsSucceedsWithRequiredPermissions(self):
    project_ref = projects_command_util.ParseProject(self._PROJECT_NAME)
    key_ref = GetCryptoKeyRef(self._KMS_KEY_NAME)
    self._ExpectProjectIamCall(
        project_ref,
        ['privateca.certificateAuthorities.create'],
        ['privateca.certificateAuthorities.create'])
    self._ExpectKmsIamCall(
        key_ref,
        ['cloudkms.cryptoKeys.setIamPolicy'],
        ['cloudkms.cryptoKeys.setIamPolicy'])
    iam.CheckCreateCertificateAuthorityPermissions(project_ref, key_ref)

  def testCreateCertificatePermissionsFailsWithoutProjectPermissions(self):
    project_ref = projects_command_util.ParseProject(self._PROJECT_NAME)
    key_ref = GetCryptoKeyRef(self._KMS_KEY_NAME)
    self._ExpectProjectIamCall(
        project_ref,
        ['privateca.certificateAuthorities.create'],
        [])

    with self.AssertRaisesExceptionMatches(
        exceptions.InsufficientPermissionException,
        'project'):
      iam.CheckCreateCertificateAuthorityPermissions(project_ref, key_ref)

  def testCreateCertificatePermissionsFailsWithoutKeyPermissions(self):
    project_ref = projects_command_util.ParseProject(self._PROJECT_NAME)
    key_ref = GetCryptoKeyRef(self._KMS_KEY_NAME)
    self._ExpectProjectIamCall(
        project_ref,
        ['privateca.certificateAuthorities.create'],
        ['privateca.certificateAuthorities.create'])
    self._ExpectKmsIamCall(
        key_ref,
        ['cloudkms.cryptoKeys.setIamPolicy'],
        [])

    with self.AssertRaisesExceptionMatches(
        exceptions.InsufficientPermissionException,
        'KMS key'):
      iam.CheckCreateCertificateAuthorityPermissions(project_ref, key_ref)

  def testCreateCertificatePermissionsIgnoresMissingKmsKey(self):
    project_ref = projects_command_util.ParseProject(self._PROJECT_NAME)
    self._ExpectProjectIamCall(
        project_ref,
        ['privateca.certificateAuthorities.create'],
        ['privateca.certificateAuthorities.create'])

    iam.CheckCreateCertificateAuthorityPermissions(project_ref, None)


if __name__ == '__main__':
  test_case.main()
