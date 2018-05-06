# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests of the 'delete' command."""
from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.functions import base


class FunctionsDeleteTest(base.FunctionsTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def testDelete(self):
    test_name = 'projects/{0}/locations/us-central1/functions/my-test'.format(
        self.Project())
    self.mock_client.projects_locations_functions.Delete.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsDeleteRequest(
            name=test_name),
        self._GenerateActiveOperation('operations/operation'))
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))
    self.Run('functions delete my-test')
    self.AssertErrContains('Deleted [{0}]'.format(test_name))

  def testFailedDelete(self):
    test_name = 'projects/{0}/locations/us-central1/functions/my-test'.format(
        self.Project())
    self.mock_client.projects_locations_functions.Delete.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsDeleteRequest(
            name=test_name),
        self._GenerateActiveOperation('operations/operation'))
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateFailedOperation('operations/operation'))
    with self.assertRaisesRegex(exceptions.FunctionsError,
                                base.OP_FAILED_REGEXP):
      self.Run('functions delete my-test')

  def testDeleteNoAuth(self):
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_AUTH_REGEXP):
      self.Run('functions delete my-test')


class FunctionsDeleteWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testDeleteNoProject(self):
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_PROJECT_REGEXP):
      self.Run('functions delete my-test')

if __name__ == '__main__':
  test_case.main()
