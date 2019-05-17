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

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import http_encoding
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersGetIamPolicyTest(testbase.FoldersUnitTestBase):

  def testGetIamPolicyFolder(self):
    test_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/resourcemanager.projectCreator',
                members=['domain:foo.com']), self.messages.Binding(
                    role='roles/resourcemanager.organizationAdmin',
                    members=['user:admin@foo.com'])
        ],
        etag=http_encoding.Encode('someUniqueEtag'),
        version=1)
    self.mock_folders.GetIamPolicy.Expect(self.ExpectedRequest(), test_policy)
    self.assertEqual(self.DoRequest(), test_policy)

  def testGetIamPolicyFolderListCommandFilter(self):
    test_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/resourcemanager.projectCreator',
                members=['domain:foo.com']), self.messages.Binding(
                    role='roles/resourcemanager.organizationAdmin',
                    members=['user:admin@foo.com'])
        ],
        etag=http_encoding.Encode('someUniqueEtag'),
        version=1)
    self.mock_folders.GetIamPolicy.Expect(self.ExpectedRequest(), test_policy)
    args = [
        '--flatten=bindings[].members',
        '--filter=bindings.role:roles/resourcemanager.organizationAdmin',
        '--format=table[no-heading](bindings.members:sort=1)',
    ]
    self.DoRequest(args)
    self.AssertOutputEquals('user:admin@foo.com\n')

  def testGetIamPolicyFolder_raisesFolderNotFoundError(self):
    self.SetupGetIamPolicyFailure(testbase.HTTP_404_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'Folder [BAD_ID] not found: Resource not found.', self.DoRequest)

  def testGetIamPolicyFolder_raisesFolderAccessError(self):
    self.SetupGetIamPolicyFailure(testbase.HTTP_403_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access folder [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount()), self.DoRequest)

  def SetupGetIamPolicyFailure(self, exception):
    self.mock_folders.GetIamPolicy.Expect(
        self.ExpectedRequest(), exception=exception)

  def ExpectedRequest(self):
    return self.messages.CloudresourcemanagerFoldersGetIamPolicyRequest(
        foldersId=folders.FolderNameToId(self.TEST_FOLDER.name))

  def DoRequest(self, args=None):
    command = ['get-iam-policy', folders.FolderNameToId(self.TEST_FOLDER.name)]
    if args:
      command += args
    return self.RunFolders(*command)


class FoldersGetIamPolicyAlphaTest(FoldersGetIamPolicyTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class FoldersGetIamPolicyBetaTest(FoldersGetIamPolicyTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
