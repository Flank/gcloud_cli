# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests that exercise user deletion."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class UsersDeleteTest(base.SqlMockTestBeta):

  def testDelete(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    msgs = apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.users.Delete.Expect(
        msgs.SqlUsersDeleteRequest(
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host'),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name', status='DONE'))
    self.Run('sql users delete --instance my_instance my_username my_host')
    self.assertEqual(prompt_mock.call_count, 1)

  def testDeleteNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql users delete --instance my_instance my_username '
               'my_host --async')

  def testDeleteAsync(self):
    msgs = apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.users.Delete.Expect(
        msgs.SqlUsersDeleteRequest(
            project=self.Project(),
            instance='my_instance',
            name='my_username',
            host='my_host'),
        msgs.Operation(name='op_name'))
    self.mocked_client.operations.Get.Expect(
        msgs.SqlOperationsGetRequest(
            operation='op_name', project=self.Project()),
        msgs.Operation(name='op_name'))

    result = self.Run('sql users delete --instance my_instance my_username '
                      'my_host --async')
    self.assertEquals(result.name, 'op_name')
    self.AssertOutputEquals('')
    self.AssertErrContains('my_username@my_host will be deleted. New '
                           'connections can no longer be made using this user. '
                           'Existing connections are not affected.\n\n'
                           'Do you want to continue (Y/n)?')


if __name__ == '__main__':
  test_case.main()
