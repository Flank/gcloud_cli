# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the firewall-rules describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class FirewallRulesDescribeTest(test_base.BaseTest,
                                completer_test_base.GRICompleterBase,
                                test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def GetFirewall(self):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')

    deny_ingress_ref = self.resources.Create(
        'compute.firewalls',
        firewall='default-deny-ingress',
        project='my-project')
    deny_ingress = self.messages.Firewall(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(IPProtocol='all'),
        ],
        name='default-deny-ingress',
        network=network_ref.SelfLink(),
        selfLink=deny_ingress_ref.SelfLink(),
        sourceRanges=['0.0.0.0/0'],
        priority=65535,
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS)

    allow_internal_ref = self.resources.Create(
        'compute.firewalls',
        firewall='default-allow-internal',
        project='my-project')
    allow_internal = self.messages.Firewall(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='tcp', ports=['1-65535']),
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='udp', ports=['1-65535']),
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='icmp'),
        ],
        name='default-allow-internal',
        network=network_ref.SelfLink(),
        selfLink=allow_internal_ref.SelfLink(),
        priority=65534,
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        sourceRanges=['10.0.0.0/8'],
        sourceTags=['tag-1', 'tag-2'])

    allow_egress_ref = self.resources.Create(
        'compute.firewalls',
        firewall='default-allow-egress',
        project='my-project')
    allow_egress = self.messages.Firewall(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='all'),
        ],
        name='default-allow-egress',
        network=network_ref.SelfLink(),
        selfLink=allow_egress_ref.SelfLink(),
        destinationRanges=['0.0.0.0/0'],
        direction=self.messages.Firewall.DirectionValueValuesEnum.EGRESS,
        targetTags=['tag-3', 'tag-4'])
    return [deny_ingress, allow_internal, allow_egress]

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self.GetFirewall()[0]],
    ])

    self.Run("""
        compute firewall-rules describe my-firewall
        """)

    self.CheckRequests(
        [(self.compute_v1.firewalls, 'Get',
          self.messages.ComputeFirewallsGetRequest(
              firewall='my-firewall', project='my-project'))],)
    self.assertMultiLineEqual(self.GetOutput(),
                              textwrap.dedent("""\
            denied:
            - IPProtocol: all
            direction: INGRESS
            name: default-deny-ingress
            network: https://compute.googleapis.com/compute/v1/projects/my-project/global/networks/default
            priority: 65535
            selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/global/firewalls/default-deny-ingress
            sourceRanges:
            - 0.0.0.0/0
            """))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        self.GetFirewall())
    self.RunCompletion('compute firewall-rules describe d', [
        'default-deny-ingress',
        'default-allow-internal',
        'default-allow-egress',
    ])


class AlphaFirewallRulesDescribeTest(FirewallRulesDescribeTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def getEgressDenyFirewall(self):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')
    return self.messages.Firewall(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='tcp', ports=['1-65535']),
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='udp', ports=['1-65535']),
            self.messages.Firewall.DeniedValueListEntry(IPProtocol='icmp'),
        ],
        name='my-firewall',
        network=network_ref.SelfLink(),
        selfLink=(
            'https://compute.googleapis.com/compute/alpha/projects/my-project/'
            'global/firewalls/my-firewall'),
        destinationRanges=['1.2.3.4/32', '2.3.4.0/24'],
        direction=self.messages.Firewall.DirectionValueValuesEnum.EGRESS,
        targetServiceAccounts=['acct1@google.com', 'acct2@google.com'])

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[self.getEgressDenyFirewall()],])

    self.Run("""
        alpha compute firewall-rules describe my-firewall
        """)

    self.CheckRequests(
        [(self.compute_alpha.firewalls, 'Get',
          self.messages.ComputeFirewallsGetRequest(
              firewall='my-firewall', project='my-project'))],)
    self.assertMultiLineEqual(self.GetOutput(),
                              textwrap.dedent("""\
            denied:
            - IPProtocol: tcp
              ports:
              - 1-65535
            - IPProtocol: udp
              ports:
              - 1-65535
            - IPProtocol: icmp
            destinationRanges:
            - 1.2.3.4/32
            - 2.3.4.0/24
            direction: EGRESS
            name: my-firewall
            network: https://compute.googleapis.com/compute/alpha/projects/my-project/global/networks/default
            selfLink: https://compute.googleapis.com/compute/alpha/projects/my-project/global/firewalls/my-firewall
            targetServiceAccounts:
            - acct1@google.com
            - acct2@google.com
            """))

if __name__ == '__main__':
  test_case.main()
