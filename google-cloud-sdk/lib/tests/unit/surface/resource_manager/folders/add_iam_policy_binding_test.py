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

import copy

from googlecloudsdk.api_lib.resource_manager import folders
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersAddIamPolicyBindingTest(testbase.FoldersUnitTestBase):

  messages = testbase.FoldersUnitTestBase.messages

  NEW_ROLE = 'roles/resourcemanager.projectCreator'
  NEW_USER = 'user:fox@google.com'

  def testAddIamPolicyBinding(self):
    """Test the standard use case."""
    self.mock_folders.GetIamPolicy.Expect(self.ExpectedGetRequest(),
                                          copy.deepcopy(self._MakePolicy()))
    new_policy = self._MakePolicy(self.NEW_USER)
    self.mock_folders.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
            foldersId=folders.FolderIdToName(self.TEST_FOLDER.name),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    self.assertEqual(self.DoRequest(), new_policy)

  def testAddIamPolicyBindingFolder_raisesFolderNotFoundError(self):
    self.SetupGetIamPolicyFailure(testbase.HTTP_404_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'Folder [BAD_ID] not found: Resource not found.', self.DoRequest)

  def testAddIamPolicyBindingFolder_raisesFolderAccessError(self):
    self.SetupGetIamPolicyFailure(testbase.HTTP_403_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access folder [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount()), self.DoRequest)

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerFoldersGetIamPolicyRequest(
        foldersId=folders.FolderIdToName(self.TEST_FOLDER.name))

  def SetupGetIamPolicyFailure(self, exception):
    self.mock_folders.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), exception=exception)

  def DoRequest(self):
    return self.RunFolders('add-iam-policy-binding',
                           folders.FolderIdToName(self.TEST_FOLDER.name),
                           '--role={0}'.format(self.NEW_ROLE),
                           '--member={0}'.format(self.NEW_USER))

  def _MakePolicy(self, extra_member=None):
    members = [u'domain:foo.com']
    if extra_member:
      members.append(extra_member)
    return self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role=u'roles/resourcemanager.projectCreator', members=members),
            self.messages.Binding(
                role=u'roles/resourcemanager.folderAdmin',
                members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)


if __name__ == '__main__':
  test_case.main()
