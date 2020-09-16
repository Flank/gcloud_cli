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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.p4sa."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam as kms_iam
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.privateca import p4sa
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


def GetCryptoKeyRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys')


def GetProjectRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name, collection='projects')


class P4saUtilsTest(sdk_test_base.WithFakeAuth):

  _BUCKET_NAME = 'my-bucket'
  _KEY_NAME = 'projects/my-project/locations/my-location/keyRings/my-key-ring/cryptoKeys/my-crypto-key'
  _PROJECT_ID = 'my-project'

  def SetUp(self):
    self.bucket_ref = storage_util.BucketReference(self._BUCKET_NAME)
    self.key_ref = GetCryptoKeyRef(self._KEY_NAME)
    self.project_ref = command_lib_util.ParseProject(self._PROJECT_ID)

  @mock.patch.object(serviceusage, 'GenerateServiceIdentity', autospec=True)
  def testGetOrCreateReturnsP4saEmail(self, mock_fn):
    p4sa_email = 'service-166289904856@gcp-sa-eprivateca.iam.gserviceaccount.com'
    mock_fn.return_value = (p4sa_email, '4ed34a88b0d845b3a35ea25fb6f08590')

    self.assertEqual(p4sa.GetOrCreate(self.project_ref), p4sa_email)
    mock_fn.assert_has_calls(
        [mock.call(self._PROJECT_ID, 'privateca.googleapis.com')])

  @mock.patch.object(kms_iam, 'AddPolicyBindingsToCryptoKey', autospec=True)
  @mock.patch.object(
      storage_api.StorageClient, 'AddIamPolicyBindings', autospec=True)
  def testAddResourceRoleBindingsCallsIamFunctions(self, mock_storage_fn,
                                                   mock_kms_fn):
    p4sa_email = 'service-166289904856@gcp-sa-eprivateca.iam.gserviceaccount.com'
    iam_principal = 'serviceAccount:{}'.format(p4sa_email)

    p4sa.AddResourceRoleBindings(p4sa_email, self.key_ref, self.bucket_ref)

    mock_kms_fn.assert_has_calls([
        mock.call(self.key_ref,
                  [(iam_principal, 'roles/cloudkms.signerVerifier'),
                   (iam_principal, 'roles/viewer')]),
    ])
    mock_storage_fn.assert_has_calls([
        mock.call(
            mock.ANY,  # self
            self.bucket_ref,
            [(iam_principal, 'roles/storage.objectAdmin'),
             (iam_principal, 'roles/storage.legacyBucketReader')])
    ])


if __name__ == '__main__':
  test_case.main()
