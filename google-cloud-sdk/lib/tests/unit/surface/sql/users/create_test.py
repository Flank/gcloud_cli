# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests that exercise user creation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseUsersCreateTest(object):

  def testCreate(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            password='my_password'), msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(
            name='op_name', status=msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run('sql users create --instance my_instance '
             'my_username --host my_host --password my_password')
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating Cloud SQL user')
    self.AssertErrContains('Created user [my_username].')

  # TODO(b/110486599): Remove this when the argument is removed.
  def testPositionalHostError(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'Positional argument deprecated_host has been '
        'removed'):
      self.Run('sql users create --instance my_instance '
               'my_username my_host --password my_password')

  def testCreateWithNoHostArgument(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host=None,
            password='my_password'), msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(
            name='op_name', status=msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run('sql users create --instance my_instance '
             'my_username --password my_password')
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating Cloud SQL user')
    self.AssertErrContains('Created user [my_username].')

  def testCreateWithHostFlag(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            password='my_password'), msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(
            name='op_name', status=msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run('sql users create --instance my_instance '
             'my_username --host my_host --password my_password')
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating Cloud SQL user')
    self.AssertErrContains('Created user [my_username].')

  def testCreateAsync(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host',
            password='my_password'), msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name'))
    result = self.Run('sql users create --instance my_instance my_username '
                      '--host my_host --password my_password --async')
    self.assertEqual(result.name, 'op_name')
    self.AssertOutputEquals('')
    self.AssertErrContains('Create in progress for user [my_username].\n')


class UsersCreateGATest(_BaseUsersCreateTest, base.SqlMockTestGA):
  pass


class UsersCreateBetaTest(_BaseUsersCreateTest, base.SqlMockTestBeta):
  pass


class UsersCreateAlphaTest(_BaseUsersCreateTest, base.SqlMockTestAlpha):

  def testCreateIamUser(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='test@google.com',
            type=self.messages.User.TypeValueValuesEnum.CLOUD_IAM_USER),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(
            name='op_name', status=msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run('sql users create --instance my_instance '
             'test@google.com --type CLOUD_IAM_USER')
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating Cloud SQL user')
    self.AssertErrContains('Created user [test@google.com].')

  def testCreateIamServiceAccount(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.Insert.Expect(
        msgs.User(
            kind='sql#user',
            project=self.Project(),
            instance='my_instance',
            name='sa@iam',
            type=self.messages.User.TypeValueValuesEnum
            .CLOUD_IAM_SERVICE_ACCOUNT),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(
            name='op_name', status=msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run('sql users create --instance my_instance '
             'sa@iam --type CLOUD_IAM_SERVICE_ACCOUNT')
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating Cloud SQL user')
    self.AssertErrContains('Created user [sa@iam].')


if __name__ == '__main__':
  test_case.main()
