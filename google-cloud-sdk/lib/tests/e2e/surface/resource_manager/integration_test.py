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

from apitools.base.py import encoding

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import test_case

messages = folders.FoldersMessages()

FOLDER_ACTIVE = messages.Folder.LifecycleStateValueValuesEnum.ACTIVE

TEST_ORGANIZATION_ID = '961309089256'
TEST_TOP_LEVEL_FOLDER_ID = '79536718298'
TEST_TOP_LEVEL_FOLDER_NAME = u'folders/{0}'.format(TEST_TOP_LEVEL_FOLDER_ID)

TEST_TOP_LEVEL_FOLDER = messages.Folder(
    name=TEST_TOP_LEVEL_FOLDER_NAME,
    parent=u'organizations/{0}'.format(TEST_ORGANIZATION_ID),
    displayName=u'Elysium gCloud Testing',
    lifecycleState=FOLDER_ACTIVE,
    createTime=u'2016-10-21T20:44:47.207Z')

TEST_SUBFOLDER_A = messages.Folder(
    createTime=u'2016-10-24T18:36:34.280Z',
    displayName=u'Folder A',
    lifecycleState=FOLDER_ACTIVE,
    name=u'folders/309449917453',
    parent=TEST_TOP_LEVEL_FOLDER_NAME)

TEST_SUBFOLDER_B = messages.Folder(
    createTime=u'2016-10-24T18:36:51.980Z',
    displayName=u'Folder B',
    lifecycleState=FOLDER_ACTIVE,
    name=u'folders/740752656255',
    parent=TEST_TOP_LEVEL_FOLDER_NAME)


class FolderIntegrationTest(e2e_base.WithServiceAuth):

  messages = folders.FoldersMessages()

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribeFolder(self):
    result = self.RunFolders('describe', TEST_TOP_LEVEL_FOLDER_ID)
    self.assertEqual(result, TEST_TOP_LEVEL_FOLDER)

  @test_case.Filters.skip('consistently failing', 'b/62423326')
  def testListFoldersInOrganization(self):
    result = self.RunFolders('list', '--organization', TEST_ORGANIZATION_ID)
    self.assertEqual(list(result), [TEST_TOP_LEVEL_FOLDER])

  @test_case.Filters.skip('Failing consistently', 'b/78307868')
  def testListFoldersInFolder(self):
    result = self.RunFolders('list', '--folder', TEST_TOP_LEVEL_FOLDER_ID)
    self.assertEqual(list(result), [TEST_SUBFOLDER_A, TEST_SUBFOLDER_B])

  def testSetIamPolicy(self):
    folder_id = folders.FolderNameToId(TEST_SUBFOLDER_B.name)

    new_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                members=[u'serviceAccount:' + self.Account()],
                role=u'roles/owner')
        ],
        version=0)

    # Because this policy won't mess up any other integration
    # tests, we don't need to worry about changing it back to
    # the original policy (which is nontrivial to perform safely
    # in an environment where tests can be executed concurrently).
    created_policy = self.setIamPolicy(folder_id, new_policy)

    self.assertListEqual(created_policy.auditConfigs, [])
    self.assertListEqual(created_policy.bindings, new_policy.bindings)

  def setIamPolicy(self, resource_id, policy):
    json = encoding.MessageToJson(policy)
    policy_file_path = self.Touch(self.temp_path, 'good.json', contents=json)
    return self.RunFolders('set-iam-policy', resource_id, policy_file_path)

  def RunFolders(self, *command):
    return self.Run(['alpha', 'resource-manager', 'folders'] + list(command))


if __name__ == '__main__':
  test_case.main()
