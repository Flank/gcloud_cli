# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the vpn-tunnels delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.exceptions import ToolException
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class VpnTunnelsDeleteTest(test_base.BaseTest):

  def testSimpleInvocationMakesRightRequest(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute vpn-tunnels delete tunnel-1
          --region region-1
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-1',
              project='my-project',
              region='region-1'))],
    )

  def testInvocationWithMultipleTunnelsOk(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute
             vpn-tunnels delete tunnel-1 tunnel-2 tunnel-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-1',
              project='my-project',
              region='us-central2')),
         (self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-2',
              project='my-project',
              region='us-central2')),
         (self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-3',
              project='my-project',
              region='us-central2'))])

  def testReplyingYesToPromptContinues(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute vpn-tunnels delete tunnel-1 tunnel-2 tunnel-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-1',
              project='my-project',
              region='us-central2')),
         (self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-2',
              project='my-project',
              region='us-central2')),
         (self.compute.vpnTunnels,
          'Delete',
          messages.ComputeVpnTunnelsDeleteRequest(
              vpnTunnel='tunnel-3',
              project='my-project',
              region='us-central2'))])

  def testReplyingNoToPromptAborts(self):
    self.WriteInput('n\n')
    with self.assertRaises(ToolException):
      self.Run("""
          compute vpn-tunnels delete
               tunnel-1 tunnel-2 tunnel-3
            --region us-central2
          """)

    self.CheckRequests()
    self.AssertErrContains('Deletion aborted by user.')


if __name__ == '__main__':
  test_case.main()
