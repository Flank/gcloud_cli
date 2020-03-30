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
"""Tests that exercise user list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseUsersListTest(object):

  def testList(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.List.Expect(
        msgs.SqlUsersListRequest(
            project=self.Project(), instance='my_instance'),
        msgs.UsersListResponse(items=[
            msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='my_username',
                host='my_host')
        ]))
    _ = self.Run('sql users list --instance my_instance')
    self.AssertOutputContains(
        """\
NAME         HOST
my_username  my_host
""",
        normalize_space=True)


class UsersListGATest(_BaseUsersListTest, base.SqlMockTestGA):
  pass


class UsersListBetaTest(_BaseUsersListTest, base.SqlMockTestBeta):
  pass


class UsersListAlphaTest(_BaseUsersListTest, base.SqlMockTestAlpha):

  def testList(self):
    msgs = apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.users.List.Expect(
        msgs.SqlUsersListRequest(
            project=self.Project(), instance='my_instance'),
        msgs.UsersListResponse(items=[
            msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='postgres',
                type=self.messages.User.TypeValueValuesEnum
                .NATIVE),
            msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='test@google.com',
                type=self.messages.User.TypeValueValuesEnum
                .CLOUD_IAM_USER),
            msgs.User(
                project=self.Project(),
                instance='my_instance',
                name='test-sa@iam',
                type=self.messages.User.TypeValueValuesEnum
                .CLOUD_IAM_SERVICE_ACCOUNT),
        ]))
    _ = self.Run('sql users list --instance my_instance')
    self.AssertOutputContains(
        """\
NAME             HOST  TYPE
postgres               NATIVE
test@google.com        CLOUD_IAM_USER
test-sa@iam            CLOUD_IAM_SERVICE_ACCOUNT
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
