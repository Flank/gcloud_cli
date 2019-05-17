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
"""ai-platform models get-iam-policy tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class GetIamPolicyUnitTestGA(base.MlGaPlatformTestBase):

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
        etag=b'abcd'
    )
    self.client.projects_models.GetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=self.policy)

  def testGetIamPolicy(self, module_name):
    response = self.Run('{} models get-iam-policy myModel '
                        '    --format disable'.format(module_name))

    self.assertEqual(response, self.policy)

  def testGetIamPolicyOutput(self, module_name):
    self.Run('{} models get-iam-policy myModel'.format(module_name))

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

  def testListCommandFilter(self, module_name):
    self.Run("""
        {} models get-iam-policy myModel
        --flatten=bindings[].members
        --filter=bindings.role:roles/owner
        --format=table[no-heading](bindings.members:sort=1)
        """.format(module_name))

    self.AssertOutputEquals(
        'user:test-owner1@gmail.com\nuser:test-owner2@gmail.com\n')


class GetIamPolicyUnitTestBeta(base.MlBetaPlatformTestBase,
                               GetIamPolicyUnitTestGA):
  pass


class GetIamPolicyUnitTestAlpha(base.MlAlphaPlatformTestBase,
                                GetIamPolicyUnitTestBeta):
  pass


@parameterized.parameters('ml-engine', 'ai-platform')
class GetIamPolicyErrorUnitTestGA(base.MlGaPlatformTestBase):

  def testGetIamPolicyModelRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument MODEL: Must be specified.'):
      self.Run('{} models get-iam-policy'.format(module_name))


class GetIamPolicyErrorUnitTestBeta(base.MlBetaPlatformTestBase,
                                    GetIamPolicyErrorUnitTestGA):
  pass


class GetIamPolicyErrorUnitTestAlpha(base.MlAlphaPlatformTestBase,
                                     GetIamPolicyErrorUnitTestBeta):
  pass


if __name__ == '__main__':
  test_case.main()
