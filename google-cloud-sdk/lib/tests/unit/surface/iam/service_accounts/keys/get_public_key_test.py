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

"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class GetPublicKeyTest(unit_test_base.BaseTest):

  def _SetUpGetPublicKeyExpectations(self, iam_account, key_id='1234'):
    self.client.projects_serviceAccounts_keys.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysGetRequest(
            name=iam_util.EmailAndKeyToResourceName(iam_account, key_id),
            publicKeyType=iam_util.PublicKeyTypeFromString('pem')),
        response=self.msgs.ServiceAccountKey(
            name=('projects/test-project/serviceAccounts/%s/keys/1234'
                  % iam_account),
            publicKeyData=b'key data goes here'))

  def testGetServiceAccountPublicKey(self):
    iam_account = 'test@test-project.iam.gserviceaccount.com'
    key_id = '1234'
    self._SetUpGetPublicKeyExpectations(iam_account, key_id)

    tmp_file = self.Touch(self.temp_path)
    self.Run('beta iam service-accounts keys get-public-key 1234 --iam-account '
             '{0} --output-file {1}'.
             format(iam_account, tmp_file))

    self.AssertErrContains(('written key [{0}] for [{1}] as [{2}]').format(
        key_id, iam_account, tmp_file))
    self.AssertBinaryFileEquals(b'key data goes here', tmp_file)

  def testGetServiceAccountPublicKeyByName(self):
    iam_account = 'test@test-project.iam.gserviceaccount.com'
    key_id = '1234'
    name = ('projects/-/serviceAccounts/%s/keys/1234' % iam_account)
    self._SetUpGetPublicKeyExpectations(iam_account, key_id)

    tmp_file = self.Touch(self.temp_path)
    self.Run('beta iam service-accounts keys get-public-key {0} --iam-account '
             '{1} --output-file {2}'.
             format(name, iam_account, tmp_file))

    self.AssertErrContains(('written key [{0}] for [{1}] as [{2}]').format(
        key_id, iam_account, tmp_file))
    self.AssertBinaryFileEquals(b'key data goes here', tmp_file)

  def testGetServiceAccountPublicKeyInvalidAccount(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts keys list --iam-account testfoo')

  def testGetServiceAccountPublicKeyValidUniqueId(self):
    iam_account = self.sample_unique_id
    self._SetUpGetPublicKeyExpectations(iam_account)

    tmp_file = self.Touch(self.temp_path)
    try:
      self.Run('beta iam service-accounts keys get-public-key 1234 '
               '--iam-account {0} --output-file {1}'.
               format(iam_account, tmp_file))
    except cli_test_base.MockArgumentError:
      self.fail('get-public-key should accept unique ids for service '
                'accounts.')


if __name__ == '__main__':
  test_case.main()
