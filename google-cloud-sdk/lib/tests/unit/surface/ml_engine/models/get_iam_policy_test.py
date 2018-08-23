# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
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
        etag=b'abcd'
    )
    self.client.projects_models.GetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=self.policy)

  def testGetIamPolicy(self, track):
    self.track = track
    response = self.Run('ml-engine models get-iam-policy myModel '
                        '    --format disable')

    self.assertEqual(response, self.policy)

  def testGetIamPolicyOutput(self, track):
    self.track = track
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

  def testListCommandFilter(self, track):
    self.track = track
    self.Run("""
        ml-engine models get-iam-policy myModel
        --flatten=bindings[].members
        --filter=bindings.role:roles/owner
        --format=table[no-heading](bindings.members:sort=1)
        """)

    self.AssertOutputEquals(
        'user:test-owner1@gmail.com\nuser:test-owner2@gmail.com\n')


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class GetIamPolicyErrorUnitTest(base.MlGaPlatformTestBase):

  def testGetIamPolicyModelRequired(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        'argument MODEL: Must be specified.'):
      self.Run('ml-engine models get-iam-policy')


if __name__ == '__main__':
  test_case.main()
