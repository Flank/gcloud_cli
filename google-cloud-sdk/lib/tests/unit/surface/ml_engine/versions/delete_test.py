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
"""ml-engine versions delete tests."""

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class DeleteTestBase(object):

  def SetUp(self):
    self.version_ref = resources.REGISTRY.Parse(
        'versionId',
        params={'projectsId': self.Project(), 'modelsId': 'modelId'},
        collection='ml.projects.models.versions')
    self.StartPatch('time.sleep')

  def testDelete(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(
            name='opName', done=True))

    self.WriteInput('y')
    self.Run('ml-engine versions delete versionId --model modelId')

    self.delete_mock.assert_called_once_with(self.version_ref)
    self.AssertErrContains('Deleting version [versionId]')

  def testDeleteCancel(self):
    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('ml-engine versions delete versionId --model modelId')
    self.AssertErrContains('This will delete version [versionId]')
    self.AssertErrNotContains('Deleting version [versionId]')


class DeleteGaTest(DeleteTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    resources.REGISTRY.RegisterApiByName('ml', 'v1')
    super(DeleteGaTest, self).SetUp()
    self.delete_mock = self.StartObjectPatch(
        versions_api.VersionsClient, 'Delete',
        return_value=self.msgs.GoogleLongrunningOperation(name='opId'))


class DeleteBetaTest(DeleteTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(DeleteBetaTest, self).SetUp()
    self.delete_mock = self.StartObjectPatch(
        versions_api.VersionsClient, 'Delete',
        return_value=self.msgs.GoogleLongrunningOperation(name='opId'))


if __name__ == '__main__':
  test_case.main()
