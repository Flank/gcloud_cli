# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for Cloud Functions get-iam-policy surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.functions import base


class GetIamPolicyTest(base.FunctionsTestBase):

  def test_get_iam_policy(self):
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
    self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
        self.messages.
        CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
            resource=function_ref_name),
        response=expected_policy)
    actual_policy = self.Run('alpha functions get-iam-policy my-function')
    self.assertEqual(expected_policy, actual_policy)


if __name__ == '__main__':
  test_case.main()
