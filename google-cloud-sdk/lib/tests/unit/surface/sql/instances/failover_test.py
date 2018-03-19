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
"""Tests that exercise triggering instance failover."""

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class InstancesFailoverTest(base.SqlMockTestBeta):

  def testInstancesFailover(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.mocked_client.instances.Get.Expect(
        request=self.messages.SqlInstancesGetRequest(
            project=self.Project(), instance='my-instance'),
        response=self.messages.DatabaseInstance(settings=self.messages.Settings(
            settingsVersion=12345)))
    self.mocked_client.instances.Failover.Expect(
        request=self.messages.SqlInstancesFailoverRequest(
            project=self.Project(),
            instance='my-instance',
            instancesFailoverRequest=self.messages.InstancesFailoverRequest(
                failoverContext=self.messages.FailoverContext(
                    kind='sql#failoverContext', settingsVersion=12345))),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql instances failover my-instance')
    self.assertEqual(prompt_mock.call_count, 1)

  def testFailoverNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances failover my-instance')


if __name__ == '__main__':
  test_case.main()
