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
"""Tests that exercise the 'gcloud dns policies list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_beta


class ListTest(base.DnsMockBetaTest):

  def testListPolicies(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    expected_output = util_beta.GetPolicies(networks=['1.0.1.1', '1.0.1.2'])
    list_request = self.messages.DnsPoliciesListRequest(project=self.Project())
    self.client.policies.List.Expect(
        request=list_request,
        response=self.messages.PoliciesListResponse(policies=expected_output))
    actual_output = self.Run('dns policies list')
    self.assertEqual(expected_output, actual_output)

  def testListPoliciesFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    list_request = self.messages.DnsPoliciesListRequest(project=self.Project())
    test_networks = [
        util_beta.GetNetworkURI('default', self.Project()),
        util_beta.GetNetworkURI('network1', self.Project())
    ]
    name_servers = util_beta.GetAltNameServerConfig(['2.0.1.1', '2.0.1.2'])
    expected_output = util_beta.GetPolicies(
        name_server_config=name_servers,
        networks=test_networks,
        forwarding=True)
    self.client.policies.List.Expect(
        request=list_request,
        response=self.messages.PoliciesListResponse(policies=expected_output))
    self.Run('dns policies list')
    self.AssertOutputContains(
        """\
NAME DESCRIPTION FORWARDING ALTERNATE_NAME_SERVERS NETWORKS
mypolicy0 My policy 0 True 2.0.1.1, 2.0.1.2 default, network1
mypolicy1 My policy 1 True 2.0.1.1, 2.0.1.2 default, network1
mypolicy2 My policy 2 True 2.0.1.1, 2.0.1.2 default, network1
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
