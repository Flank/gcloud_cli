# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for Cloud Functions remove-iam-policy-binding surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.functions import base


class RemoveIamPolicyBindingTest(base.FunctionsTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def test_remove_iam_policy_binding(self):
    function_ref_name = 'projects/{}/locations/{}/functions/my-function'.format(
        self.Project(), self.GetRegion())
    role_to_remove = 'roles/cloudfunctions.invoker'
    user_to_remove = 'user:olduser@google.com'
    start_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:foo@google.com', user_to_remove])
        ],
        etag=b'someUniqueEtag',
        version=1)
    expected_updated_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:foo@google.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
        self.messages.
        CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
            resource=function_ref_name),
        response=start_policy)
    set_request = \
      self.messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=function_ref_name,
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=expected_updated_policy))
    self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
        set_request,
        response=expected_updated_policy)
    actual_updated_policy = self.Run("""
        functions remove-iam-policy-binding \
        my-function --role={0} --member={1}
        """.format(role_to_remove, user_to_remove))
    self.assertEqual(expected_updated_policy, actual_updated_policy)


class RemoveIamPolicyBindingAlphaTest(RemoveIamPolicyBindingTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
