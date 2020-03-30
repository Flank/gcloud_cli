# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import (
    forwarding_rules_update_test_base)


class UpdateLabelsTestBeta(forwarding_rules_update_test_base.UpdateTestBase):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testUpdateMissingNameOrLabels(self):
    self._SetNextGetResult()
    with self.assertRaisesRegex(calliope_exceptions.ToolException,
                                'At least one property must be specified.'):
      self.Run('compute forwarding-rules update forwarding-rule-1 '
               '--region us-central2')

  def testGlobalUpdateAndRemoveLabels(self):
    self._SetNextGetResult(
        labels=(('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')),
        label_fingerprint=b'fingerprint-42',
    )

    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    merged_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    self.Run('compute forwarding-rules update forwarding-rule-1 --global '
             '--update-labels {0} --remove-labels key1,key0'.format(','.join([
                 '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels
             ])))
    self._CheckSetLabelsRequest(
        is_global=True,
        label_fingerprint=b'fingerprint-42',
        labels=merged_labels)

  def testGlobalClearLabels(self):
    self._SetNextGetResult(
        labels=(('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')),
        label_fingerprint=b'fingerprint-42')

    self.Run('compute forwarding-rules update forwarding-rule-1 --global '
             '--clear-labels')
    self._CheckSetLabelsRequest(
        is_global=True, label_fingerprint=b'fingerprint-42', labels=())

  def testRegionUpdateAndRemoveLabels(self):
    self._SetNextGetResult(
        labels=(('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')),
        label_fingerprint=b'fingerprint-42',
    )

    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    merged_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    self.Run(
        'compute forwarding-rules update forwarding-rule-1 --region us-central2'
        ' --update-labels {0} --remove-labels key1,key0'.format(','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self._CheckSetLabelsRequest(
        is_global=False,
        label_fingerprint=b'fingerprint-42',
        labels=merged_labels)

  def testUpdateWithNoLabels(self):
    self._SetNextGetResult(label_fingerprint=b'fingerprint-42',)

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    self.Run('compute forwarding-rules update forwarding-rule-1 --global '
             '--update-labels {0}'.format(','.join([
                 '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels
             ])))
    self._CheckSetLabelsRequest(
        is_global=True,
        label_fingerprint=b'fingerprint-42',
        labels=update_labels)

  def testRemoveWithNoLabelsOnForwardingRule(self):
    self._SetNextGetResult(label_fingerprint=b'fingerprint-42',)

    self.Run('compute forwarding-rules update forwarding-rule-1 --global '
             '--remove-labels DoesNotExist')
    self._CheckNoUpdateRequest(is_global=True)

  def testNoNetUpdate(self):
    self._SetNextGetResult(
        labels=(('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')),
        label_fingerprint=b'fingerprint-42',
    )
    update_labels = (('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))
    self.Run('compute forwarding-rules update forwarding-rule-1 --global '
             '--update-labels {0} --remove-labels key4'.format(','.join([
                 '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels
             ])))
    self._CheckNoUpdateRequest(is_global=True)

  def testScopePrompt(self):
    self._SetNextGetResult(label_fingerprint=b'fingerprint-42',)

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2')
        ],)
    self.WriteInput('2\n')
    self.Run('compute forwarding-rules update forwarding-rule-1 '
             '--remove-labels key0')
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["global", "region: us-central1", "region: us-central2"]')


class UpdateLabelsTestAlpha(UpdateLabelsTestBeta):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


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
        networkTier=self.select_network_tier,
        labelFingerprint=b'fingerprint-42')

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --update-labels=key1=value1
          --global
        """)
    self._CheckPatchAndSetLabelsRequest(
        is_global=True,
        label_fingerprint=b'fingerprint-42',
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
        networkTier=self.select_network_tier,
        labelFingerprint=b'fingerprint-42')

    self.Run("""
        compute forwarding-rules update forwarding-rule-1
          --network-tier premium
          --update-labels=key1=value1
          --region us-central2
        """)
    self._CheckPatchAndSetLabelsRequest(
        is_global=False,
        label_fingerprint=b'fingerprint-42',
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


class ForwardingRuleUpdateWithGlobalAccessGATest(
    forwarding_rules_update_test_base.UpdateTestBase):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testUpdateRegionWithGlobalAccess(self):
    self._SetNextGetResult(allowGlobalAccess=None)

    self.Run('compute forwarding-rules update forwarding-rule-1 '
             '--allow-global-access --region us-central2')

    self._CheckPatchRequest(is_global=False, allowGlobalAccess=True)

  def testUpdateGloalBackToRegionAccess(self):
    self._SetNextGetResult(allowGlobalAccess=True)

    self.Run('compute forwarding-rules update forwarding-rule-1 '
             '--no-allow-global-access --region us-central2')

    self._CheckPatchRequest(is_global=False, allowGlobalAccess=False)


class ForwardingRuleUpdateWithGlobalAccessBetaTest(
    ForwardingRuleUpdateWithGlobalAccessGATest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA


class ForwardingRuleUpdateWithGlobalAccessAlphaTest(
    ForwardingRuleUpdateWithGlobalAccessBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
