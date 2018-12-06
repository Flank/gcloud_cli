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
"""ml-engine models set-iam-policy tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.ml_engine import models_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class SetIamPolicyUnitTests(base.MlGaPlatformTestBase):

  POLICY_FILE = {
      'bindings': [{
          'members': ['user:email1@gmail.com', 'user:user2@gmail.com'],
          'role': 'roles/owner'
      }],
      'etag': 'YWJjZA==',
      'version': 1
  }

  def SetUp(self):
    self.policy = encoding.DictToMessage(self.POLICY_FILE,
                                         self.msgs.GoogleIamV1Policy)

  def testSetIamPolicy(self, track):
    self.track = track
    self.set_iam_policy = self.StartObjectPatch(
        iam_util, 'ParsePolicyFileWithUpdateMask',
        return_value=(self.policy, 'bindings,etag,version'))

    iam_request = self.msgs.GoogleIamV1SetIamPolicyRequest(
        policy=self.policy,
        updateMask='bindings,etag,version')
    ml_set_iam_request = self.msgs.MlProjectsModelsSetIamPolicyRequest(
        googleIamV1SetIamPolicyRequest=iam_request,
        resource='projects/{}/models/myModel'.format(self.Project()))
    self.client.projects_models.SetIamPolicy.Expect(
        request=ml_set_iam_request,
        response=self.policy)

    response = self.Run('ml-engine models set-iam-policy myModel policy_file '
                        '--format disable')

    self.assertEqual(response, self.policy)
    self.set_iam_policy.assert_called_once_with(
        'policy_file', self.msgs.GoogleIamV1Policy)

  def testSetIamPolicyOutput(self, track):
    self.set_iam_policy = self.StartObjectPatch(
        iam_util, 'ParsePolicyFileWithUpdateMask',
        return_value=(self.policy, 'bindings,etag,version'))

    request = self.msgs.GoogleIamV1SetIamPolicyRequest(
        policy=self.policy,
        updateMask='bindings,etag,version')
    self.client.projects_models.SetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=request,
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=self.policy)
    self.Run('ml-engine models set-iam-policy myModel policy.json')

    self.AssertOutputEquals("""\
        bindings:
        - members:
        - user:email1@gmail.com
        - user:user2@gmail.com
        role: roles/owner
        etag: YWJjZA==
        version: 1
        """, normalize_space=True)
    self.set_iam_policy.assert_called_once_with(
        'policy.json', self.msgs.GoogleIamV1Policy)

  def testSetIamPolicyPolicyFileRequired(self, track):
    self.track = track
    self.set_iam_policy = self.StartObjectPatch(
        models_util, 'SetIamPolicy', return_value=self.policy)
    with self.AssertRaisesArgumentErrorMatches(
        'argument POLICY_FILE: Must be specified.'):
      self.Run('ml-engine models set-iam-policy myModel')


if __name__ == '__main__':
  test_case.main()
