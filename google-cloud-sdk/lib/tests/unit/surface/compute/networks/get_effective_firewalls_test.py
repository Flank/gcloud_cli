# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for the networks get-effective-firewalls subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.util import apis as core_apis

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GetEffectiveFirewallsAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.api_version = 'alpha'
    self.SelectApi(self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)

  def testGetEffectiveFirewalls(self):
    self.make_requests.side_effect = iter([[
        self.messages.NetworksGetEffectiveFirewallsResponse(firewalls=[
            self.messages.Firewall(
                direction=self.messages.Firewall.DirectionValueValuesEnum
                .INGRESS,
                priority=10,
                name='rule10'),
            self.messages.Firewall(
                direction=self.messages.Firewall.DirectionValueValuesEnum
                .EGRESS,
                priority=8,
                name='rule8'),
            self.messages.Firewall(
                direction=self.messages.Firewall.DirectionValueValuesEnum
                .INGRESS,
                priority=9,
                name='rule9')
        ])
    ]])

    self.Run(self.api_version +
             ' compute networks get-effective-firewalls my-network')

    self.CheckRequests(
        [(self.compute.networks, 'GetEffectiveFirewalls',
          self.messages.ComputeNetworksGetEffectiveFirewallsRequest(
              network='my-network', project=self.Project()))],)

    expected_str = textwrap.dedent(
        'TYPE              SECURITY_POLICY_ID  PRIORITY  ACTION  DIRECTION  IP_RANGES\n'
        'network-firewall                      9         DENY    INGRESS\n'
        'network-firewall                      10        DENY    INGRESS\n'
        'network-firewall                      8         DENY    EGRESS')

    self.assertMultiLineEqual(self.GetOutput().strip(),
                              textwrap.dedent(expected_str))


class GetEffectiveFirewallsBetaTest(GetEffectiveFirewallsAlphaTest):

  def SetUp(self):
    self.api_version = 'beta'
    self.SelectApi(self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)


if __name__ == '__main__':
  test_case.main()
