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

"""Tests that exercise the 'gcloud dns policies describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_beta


class DescribeTest(base.DnsMockBetaTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribe(self):
    expected_output = util_beta.GetPolicies(networks=[], num=1).pop()
    describe_req = self.messages.DnsPoliciesGetRequest(
        project=self.Project(), policy='mypolicy0')
    self.client.policies.Get.Expect(
        request=describe_req, response=expected_output)
    actual_output = self.Run('dns policies describe mypolicy0')
    self.assertEqual(expected_output, actual_output)


if __name__ == '__main__':
  test_case.main()
