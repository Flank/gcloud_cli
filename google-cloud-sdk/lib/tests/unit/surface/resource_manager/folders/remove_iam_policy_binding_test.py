# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.core.util import http_encoding
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersRemoveIamPolicyBindingTest(testbase.FoldersUnitTestBase):

  messages = testbase.FoldersUnitTestBase.messages

  REMOVE_USER = 'user:admin@foo.com'
  REMOVE_ROLE = 'roles/resourcemanager.folderAdmin'
  START_POLICY = messages.Policy(
      bindings=[
          messages.Binding(
              role='roles/resourcemanager.projectCreator',
              members=['domain:foo.com']), messages.Binding(
                  role='roles/resourcemanager.folderAdmin',
                  members=['user:admin@foo.com'])
      ],
      etag=http_encoding.Encode('someUniqueEtag'),
      version=1)
  NEW_POLICY = messages.Policy(
      bindings=[
          messages.Binding(
              role='roles/resourcemanager.projectCreator',
              members=['domain:foo.com'])
      ],
      etag=http_encoding.Encode('someUniqueEtag'),
      version=1)

  def testRemoveIamPolicyBinding(self):
    """Test the standard use case."""
    self.mock_folders.GetIamPolicy.Expect(self.ExpectedGetRequest(),
                                          copy.deepcopy(self.START_POLICY))
    self.mock_folders.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
            foldersId=folders.FolderIdToName(self.TEST_FOLDER.name),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.NEW_POLICY)), self.NEW_POLICY)

    self.assertEqual(self.DoRequest(), self.NEW_POLICY)

  def testRemoveIamPolicyBindingFolder_raisesFolderNotFoundError(self):
    self.SetupGetIamPolicyFailure(testbase.HTTP_404_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'Folder [BAD_ID] not found: Resource not found.', self.DoRequest)

  def testRemoveIamPolicyBindingFolder_raisesFolderAccessError(self):
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
    return self.RunFolders('remove-iam-policy-binding',
                           folders.FolderIdToName(self.TEST_FOLDER.name),
                           '--role={0}'.format(self.REMOVE_ROLE),
                           '--member={0}'.format(self.REMOVE_USER))


if __name__ == '__main__':
  test_case.main()
