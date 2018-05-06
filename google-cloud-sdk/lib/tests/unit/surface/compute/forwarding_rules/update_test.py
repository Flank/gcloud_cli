# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for forwarding rules update."""

import textwrap

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import (
    forwarding_rules_labels_test_base)
from tests.lib.surface.compute import (
    forwarding_rules_update_test_base)


class UpdateLabelsTestBeta(
    forwarding_rules_labels_test_base.ForwardingRulesLabelsTestBase):

  def testUpdateMissingNameOrLabels(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')
    with self.assertRaisesRegex(calliope_exceptions.RequiredArgumentException,
                                'At least one of --update-labels or '
                                '--remove-labels must be specified.'):
      self.Run('compute forwarding-rules update {0} --region {1}'
               .format(forwarding_rule_ref.Name(), forwarding_rule_ref.region))

  def testGlobalUpdateAndRemoveLabels(self):
    forwarding_rule_ref = self._GetForwardingRuleRef('fr-1')

    forwarding_rule_labels = (('key1', 'value1'), ('key2', 'value2'),
                              ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    forwarding_rule = self._MakeForwardingRuleProto(
        labels=forwarding_rule_labels, fingerprint='fingerprint-42')
    updated_forwarding_rule = self._MakeForwardingRuleProto(
        labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, forwarding_rule_ref)

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)
    self._ExpectLabelsSetRequest(forwarding_rule_ref, edited_labels,
                                 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(forwarding_rule_ref, updated_forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --update-labels {1} '
        '--remove-labels key1,key0'
        .format(forwarding_rule_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_forwarding_rule)

  def testGlobalClearLabels(self):
    forwarding_rule_ref = self._GetForwardingRuleRef('fr-1')

    forwarding_rule_labels = (('key1', 'value1'), ('key2', 'value2'),
                              ('key3', 'value3'))
    edited_labels = ()

    forwarding_rule = self._MakeForwardingRuleProto(
        labels=forwarding_rule_labels, fingerprint='fingerprint-42')
    updated_forwarding_rule = self._MakeForwardingRuleProto(
        labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, forwarding_rule_ref)

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)
    self._ExpectLabelsSetRequest(forwarding_rule_ref, edited_labels,
                                 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(forwarding_rule_ref, updated_forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --clear-labels'
        .format(forwarding_rule_ref.SelfLink()))
    self.assertEqual(response, updated_forwarding_rule)

  def testRegionUpdateAndRemoveLabels(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')

    forwarding_rule_labels = (('key1', 'value1'), ('key2', 'value2'),
                              ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    forwarding_rule = self._MakeForwardingRuleProto(
        labels=forwarding_rule_labels, fingerprint='fingerprint-42')
    updated_forwarding_rule = self._MakeForwardingRuleProto(
        labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, forwarding_rule_ref)

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)
    self._ExpectLabelsSetRequest(forwarding_rule_ref, edited_labels,
                                 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(forwarding_rule_ref, updated_forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --update-labels {1} '
        '--remove-labels key1,key0'
        .format(forwarding_rule_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_forwarding_rule)

  def testUpdateWithNoLabels(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    forwarding_rule = self._MakeForwardingRuleProto(
        labels=(), fingerprint='fingerprint-42')
    updated_forwarding_rule = self._MakeForwardingRuleProto(
        labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, forwarding_rule_ref)

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)
    self._ExpectLabelsSetRequest(forwarding_rule_ref, update_labels,
                                 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(forwarding_rule_ref, updated_forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --update-labels {1} '
        .format(forwarding_rule_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_forwarding_rule)

  def testRemoveWithNoLabelsOnForwardingRule(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')
    forwarding_rule = self._MakeForwardingRuleProto(
        labels={}, fingerprint='fingerprint-42')

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --remove-labels DoesNotExist'
        .format(forwarding_rule_ref.SelfLink()))
    self.assertEqual(response, forwarding_rule)

  def testNoNetUpdate(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')

    forwarding_rule_labels = (('key1', 'value1'), ('key2', 'value2'),
                              ('key3', 'value3'))
    update_labels = (('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    forwarding_rule = self._MakeForwardingRuleProto(
        labels=forwarding_rule_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)

    response = self.Run(
        'compute forwarding-rules update {0} --update-labels {1} '
        '--remove-labels key4'.format(forwarding_rule_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, forwarding_rule)

  def testScopePrompt(self):
    forwarding_rule_ref = self._GetForwardingRuleRef(
        'fr-1', region='us-central1')
    forwarding_rule = self._MakeForwardingRuleProto(labels=[])
    self._ExpectGetRequest(forwarding_rule_ref, forwarding_rule)

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2')
        ],)
    self.WriteInput('2\n')
    self.Run('compute forwarding-rules update fr-1 --remove-labels key0')
    self.AssertErrEquals(
        textwrap.dedent("""\
            For the following forwarding rule:
             - [fr-1]
            choose a region or global:
             [1] global
             [2] region: us-central1
             [3] region: us-central2
            Please enter your numeric choice:{0}
            """.format('  ')))


class ForwardingRuleUpdateWithNetworkTierAlphaTest(
    forwarding_rules_update_test_base.UpdateTestBase):

  def testGlobalUpdateToPremiumNetworkTier(self):
    self._SetNextGetResult(networkTier=self.select_network_tier)

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --global
        """)
    self._CheckPatchRequest(
        is_global=True, networkTier=self.premium_network_tier)

  def testGlobalUpdateToSelectNetworkTier(self):
    self._SetNextGetResult(networkTier=self.premium_network_tier)

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier select
          --global
        """)
    self._CheckPatchRequest(
        is_global=True, networkTier=self.select_network_tier)

  def testGlobalUpdateToInvalidNetworkTier(self):
    self._SetNextGetResult(networkTier=self.premium_network_tier)
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute forwarding-rules update forwarding-rule-1
            --network-tier INVALID-TIER
            --global
          """)

  def testGlobalUpdateNetworkTierAndLabel(self):
    self._SetNextGetResult(
        networkTier=self.select_network_tier, labelFingerprint='fingerprint-42')

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --update-labels=key1=value1
          --global
        """)
    self._CheckPatchAndSetLabelsRequest(
        is_global=True,
        label_fingerprint='fingerprint-42',
        labels=(('key1', 'value1'),),
        networkTier=self.premium_network_tier)

  def testRegionalUpdateToPremiumNetworkTier(self):
    self._SetNextGetResult(networkTier=self.select_network_tier)

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --region us-central2
        """)
    self._CheckPatchRequest(
        is_global=False, networkTier=self.premium_network_tier)

  def testRegionalUpdateToSelectNetworkTier(self):
    self._SetNextGetResult(networkTier=self.premium_network_tier)

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier select
          --region us-central2
        """)
    self._CheckPatchRequest(
        is_global=False, networkTier=self.select_network_tier)

  def testRegionalUpdateToInvalidNetworkTier(self):
    self._SetNextGetResult(networkTier=self.premium_network_tier)
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute forwarding-rules update forwarding-rule-1
            --network-tier invalid-tier
            --region us-central2
          """)

  def testRegionalUpdateNetworkTierAndLabel(self):
    self._SetNextGetResult(
        networkTier=self.select_network_tier, labelFingerprint='fingerprint-42')

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --update-labels=key1=value1
          --region us-central2
        """)
    self._CheckPatchAndSetLabelsRequest(
        is_global=False,
        label_fingerprint='fingerprint-42',
        labels=(('key1', 'value1'),),
        networkTier=self.premium_network_tier)

  def testUpdate_noChange(self):
    self._SetNextGetResult(networkTier=self.premium_network_tier)

    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be specified.'):
      self.Run("""
          compute forwarding-rules update forwarding-rule-1
            --region us-central2
          """)


if __name__ == '__main__':
  test_case.main()
