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
"""Tests for google3.third_party.py.tests.api_lib.cloudkms.iam."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case


def GetCryptoKeyRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys')


class KmsIamTest(sdk_test_base.WithFakeAuth):
  _KEY_NAME = 'projects/my-project/locations/my-location/keyRings/my-key-ring/cryptoKeys/my-crypto-key'

  def SetUp(self):
    self.messages = cloudkms_base.GetMessagesModule()
    self.mock_client = mock.Client(
        apis.GetClientClass(
            cloudkms_base.DEFAULT_API_NAME,
            cloudkms_base.DEFAULT_API_VERSION),
        real_client=cloudkms_base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.key_ref = GetCryptoKeyRef(self._KEY_NAME)

  def testTestCryptoKeyIamPermissions(self):
    permissions = ['cloudkms.keyRings.list', 'cloudkms.cryptoKeys.list']
    expected = self.messages.TestIamPermissionsResponse(permissions=permissions)
    self.mock_client.projects_locations_keyRings_cryptoKeys.TestIamPermissions.Expect(
        request=self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysTestIamPermissionsRequest(
            resource=self.key_ref.RelativeName(),
            testIamPermissionsRequest=self.messages.TestIamPermissionsRequest(
                permissions=permissions)),
        response=expected)

    actual = iam.TestCryptoKeyIamPermissions(self.key_ref, permissions)
    self.assertEqual(actual.permissions, expected.permissions)

  def testAddPolicyBindingToCryptoKeyAddsNewBinding(self):
    old_policy = self.messages.Policy(
        version=1,
        etag=b'CAE3',
        bindings=[])

    # IAM utils always sets the policy version to the latest available.
    new_policy = copy.deepcopy(old_policy)
    new_policy.version = 3
    new_policy.bindings.append(
        self.messages.Binding(
            role='roles/cloudkms.signerVerifier',
            members=['user:test-user@gmail.com']))
    new_policy_request = self.messages.SetIamPolicyRequest(
        policy=new_policy, updateMask='bindings,etag,version')

    # ETAG should be updated after SetIamPolicy.
    expected_policy = copy.deepcopy(new_policy)
    expected_policy.etag = b'CAE4'
    self.mock_client.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        request=self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self._KEY_NAME, options_requestedPolicyVersion=3),
        response=old_policy)
    self.mock_client.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self._KEY_NAME, setIamPolicyRequest=new_policy_request),
        response=expected_policy)

    actual_policy = iam.AddPolicyBindingToCryptoKey(
        self.key_ref, 'user:test-user@gmail.com',
        'roles/cloudkms.signerVerifier')
    self.assertEqual(actual_policy, expected_policy)

  def testAddPolicyBindingsToCryptoKeyAddsNewBindings(self):
    old_policy = self.messages.Policy(
        version=1,
        etag=b'CAE3',
        bindings=[])

    new_policy = copy.deepcopy(old_policy)
    new_policy.version = 3
    new_policy.bindings.append(
        self.messages.Binding(
            role='roles/cloudkms.signerVerifier',
            members=['user:test-user@gmail.com', 'user:test-user-2@gmail.com']))
    new_policy.bindings.append(
        self.messages.Binding(
            role='roles/viewer', members=['user:test-user@gmail.com']))
    new_policy_request = self.messages.SetIamPolicyRequest(
        policy=new_policy, updateMask='bindings,etag,version')

    expected_policy = copy.deepcopy(new_policy)
    expected_policy.etag = b'CAE4'
    self.mock_client.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        request=self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self._KEY_NAME, options_requestedPolicyVersion=3),
        response=old_policy)
    self.mock_client.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self._KEY_NAME, setIamPolicyRequest=new_policy_request),
        response=expected_policy)

    actual_policy = iam.AddPolicyBindingsToCryptoKey(
        self.key_ref,
        [('user:test-user@gmail.com', 'roles/cloudkms.signerVerifier'),
         ('user:test-user-2@gmail.com', 'roles/cloudkms.signerVerifier'),
         ('user:test-user@gmail.com', 'roles/viewer')])
    self.assertEqual(actual_policy, expected_policy)

  def testAddPolicyBindingsToCryptoKeyDoesntCallSetForSameBindings(self):
    policy = self.messages.Policy(
        version=1,
        etag=b'CAE3',
        bindings=[
            self.messages.Binding(
                role='roles/cloudkms.signerVerifier',
                members=[
                    'user:test-user@gmail.com', 'user:test-user-2@gmail.com'
                ]),
            self.messages.Binding(
                role='roles/viewer', members=['user:test-user@gmail.com']),
        ])

    self.mock_client.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        request=self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self._KEY_NAME, options_requestedPolicyVersion=3),
        response=policy)

    actual_policy = iam.AddPolicyBindingsToCryptoKey(
        self.key_ref,
        [('user:test-user@gmail.com', 'roles/cloudkms.signerVerifier'),
         ('user:test-user-2@gmail.com', 'roles/cloudkms.signerVerifier'),
         ('user:test-user@gmail.com', 'roles/viewer')])
    self.assertEqual(actual_policy, policy)


if __name__ == '__main__':
  test_case.main()
