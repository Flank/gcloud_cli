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
"""Tests for the firewall-rules list subcommand."""
import textwrap
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.firewall_rules import flags
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class FirewallRulesListTest(test_base.BaseTest,
                            completer_test_base.CompleterBase):

  def SetUp(self):
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.mock_get_global_resources = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(self.GetFirewall()))

  def testTableOutput(self):
    self.Run("""
        compute firewall-rules list
        """)

    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.firewalls,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertErrContains(flags.LIST_NOTICE)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME NETWORK DIRECTION PRIORITY ALLOW DENY
            default-deny-ingress default INGRESS 65535 all
            default-allow-internal default INGRESS 65534 tcp:1-65535,udp:1-65535,icmp
            default-allow-egress default EGRESS all
            """),
        normalize_space=True)

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

  def testTableOutputWithAllFields(self):
    self.Run("""
        compute firewall-rules list --format="{0}"
        """.format(flags.LIST_WITH_ALL_FIELDS_FORMAT))
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.firewalls,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME NETWORK DIRECTION PRIORITY SRC_RANGES DEST_RANGES ALLOW DENY SRC_TAGS SRC_SVC_ACCT TARGET_TAGS TARGET_SVC_ACCT
            default-deny-ingress default INGRESS 65535 0.0.0.0/0 all
            default-allow-internal default INGRESS 65534 10.0.0.0/8 tcp:1-65535,udp:1-65535,icmp tag-1,tag-2
            default-allow-egress default EGRESS 0.0.0.0/0 all tag-3,tag-4
            """),
        normalize_space=True)

  def testFirewallsCompleter(self):
    self.RunCompleter(
        flags.FirewallsCompleter,
        expected_command=[
            'compute',
            'firewall-rules',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'default-allow-egress',
            'default-allow-internal',
            'default-deny-ingress'
        ],
        cli=self.cli,
    )


class BetaFirewallRulesListTest(FirewallRulesListTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.mock_get_global_resources = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(self.GetFirewall()))


class AlphaFirewallRulesListTest(BetaFirewallRulesListTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.mock_get_global_resources = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            self.GetDisabledAndEnabledFirewall()))

  def GetDisabledAndEnabledFirewall(self):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')

    disabled_firewall_ref = self.resources.Create(
        'compute.firewalls', firewall='disabled-firewall', project='my-project')
    disabled_firewall = self.messages.Firewall(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='tcp', ports=['1000-2000']),
        ],
        name='disabled-firewall',
        network=network_ref.SelfLink(),
        selfLink=disabled_firewall_ref.SelfLink(),
        sourceRanges=['0.0.0.0/0'],
        priority=300,
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        disabled=True)

    enabled_firewall_ref = self.resources.Create(
        'compute.firewalls', firewall='enabled-firewall', project='my-project')
    enabled_firewall = self.messages.Firewall(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='udp', ports=['1000-2000']),
        ],
        name='enabled-firewall',
        network=network_ref.SelfLink(),
        selfLink=enabled_firewall_ref.SelfLink(),
        sourceRanges=['0.0.0.0/0'],
        priority=200,
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        disabled=False)

    return [disabled_firewall, enabled_firewall]

  def testTableOutput(self):
    self.Run("""
        compute firewall-rules list
        """)

    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.firewalls,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertErrContains(flags.LIST_NOTICE)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME NETWORK DIRECTION PRIORITY ALLOW DENY DISABLED
            disabled-firewall default INGRESS 300 tcp:1000-2000 True
            enabled-firewall default INGRESS 200 udp:1000-2000 False
            """),
        normalize_space=True)

  def testTableOutputWithAllFields(self):
    self.Run("""
        compute firewall-rules list --format="{0}"
        """.format(flags.LIST_WITH_ALL_FIELDS_FORMAT_ALPHA))
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.firewalls,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME NETWORK DIRECTION PRIORITY SRC_RANGES DEST_RANGES ALLOW DENY SRC_TAGS SRC_SVC_ACCT TARGET_TAGS TARGET_SVC_ACCT DISABLED
            disabled-firewall default INGRESS 300 0.0.0.0/0 tcp:1000-2000 True
            enabled-firewall default INGRESS 200 0.0.0.0/0 udp:1000-2000 False
            """),
        normalize_space=True)

  def testFirewallsCompleter(self):
    self.RunCompleter(
        flags.FirewallsCompleter,
        expected_command=[
            'compute',
            'firewall-rules',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'disabled-firewall',
            'enabled-firewall',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
