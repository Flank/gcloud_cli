# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
"""ml-engine models get-iam-policy tests."""

from googlecloudsdk.command_lib.ml_engine import models_util
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

import mock


class GetIamPolicyUnitTest(base.MlGaPlatformTestBase):

  def SetUp(self):
    self.policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=[
                    'user:test-user1@gmail.com',
                    'user:test-user2@gmail.com'
                ],
                role='roles/editor'
            ),
            self.msgs.GoogleIamV1Binding(
                members=[
                    'user:test-owner1@gmail.com',
                    'user:test-owner2@gmail.com'
                ],
                role='roles/owner'
            )
        ],
        etag='abcd'
    )
    self.get_iam_policy = self.StartObjectPatch(
        models_util, 'GetIamPolicy', return_value=self.policy)

  def testGetIamPolicy(self):
    response = self.Run('ml-engine models get-iam-policy myModel '
                        '    --format disable')

    self.assertEquals(response, self.policy)
    self.get_iam_policy.assert_called_once_with(mock.ANY, 'myModel')

  def testGetIamPolicyOutput(self):
    self.Run('ml-engine models get-iam-policy myModel')

    self.AssertOutputEquals("""\
        bindings:
        - members:
          - user:test-user1@gmail.com
          - user:test-user2@gmail.com
        role: roles/editor
        - members:
          - user:test-owner1@gmail.com
          - user:test-owner2@gmail.com
        role: roles/owner
        etag: YWJjZA==
        """, normalize_space=True)
    self.get_iam_policy.assert_called_once_with(mock.ANY, 'myModel')

  def testListCommandFilter(self):
    self.Run("""
        ml-engine models get-iam-policy myModel
        --flatten=bindings[].members
        --filter=bindings.role:roles/owner
        --format=table[no-heading](bindings.members:sort=1)
        """)

    self.AssertOutputEquals(
        'user:test-owner1@gmail.com\nuser:test-owner2@gmail.com\n')

  def testGetIamPolicyModelRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument MODEL: Must be specified.'):
      self.Run('ml-engine models get-iam-policy')


class GetIamPolicyIntegrationTestBase(base.MlGaPlatformTestBase):

  def testGetIamPolicy(self):
    policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com'],
                role='roles/owner')],
        etag='abcd')
    self.client.projects_models.GetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=policy)

    self.Run('ml-engine models get-iam-policy myModel')


if __name__ == '__main__':
  test_case.main()
