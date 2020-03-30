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
"""Tests for the packet mirrorings describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.compute = self.compute_v1

  def testDescribe(self):
    name = 'pm-1'
    region = 'us-central1'
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')
    forwarding_rule_ref = self.resources.Create(
        'compute.forwardingRules',
        region='us-central1',
        forwardingRule='fr-1',
        project='my-project')

    packet_mirroring = self.messages.PacketMirroring(
        name=name,
        region=region,
        network=self.messages.PacketMirroringNetworkInfo(
            url=network_ref.SelfLink()),
        collectorIlb=self.messages.PacketMirroringForwardingRuleInfo(
            url=forwarding_rule_ref.SelfLink()),
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['tag-1']),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.FALSE)
    self.make_requests.side_effect = iter([
        [packet_mirroring],
    ])

    self.Run('compute packet-mirrorings describe {} --region {}'.format(
        name, region))

    self.CheckRequests([(self.compute.packetMirrorings, 'Get',
                         self.messages.ComputePacketMirroringsGetRequest(
                             packetMirroring=name,
                             project='my-project',
                             region=region))])
    self.AssertOutputContains('name: {}'.format(name))


class DescribeTestBeta(DescribeTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.compute = self.compute_beta


class DescribeTestAlpha(DescribeTestBeta):

  def SetUp(self):
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.compute = self.compute_alpha

if __name__ == '__main__':
  test_case.main()
