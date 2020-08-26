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
"""Tests for the firewall-rules create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class FirewallRulesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.api_version = 'v1'
    self.SelectApi(self.api_version)
    self.StartObjectPatch(progress_tracker, 'ProgressTracker')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def CheckFirewallRequest(self, **kwargs):
    network_ref = self.resources.Create(
        'compute.networks', network='default', project='my-project')
    firewall_msg = {
        'network': network_ref.SelfLink(),
        'direction': self.messages.Firewall.DirectionValueValuesEnum.INGRESS
    }
    firewall_msg.update(kwargs)
    self.CheckRequests([(self.compute.firewalls, 'Insert',
                         self.messages.ComputeFirewallsInsertRequest(
                             firewall=self.messages.Firewall(**firewall_msg),
                             project='my-project'))])

  def AssertRaisesArgumentValidationExceptionRegexp(self,  # pylint:disable=keyword-arg-before-vararg
                                                    expected_regexp,
                                                    callable_obj=None,
                                                    *args,
                                                    **kwargs):
    if callable_obj is None:
      return self.assertRaisesRegex(firewalls_utils.ArgumentValidationError,
                                    expected_regexp)

    return self.assertRaisesRegex(firewalls_utils.ArgumentValidationError,
                                  expected_regexp, callable_obj, *args,
                                  **kwargs)

  def testDefaultOptions(self):
    self.make_requests.side_effect = [[
        self.messages.Firewall(
            name='firewall-1',
            network='default',
            direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
            priority=65534,
            allowed=[
                self.messages.Firewall.AllowedValueListEntry(
                    IPProtocol='tcp', ports=['80'])
            ],
            denied=[
                self.messages.Firewall.DeniedValueListEntry(IPProtocol='all')
            ],
            disabled=False)
    ]]

    self.Run("""
        compute firewall-rules create firewall-1
          --allow tcp:80
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='tcp', ports=['80'])
        ],
        name='firewall-1')

    self.AssertOutputEquals(
        """\
      NAME        NETWORK  DIRECTION  PRIORITY  ALLOW   DENY  DISABLED
      firewall-1  default  INGRESS    65534     tcp:80  all   False
      """,
        normalize_space=True)

  def BadSpecRaisesToolException(self, bad_spec):
    with self.AssertRaisesToolExceptionRegexp(
        r'Firewall rules must be of the form PROTOCOL\[:PORT\[-PORT\]\]; '
        r'received \[{0}\].'.format(bad_spec)):
      self.Run("""
          compute firewall-rules create firewall-1
            --allow {0} --source-tags src
          """.format(bad_spec))

    self.CheckRequests()

  def testBadSpecRaisesToolException1(self):
    self.BadSpecRaisesToolException(':')

  def testBadSpecRaisesToolException2(self):
    self.BadSpecRaisesToolException('spec:1:2')

  def testBadSpecRaisesToolException3(self):
    self.BadSpecRaisesToolException('123:spec')

  def testBadSpecRaisesToolException4(self):
    self.BadSpecRaisesToolException('1:2-3-4')

  def testManySpecs(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123,tcp:80,udp:2000-3000,udp:123
          --source-tags src
        """)
    allow_rules = []
    allow_rules.append(
        self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='123', ports=[]))
    allow_rules.append(
        self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='tcp', ports=['80']))
    allow_rules.append(
        self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='udp', ports=['2000-3000']))
    allow_rules.append(
        self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='udp', ports=['123']))
    self.CheckFirewallRequest(
        allowed=allow_rules, name='firewall-1', sourceTags=['src'])

  def testDescription(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --description funky
          --source-tags src
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        description='funky',
        sourceTags=['src'])

  def testNetwork(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --network my-network
          --source-tags src
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        network=('https://compute.googleapis.com/compute/' + self.api_version +
                 '/projects/my-project/global/networks/my-network'),
        sourceTags=['src'])

  def testUriSupport(self):
    self.Run("""
        compute firewall-rules create
          https://compute.googleapis.com/compute/v1/projects/my-project/global/firewalls/firewall-1
          --allow 123
          --network https://compute.googleapis.com/compute/v1/projects/my-project/global/networks/my-network
          --source-tags src
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        network=('https://compute.googleapis.com/compute/v1/projects/'
                 'my-project/global/networks/my-network'),
        sourceTags=['src'])

  def testSourceRanges(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --source-ranges 1.2.3.4/5,6.7.8.9/10
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        sourceRanges=['1.2.3.4/5', '6.7.8.9/10'])

  def testSourceTags(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --source-tags src-tag-1,src-tag-2,src-tag-3
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        sourceTags=['src-tag-1', 'src-tag-2', 'src-tag-3'])

  def testTargetTags(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --source-tags src
          --target-tags targ-tag-1,targ-tag-2,targ-tag-3
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        sourceTags=['src'],
        targetTags=['targ-tag-1', 'targ-tag-2', 'targ-tag-3'])

  def testAllowIsRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--action | --allow) must be specified.'):
      self.Run("""
          compute firewall-rules create firewall-1 --rules tcp:80
          """)

    self.CheckRequests()

  def testWithBothAllowAndAction(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --action: Exactly one of (--action | --allow) must be '
        'specified.'):
      self.Run("""
          compute firewall-rules create firewall-1
          --allow tcp:80
          --action allow
          """)

    self.CheckRequests()

  def testWithBothAllowAndRules(self):
    with self.AssertRaisesArgumentValidationExceptionRegexp(
        r'Can NOT specify --rules and --allow in the same request.'):
      self.Run("""
          compute firewall-rules create firewall-1
          --allow tcp:80
          --rules tcp:80
          """)

    self.CheckRequests()

  def testActionWithNoRules(self):
    with self.AssertRaisesArgumentValidationExceptionRegexp(
        r'Must specify --rules with --action'):
      self.Run("""
          compute firewall-rules create firewall-1
          --action deny
          """)

    self.CheckRequests()

  def testDirectionWithIn(self):
    direction_enum = self.messages.Firewall.DirectionValueValuesEnum
    self.Run("""
      compute firewall-rules create firewall-1
      --action deny --rules all --direction in""")
    self.verifyDirection(direction_enum.INGRESS)

  def testDirectionWithIngress(self):
    direction_enum = self.messages.Firewall.DirectionValueValuesEnum
    self.Run("""
      compute firewall-rules create firewall-1
      --action deny --rules all --direction Ingress""")
    self.verifyDirection(direction_enum.INGRESS)

  def testDirectionWithOut(self):
    direction_enum = self.messages.Firewall.DirectionValueValuesEnum
    self.Run("""compute firewall-rules create firewall-1
      --action deny --rules all --direction OUt""")
    self.verifyDirection(direction_enum.EGRESS)

  def testDirectionWithEgress(self):
    direction_enum = self.messages.Firewall.DirectionValueValuesEnum
    self.Run("""compute firewall-rules create firewall-1
      --action deny --rules all --direction egress""")
    self.verifyDirection(direction_enum.EGRESS)

  def verifyDirection(self, expected_direction):
    self.CheckFirewallRequest(
        denied=[self.messages.Firewall.DeniedValueListEntry(IPProtocol='all')],
        name='firewall-1',
        sourceRanges=[],
        destinationRanges=[],
        direction=expected_direction)

  def testManySpecsForDeny(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --action deny
          --rules 123,tcp:80,udp:2000-3000,udp:123
          --source-tags src
        """)
    deny_rules = []
    deny_rules.append(
        self.messages.Firewall.DeniedValueListEntry(IPProtocol='123', ports=[]))
    deny_rules.append(
        self.messages.Firewall.DeniedValueListEntry(
            IPProtocol='tcp', ports=['80']))
    deny_rules.append(
        self.messages.Firewall.DeniedValueListEntry(
            IPProtocol='udp', ports=['2000-3000']))
    deny_rules.append(
        self.messages.Firewall.DeniedValueListEntry(
            IPProtocol='udp', ports=['123']))

    self.CheckFirewallRequest(
        denied=deny_rules,
        name='firewall-1',
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        sourceTags=['src'])

  def testDestinationRanges(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --direction egress
          --allow 123
          --destination-ranges 1.2.3.4/5,6.7.8.9/10
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        direction=self.messages.Firewall.DirectionValueValuesEnum.EGRESS,
        destinationRanges=['1.2.3.4/5', '6.7.8.9/10'])

  def testPriority(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --priority 65534
          --action allow
          --rules 123
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='123')
        ],
        name='firewall-1',
        priority=65534,
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        sourceRanges=[])

  def testSourceServiceAccounts(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --source-service-accounts src_acct1@google.com,src_acct2@google.com
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        sourceServiceAccounts=['src_acct1@google.com', 'src_acct2@google.com'])

  def testTargetServiceAccounts(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --allow 123
          --target-service-accounts tgt_acct1@google.com,tgt_acct2@google.com
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        name='firewall-1',
        targetServiceAccounts=['tgt_acct1@google.com', 'tgt_acct2@google.com'])

  def testDisabled(self):
    self.Run("""
        compute firewall-rules create firewall-1
             --action allow
             --rules 123
             --disabled
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='123')
        ],
        name='firewall-1',
        disabled=True,
        sourceRanges=[])

  def testEnableLogging(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --action allow
          --rules 123
          --enable-logging
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='123')
        ],
        name='firewall-1',
        logConfig=self.messages.FirewallLogConfig(enable=True),
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        sourceRanges=[])

  def testToggleLoggingMetadata(self):
    self.Run("""
        compute firewall-rules create firewall-1
          --action allow
          --rules 123
          --enable-logging
          --logging-metadata exclude-all
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(IPProtocol='123')
        ],
        name='firewall-1',
        logConfig=self.messages.FirewallLogConfig(
            enable=True,
            metadata=self.messages.FirewallLogConfig.MetadataValueValuesEnum(
                'EXCLUDE_ALL_METADATA')),
        direction=self.messages.Firewall.DirectionValueValuesEnum.INGRESS,
        sourceRanges=[])

  def testToggleLoggingMetadataLoggingDisabled(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--logging-metadata\\]: cannot toggle logging'
        ' metadata if logging is not enabled.', self.Run,
        'compute firewall-rules create firewall-1'
        ' --action allow'
        ' --rules 123'
        ' --logging-metadata exclude-all')


class BetaFirewallRulesCreateTest(FirewallRulesCreateTest):

  def SetUp(self):
    self.api_version = 'beta'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.BETA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')


class AlphaFirewallRulesCreateTest(BetaFirewallRulesCreateTest):

  def SetUp(self):
    self.api_version = 'alpha'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')


if __name__ == '__main__':
  test_case.main()
