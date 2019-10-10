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

"""Tests for Cloud Functions set-iam-policy surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.functions import base


class SetIamPolicyBetaTest(base.FunctionsTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def test_set_iam_policy(self):
    function_ref_name = 'projects/{}/locations/{}/functions/my-function'.format(
        self.Project(), self.GetRegion())
    expected_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:foo@google.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    policy_json = encoding.MessageToJson(expected_policy)
    temp_file = self.Touch(self.temp_path, contents=policy_json)

    set_request = \
      self.messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=function_ref_name,
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=expected_policy, updateMask='bindings,etag,version'))
    self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
        set_request,
        response=expected_policy)
    actual_policy = self.Run(
        'functions set-iam-policy my-function {0}'.format(temp_file))
    self.assertEqual(expected_policy, actual_policy)
    self.AssertErrContains('Updated IAM policy for function [my-function].')


class SetIamPolicyAlphaTest(SetIamPolicyBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
