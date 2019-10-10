# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the instances move subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class VpnGatewaysGetStatusGaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.api_version = 'v1'
    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.message_version = self.compute_v1

  def testCall(self):
    self.make_requests.side_effect = [[self.messages.VpnGatewayStatus()]]

    self.Run("""
        compute vpn-gateways get-status my-gateway --region us-central1
        """)

    self.CheckRequests([(self.message_version.vpnGateways, 'GetStatus',
                         self.messages.ComputeVpnGatewaysGetStatusRequest(
                             project='my-project',
                             region='us-central1',
                             vpnGateway='my-gateway'))])


class VpnGatewaysGetStatusBetaTest(VpnGatewaysGetStatusGaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.api_version = 'beta'
    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.message_version = self.compute_beta


class VpnGatewaysGetStatusAlphaTest(VpnGatewaysGetStatusBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.api_version = 'alpha'
    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.message_version = self.compute_alpha


if __name__ == '__main__':
  test_case.main()
