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
"""ml-engine models set-iam-policy tests."""

from googlecloudsdk.command_lib.ml_engine import models_util
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

import mock


class SetIamPolicyUnitTestse(base.MlGaPlatformTestBase):

  def SetUp(self):
    self.policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=[
                    'user:test-user1@gmail.com',
                    'user:test-user2@gmail.com'
                ],
                role='roles/editor'
            )
        ],
        etag='abcd'
    )
    self.set_iam_policy = self.StartObjectPatch(
        models_util, 'SetIamPolicy', return_value=self.policy)

  def testSetIamPolicy(self):
    response = self.Run('ml-engine models set-iam-policy myModel policy.json '
                        '    --format disable')

    self.assertEquals(response, self.policy)
    self.set_iam_policy.assert_called_once_with(
        mock.ANY, 'myModel', 'policy.json')

  def testSetIamPolicyOutput(self):
    self.Run('ml-engine models set-iam-policy myModel policy.json')

    self.AssertOutputEquals("""\
        bindings:
        - members:
          - user:test-user1@gmail.com
          - user:test-user2@gmail.com
        role: roles/editor
        etag: YWJjZA==
        """, normalize_space=True)
    self.set_iam_policy.assert_called_once_with(
        mock.ANY, 'myModel', 'policy.json')

  def testSetIamPolicyPolicyFileRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument POLICY_FILE: Must be specified.'):
      self.Run('ml-engine models set-iam-policy myModel')


class SetIamPolicyIntegrationTestBase(base.MlGaPlatformTestBase):

  POLICY_FILE = """\
      {
        "bindings": [
          {
            "members": [
              "user:email1@gmail.com",
              "user:user2@gmail.com"
            ],
            "role": "roles/owner"
          }
        ],
        "etag": "YWJjZA==",
        "version": 1
      }
  """

  def testSetIamPolicy(self):
    policy_file = self.Touch(self.temp_path, 'policy.json',
                             contents=self.POLICY_FILE)
    new_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com', 'user:user2@gmail.com'],
                role='roles/owner')],
        etag='abcd',
        version=1)
    request = self.msgs.GoogleIamV1SetIamPolicyRequest(
        policy=new_policy,
        updateMask='bindings,etag,version')
    self.client.projects_models.SetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=request,
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=new_policy)

    self.Run('ml-engine models set-iam-policy myModel {}'.format(policy_file))


if __name__ == '__main__':
  test_case.main()
