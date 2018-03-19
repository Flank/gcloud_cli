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
"""Tests for the firewall-rules delete subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class FirewallRulesDeleteTest(test_base.BaseTest,
                              completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def testWithSingleFirewall(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute firewall-rules delete firewall-1
        """)

    self.CheckRequests(
        [(self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-1',
              project='my-project'))],
    )

  def testWithManyFirewalls(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute firewall-rules delete firewall-1 firewall-2 firewall-3
        """)

    self.CheckRequests(
        [(self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-1',
              project='my-project')),

         (self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-2',
              project='my-project')),

         (self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute firewall-rules delete firewall-1 firewall-2 firewall-3
        """)

    self.CheckRequests(
        [(self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-1',
              project='my-project')),

         (self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-2',
              project='my-project')),

         (self.compute_v1.firewalls,
          'Delete',
          messages.ComputeFirewallsDeleteRequest(
              firewall='firewall-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute firewall-rules delete firewall-1 firewall-2 firewall-3
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        self.GetFirewall())
    self.RunCompletion('compute firewall-rules delete d',
                       ['default-allow-internal', 'default-allow-egress'])

  def GetFirewall(self):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')
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
    return [allow_internal, allow_egress]


if __name__ == '__main__':
  test_case.main()
