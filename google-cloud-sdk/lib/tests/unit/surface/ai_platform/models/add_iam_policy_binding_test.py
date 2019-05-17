# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""ai-platform models add-iam-policy-binding tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ml_engine import models_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

import mock


@parameterized.parameters('ml-engine', 'ai-platform')
class AddIamPolicyBindingUnitTest(base.MlGaPlatformTestBase):

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
        etag=b'abcd'
    )
    self.add_iam_policy_binding = self.StartObjectPatch(
        models_util, 'AddIamPolicyBinding', return_value=self.policy)

  def testAddIamPolicyBinding(self, module_name):
    response = self.Run('{} models add-iam-policy-binding myModel '
                        '    --role roles/editor '
                        '    --member user:test-user1@gmail.com '
                        '    --format disable'.format(module_name))

    self.assertEqual(response, self.policy)
    self.add_iam_policy_binding.assert_called_once_with(
        mock.ANY, 'myModel', 'user:test-user1@gmail.com', 'roles/editor')

  def testAddIamPolicyBindingOutput(self, module_name):
    self.Run('{} models add-iam-policy-binding myModel '
             '    --role roles/editor '
             '    --member user:test-user1@gmail.com'.format(module_name))

    self.AssertOutputEquals("""\
        bindings:
        - members:
          - user:test-user1@gmail.com
          - user:test-user2@gmail.com
        role: roles/editor
        etag: YWJjZA==
        """, normalize_space=True)
    self.add_iam_policy_binding.assert_called_once_with(
        mock.ANY, 'myModel', 'user:test-user1@gmail.com', 'roles/editor')

  def testAddIamPolicyBindingRoleRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --role: Must be specified.'):
      self.Run('{} models add-iam-policy-binding myModel '
               '    --member user:test-user1@gmail.com'.format(module_name))

  def testAddIamPolicyBindingMemberRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --member: Must be specified.'):
      self.Run('{} models add-iam-policy-binding myModel '
               '    --role roles/editor'.format(module_name))

  def testAddIamPolicyBindingModelRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument MODEL: Must be specified.'):
      self.Run('{} models add-iam-policy-binding '
               '    --role roles/editor '
               '    --member user:test-user1@gmail.com'.format(module_name))


@parameterized.parameters('ml-engine', 'ai-platform')
class AddIamPolicyBindingIntegrationTest(base.MlGaPlatformTestBase):

  def testAddIamPolicyBinding(self, module_name):
    original_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    new_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com', 'user:user2@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    self.client.projects_models.GetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=original_policy)
    request = self.msgs.GoogleIamV1SetIamPolicyRequest(
        policy=new_policy,
        updateMask='bindings,etag')
    self.client.projects_models.SetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=request,
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=new_policy)

    self.Run('{} models add-iam-policy-binding myModel '
             '    --role roles/owner '
             '    --member user:user2@gmail.com'.format(module_name))


if __name__ == '__main__':
  test_case.main()
