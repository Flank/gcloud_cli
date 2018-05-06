# Copyright 2017 Google Inc. All Rights Reserved.
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
"""ml-engine operations delete tests."""
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class DeleteTestBase(object):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testDelete(self):
    self.client.projects_operations.Delete.Expect(
        self.msgs.MlProjectsOperationsDeleteRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        self.msgs.GoogleProtobufEmpty()
    )
    self.WriteInput('y')
    self.assertEqual(
        self.Run('ml-engine operations delete opId'),
        self.msgs.GoogleProtobufEmpty())

  def testDeleteCancel(self):
    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('ml-engine operations delete opId')
    self.AssertErrContains('This will delete operation [opId]')
    self.AssertErrNotContains('Deleting operation [opId]...')


class DeleteGaTest(DeleteTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(DeleteGaTest, self).SetUp()


class DeleteBetaTest(DeleteTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(DeleteBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
