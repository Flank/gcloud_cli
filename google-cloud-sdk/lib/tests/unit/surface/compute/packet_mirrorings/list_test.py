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
"""Tests for the packet mirrorings list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock


class ListTestBeta(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(self._GetPacketMirrorings()))

  def testList(self):
    self.Run("""
      compute packet-mirrorings list
    """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME REGION NETWORK PRIORITY ENABLE
            pm-1 us-central1 default 1000 TRUE
            pm-2 us-central2 default 999 FALSE
            """),
        normalize_space=True)

  def _GetPacketMirrorings(self):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')
    forwarding_rule_ref = self.resources.Create(
        'compute.forwardingRules',
        region='us-central1',
        forwardingRule='fr-1',
        project='my-project')

    return [
        self.messages.PacketMirroring(
            name='pm-1',
            region='us-central1',
            priority=1000,
            network=self.messages.PacketMirroringNetworkInfo(
                url=network_ref.SelfLink()),
            collectorIlb=self.messages.PacketMirroringForwardingRuleInfo(
                url=forwarding_rule_ref.SelfLink()),
            mirroredResources=self.messages
            .PacketMirroringMirroredResourceInfo(tags=['tag-1']),
            enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE),
        self.messages.PacketMirroring(
            name='pm-2',
            region='us-central2',
            priority=999,
            network=self.messages.PacketMirroringNetworkInfo(
                url=network_ref.SelfLink()),
            collectorIlb=self.messages.PacketMirroringForwardingRuleInfo(
                url=forwarding_rule_ref.SelfLink()),
            mirroredResources=self.messages
            .PacketMirroringMirroredResourceInfo(tags=['tag-1']),
            enable=self.messages.PacketMirroring.EnableValueValuesEnum.FALSE)
    ]


class ListTestAlpha(ListTestBeta):

  def SetUp(self):
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
