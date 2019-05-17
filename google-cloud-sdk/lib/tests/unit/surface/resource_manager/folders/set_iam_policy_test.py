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

from apitools.base.py import encoding

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import http_encoding
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersSetIamPolicyTest(testbase.FoldersUnitTestBase):

  def testSetIamPolicyFolder(self):
    self.mock_folders.SetIamPolicy.Expect(self.DefaultRequest(),
                                          self._MakePolicy())
    self.DoRequest()
    folder_name = self.TEST_FOLDER.name
    self.AssertErrContains(
        'Updated IAM policy for folder [folders/{}]'.format(folder_name))

  def testBadJsonOrYamlSetIamPolicyFolder(self):
    policy_file_path = self.Touch(self.temp_path, 'bad', contents='bad')
    with self.assertRaises(exceptions.Error):
      self.RunSetIamPolicy(policy_file_path)

  def testNoFileSetIamPolicyFolder(self):
    with self.assertRaises(exceptions.Error):
      self.RunSetIamPolicy('/some/bad/path/to/non/existent/file')

  def testSetIamPolicyFolder_raisesFolderNotFoundError(self):
    self.SetupSetIamPolicyFailure(testbase.HTTP_404_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'Folder [BAD_ID] not found: Resource not found.', self.DoRequest)

  def testSetIamPolicyFolder_raisesFolderAccessError(self):
    self.SetupSetIamPolicyFailure(testbase.HTTP_403_ERR)
    self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access folder [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount()), self.DoRequest)

  def testSetIamPolicyFolder_clearBindingsAndEtag_policySetsBindingsAndEtag(
      self):
    policy = self._GetTestIamPolicy(clear_fields=['bindings', 'etag'])
    expected_request = (
        self.messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
            foldersId=folders.FolderIdToName(self.TEST_FOLDER.name),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                updateMask='auditConfigs,version,bindings,etag',),))

    self.mock_folders.SetIamPolicy.Expect(expected_request, policy)

    # Setting the IAM policy yields no result, it's just a side-effect,
    # so we offload the test assertion to the mock.
    self.DoRequest(policy)

  def testSetIamPolicyFolder_auditConfigsPreserved(self):
    policy = self._GetTestIamPolicy(clear_fields=['auditConfigs'])

    expected_request = (
        self.messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
            foldersId=folders.FolderIdToName(self.TEST_FOLDER.name),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                updateMask='bindings,etag,version',),))

    self.mock_folders.SetIamPolicy.Expect(expected_request,
                                          self._GetTestIamPolicy())

    # Setting the IAM policy yields no result, it's just a side-effect,
    # so we offload the test assertion to the mock.
    self.DoRequest(policy)

  def DefaultRequest(self):
    return self.messages.CloudresourcemanagerFoldersSetIamPolicyRequest(
        foldersId=folders.FolderIdToName(self.TEST_FOLDER.name),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(
            policy=self._MakePolicy(), updateMask='bindings,etag,version'))

  def SetupSetIamPolicyFailure(self, exception):
    self.mock_folders.SetIamPolicy.Expect(
        self.DefaultRequest(), exception=exception)

  def RunSetIamPolicy(self, policy_file_path):
    self.RunFolders('set-iam-policy',
                    folders.FolderIdToName(self.TEST_FOLDER.name),
                    policy_file_path)

  def DoRequest(self, policy=None):
    json = encoding.MessageToJson(policy if policy else self._MakePolicy())
    policy_file_path = self.Touch(self.temp_path, 'good.json', contents=json)
    self.RunSetIamPolicy(policy_file_path)

  def _MakePolicy(self):
    return self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/resourcemanager.projectCreator',
                members=['domain:foo.com']), self.messages.Binding(
                    role='roles/resourcemanager.organizationAdmin',
                    members=['user:admin@foo.com'])
        ],
        etag=http_encoding.Encode('someUniqueEtag'),
        version=1)


class FoldersSetIamPolicyAlphaTest(FoldersSetIamPolicyTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class FoldersSetIamPolicyBetaTest(FoldersSetIamPolicyTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
