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
"""ml-engine models delete tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class DeleteTestBase(object):

  def SetUp(self):
    self.StartPatch('time.sleep')

  def testDelete(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(
            name='opName', done=True))

    self.WriteInput('y')
    self.Run('ml-engine models delete myModel')

    self.mocked_delete.assert_called_once_with('myModel')
    self.AssertErrContains('Deleting model [myModel]')

  def testDeleteCancel(self):
    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('ml-engine models delete modelId')
    self.AssertErrContains('This will delete model [modelId]')
    self.AssertErrNotContains('Deleting model [modelId]')


class DeleteGaTest(DeleteTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(DeleteGaTest, self).SetUp()
    self.mocked_delete = self.StartObjectPatch(
        models.ModelsClient, 'Delete',
        return_value=self.msgs.GoogleLongrunningOperation(name='opId'))


class DeleteBetaTest(DeleteTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(DeleteBetaTest, self).SetUp()
    self.mocked_delete = self.StartObjectPatch(
        models.ModelsClient, 'Delete',
        return_value=self.msgs.GoogleLongrunningOperation(name='opId'))


if __name__ == '__main__':
  test_case.main()
