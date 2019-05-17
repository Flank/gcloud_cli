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
"""Tests for the firewall-rules update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class FirewallRulesUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')

  def SetNextGetResult(self, **kwargs):
    firewall_resource = {
        'name': 'firewall-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
    }
    firewall_resource.update(kwargs)
    self.make_requests.side_effect = iter([
        [self.messages.Firewall(**firewall_resource)],
        [],
    ])

  def AssertRaisesArgumentValidationExceptionRegexp(
      self, expected_regexp, callable_obj=None, *args, **kwargs):
    if callable_obj is None:
      return self.assertRaisesRegex(
          firewalls_utils.ArgumentValidationError, expected_regexp)

    return self.assertRaisesRegex(
        firewalls_utils.ArgumentValidationError, expected_regexp, callable_obj,
        *args, **kwargs)

  def CheckFirewallRequest(self, **kwargs):
    get_request = [(self.compute.firewalls, 'Get',
                    self.messages.ComputeFirewallsGetRequest(
                        firewall='firewall-1', project='my-project'))]
    if not kwargs:
      self.CheckRequests(get_request)
    else:
      update_map = {
          'name': 'firewall-1',
          'network': ('https://www.googleapis.com/compute/v1/projects/'
                      'my-project/global/networks/default'),
      }
      update_map.update(kwargs)
      update_request = [(self.compute.firewalls, 'Patch',
                         self.messages.ComputeFirewallsPatchRequest(
                             firewall='firewall-1',
                             firewallResource=self.messages.Firewall(
                                 **update_map),
                             project='my-project'))]

      self.CheckRequests(get_request, update_request)

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run("""
          compute firewall-rules update firewall-1
          """)
    self.CheckRequests()

  def testNoUpdate(self):
    self.SetNextGetResult(sourceTags=['src'])

    self.Run("""
        compute firewall-rules update firewall-1 --source-tags src
        """)
    self.CheckFirewallRequest()

  def testUriSupport(self):
    self.SetNextGetResult(sourceTags=['src'])

    self.Run("""
        compute firewall-rules update
          https://www.googleapis.com/compute/v1/projects/my-project/global/firewalls/firewall-1
          --source-tags src
        """)

    self.CheckFirewallRequest()

  def testAllowOption(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""\
        compute firewall-rules update firewall-1
        --allow tcp:80
        """)
    self.CheckFirewallRequest(
        allowed=[self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='tcp', ports=['80'])],
        sourceRanges=['0.0.0.0/0'])

  def testUnsetAllowOption(self):
    self.SetNextGetResult(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='some+protocol-name.', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow ''
        """)

    self.CheckFirewallRequest(sourceRanges=['0.0.0.0/0'])

  def BadSpecRaisesToolException(self, bad_spec):
    with self.AssertRaisesToolExceptionRegexp(
        r'Firewall rules must be of the form PROTOCOL\[:PORT\[-PORT\]\]; '
        r'received \[{0}\].'.format(bad_spec)):
      self.Run("""
          compute firewall-rules update firewall-1
            --allow {0} --source-tags src
          """.format(bad_spec))

  def testBadSpecRaisesToolException1(self):
    self.BadSpecRaisesToolException(':')

  def testBadSpecRaisesToolException2(self):
    self.BadSpecRaisesToolException('spec:1:2')

  def testBadSpecRaisesToolException3(self):
    self.BadSpecRaisesToolException('123:spec')

  def testBadSpecRaisesToolException4(self):
    self.BadSpecRaisesToolException('1:2-3-4')

  def testManySpecs(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123,tcp:80,udp:2000-3000,udp:123
          --source-tags src
        """)

    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[]),
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='tcp', ports=['80']),
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='udp', ports=['2000-3000']),
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='udp', ports=['123'])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src'])

  def testDescription(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --description funky
          --source-tags src
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        description='funky',
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src'])

  def testUnsetDescription(self):
    self.SetNextGetResult(description='funky', sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --description ''
          --source-tags src
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src'])

  def testSourceRanges(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-ranges 1.2.3.4/5,6.7.8.9/10
        """)

    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['1.2.3.4/5', '6.7.8.9/10'])

  def testUnsetSourceRanges(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-ranges ''
        """)
    self.CheckFirewallRequest(allowed=[
        self.messages.Firewall.AllowedValueListEntry(
            IPProtocol='123', ports=[])
    ])

  def testSourceTags(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-tags src-tag-1,src-tag-2,src-tag-3
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src-tag-1', 'src-tag-2', 'src-tag-3'])

  def testUnsetSourceTags(self):
    self.SetNextGetResult(
        sourceTags=['src-tag-1', 'src-tag-2', 'src-tag-3'],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-tags ''
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

  def testTargetTags(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-tags src
          --target-tags targ-tag-1,targ-tag-2,targ-tag-3
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src'],
        targetTags=['targ-tag-1', 'targ-tag-2', 'targ-tag-3'])

  def testUnsetTargetTags(self):
    self.SetNextGetResult(
        sourceRanges=['0.0.0.0/0'], targetTags=['targ-tag-1', 'targ-tag-2'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-tags src
          --target-tags ''
        """)

    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceTags=['src'])

  def testSetAllowOptionByRules(self):
    self.SetNextGetResult(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='some+protocol-name.', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --rules tcp:80
        """)

    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='tcp', ports=['80'])
        ],
        sourceRanges=['0.0.0.0/0'])

  def testUnsetAllowOptionByRules(self):
    self.SetNextGetResult(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='some+protocol-name.', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --rules ''
        """)
    self.CheckFirewallRequest(sourceRanges=['0.0.0.0/0'])

  def testDenyOption(self):
    self.SetNextGetResult(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='some+protocol-name.', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --rules tcp:80
        """)

    self.CheckFirewallRequest(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='tcp', ports=['80'])
        ],
        sourceRanges=['0.0.0.0/0'])

  def testUnsetDenyOption(self):
    self.SetNextGetResult(
        denied=[
            self.messages.Firewall.DeniedValueListEntry(
                IPProtocol='some+protocol-name.', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --rules ''
        """)
    self.CheckFirewallRequest(sourceRanges=['0.0.0.0/0'])

  def testPriorityZero(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'], priority=1000)

    self.Run("""
        compute firewall-rules update firewall-1
        --priority 0
        """)
    self.CheckFirewallRequest(destinationRanges=['0.0.0.0/0'], priority=0)

  def testPriorityNone(self):
    self.SetNextGetResult(destinationRanges=['1.0.0.0/8'], priority=1000)

    self.Run("""
        compute firewall-rules update firewall-1
        --destination-ranges 0.0.0.0/0
        """)
    self.CheckFirewallRequest(destinationRanges=['0.0.0.0/0'], priority=1000)

  def testPriority(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'], priority=1000)

    self.Run("""
        compute firewall-rules update firewall-1
        --priority 2000
        """)
    self.CheckFirewallRequest(destinationRanges=['0.0.0.0/0'], priority=2000)

  def testDestinationRanges(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --destination-ranges 1.2.3.4/32,2.3.4.0/24
        """)
    self.CheckFirewallRequest(destinationRanges=['1.2.3.4/32', '2.3.4.0/24'])

  def testUnsetDestinationRanges(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
        --destination-ranges ''
        """)
    self.CheckFirewallRequest(destinationRanges=[])

  def testWithBothAllowAndRules(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'])
    with self.AssertRaisesArgumentValidationExceptionRegexp(
        r'Can NOT specify --rules and --allow in the same request.'):
      self.Run("""
          compute firewall-rules update firewall-1
          --allow tcp:80
          --rules tcp:80
          """)

  def testSourceServiceAccounts(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-service-accounts src1@google.com,src2@google.com
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        sourceServiceAccounts=['src1@google.com', 'src2@google.com'])

  def testUnsetSourceServiceAccount(self):
    self.SetNextGetResult(
        sourceServiceAccounts=['src1@google.com', 'src2@google.com'],
        sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --source-service-accounts ''
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

  def testTargetServiceAccounts(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --target-service-accounts tgt1@google.com,tgt2@google.com
        """)
    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'],
        targetServiceAccounts=['tgt1@google.com', 'tgt2@google.com'])

  def testUnsetTargetServiceAccounts(self):
    self.SetNextGetResult(sourceRanges=['0.0.0.0/0'])

    self.Run("""
        compute firewall-rules update firewall-1
          --allow 123
          --target-service-accounts ''
        """)

    self.CheckFirewallRequest(
        allowed=[
            self.messages.Firewall.AllowedValueListEntry(
                IPProtocol='123', ports=[])
        ],
        sourceRanges=['0.0.0.0/0'])

  def testDisabled(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'], disabled=False)

    self.Run("""
        compute firewall-rules update firewall-1 --disabled
        """)
    self.CheckFirewallRequest(destinationRanges=['0.0.0.0/0'], disabled=True)

  def testEnabled(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'], disabled=True)

    self.Run("""
        compute firewall-rules update firewall-1 --no-disabled
        """)
    self.CheckFirewallRequest(destinationRanges=['0.0.0.0/0'], disabled=False)

  def testDisabledUnspecified(self):
    self.SetNextGetResult(destinationRanges=['0.0.0.0/0'], disabled=True)

    self.Run("""
        compute firewall-rules update firewall-1 --target-tags tgt
        """)
    # Request should not have disabled set.
    self.CheckFirewallRequest(
        destinationRanges=['0.0.0.0/0'], targetTags=['tgt'])

  def testEnableLogging(self):
    self.SetNextGetResult(
        destinationRanges=['0.0.0.0/0'],
        logConfig=self.messages.FirewallLogConfig(enable=False))

    self.Run("""
        compute firewall-rules update firewall-1 --enable-logging
        """)
    self.CheckFirewallRequest(
        destinationRanges=['0.0.0.0/0'],
        logConfig=self.messages.FirewallLogConfig(enable=True))


class BetaFirewallRulesUpdateTest(FirewallRulesUpdateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def SetNextGetResult(self, **kwargs):
    firewall_resource = {
        'name':
            'firewall-1',
        'network': ('https://www.googleapis.com/compute/beta/projects/'
                    'my-project/global/networks/default'),
    }
    firewall_resource.update(kwargs)
    self.make_requests.side_effect = iter([
        [self.messages.Firewall(**firewall_resource)],
        [],
    ])

  def CheckFirewallRequest(self, **kwargs):
    get_request = [(self.compute.firewalls, 'Get',
                    self.messages.ComputeFirewallsGetRequest(
                        firewall='firewall-1', project='my-project'))]
    if not kwargs:
      self.CheckRequests(get_request)
    else:
      update_map = {
          'name':
              'firewall-1',
          'network': ('https://www.googleapis.com/compute/beta/projects/'
                      'my-project/global/networks/default'),
      }
      update_map.update(kwargs)
      update_request = [(self.compute.firewalls, 'Patch',
                         self.messages.ComputeFirewallsPatchRequest(
                             firewall='firewall-1',
                             firewallResource=self.messages.Firewall(
                                 **update_map),
                             project='my-project'))]

      self.CheckRequests(get_request, update_request)


class AlphaFirewallRulesUpdateTest(BetaFirewallRulesUpdateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetNextGetResult(self, **kwargs):
    firewall_resource = {
        'name':
            'firewall-1',
        'network': ('https://www.googleapis.com/compute/alpha/projects/'
                    'my-project/global/networks/default'),
    }
    firewall_resource.update(kwargs)
    self.make_requests.side_effect = iter([
        [self.messages.Firewall(**firewall_resource)],
        [],
    ])

  def CheckFirewallRequest(self, **kwargs):
    get_request = [(self.compute.firewalls, 'Get',
                    self.messages.ComputeFirewallsGetRequest(
                        firewall='firewall-1', project='my-project'))]
    if not kwargs:
      self.CheckRequests(get_request)
    else:
      update_map = {
          'name':
              'firewall-1',
          'network': ('https://www.googleapis.com/compute/alpha/projects/'
                      'my-project/global/networks/default'),
      }
      update_map.update(kwargs)
      update_request = [(self.compute.firewalls, 'Patch',
                         self.messages.ComputeFirewallsPatchRequest(
                             firewall='firewall-1',
                             firewallResource=self.messages.Firewall(
                                 **update_map),
                             project='my-project'))]

      self.CheckRequests(get_request, update_request)

  def testToggleLoggingMetadata(self):
    self.SetNextGetResult(
        destinationRanges=['0.0.0.0/0'],
        logConfig=self.messages.FirewallLogConfig(enable=True))

    self.Run("""
        compute firewall-rules update firewall-1
          --logging-metadata include-all
        """)
    self.CheckFirewallRequest(
        destinationRanges=['0.0.0.0/0'],
        logConfig=self.messages.FirewallLogConfig(
            enable=True,
            metadata=self.messages.FirewallLogConfig.MetadataValueValuesEnum(
                'INCLUDE_ALL_METADATA')))

  def testToggleLoggingMetadataLoggingDisabled(self):
    self.SetNextGetResult(
        destinationRanges=['0.0.0.0/0'],
        logConfig=self.messages.FirewallLogConfig(enable=False))

    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--logging-metadata\\]: cannot toggle logging'
        ' metadata if logging is not enabled.', self.Run,
        'compute firewall-rules update firewall-1'
        ' --logging-metadata include-all')


if __name__ == '__main__':
  test_case.main()
