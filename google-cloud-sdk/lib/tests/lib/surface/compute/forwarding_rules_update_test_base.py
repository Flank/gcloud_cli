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
"""Common component for forwarding rules update testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import test_base


class UpdateTestBase(test_base.BaseTest):
  """Base class for forwarding rules update test."""

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

    self.premium_network_tier = (
        self.messages.ForwardingRule.NetworkTierValueValuesEnum.PREMIUM)
    self.select_network_tier = (
        self.messages.ForwardingRule.NetworkTierValueValuesEnum.SELECT)

  def _SetNextGetResult(self, labels=None, label_fingerprint=None, **kwargs):
    forwarding_rule_resource = {'name': 'forwarding-rule-1'}
    forwarding_rule_resource.update(kwargs)
    msg = self.messages.ForwardingRule()

    if labels is not None:
      labels_value = msg.LabelsValue
      forwarding_rule_resource['labels'] = labels_value(additionalProperties=[
          labels_value.AdditionalProperty(key=pair[0], value=pair[1])
          for pair in labels
      ])

    if label_fingerprint:
      forwarding_rule_resource['labelFingerprint'] = label_fingerprint

    self.make_requests.side_effect = iter([
        [self.messages.ForwardingRule(**forwarding_rule_resource)],
        [],
    ])

  def _MakeGetRequest(self, is_global):
    if is_global:
      return (self.compute.globalForwardingRules, 'Get',
              self.messages.ComputeGlobalForwardingRulesGetRequest(
                  forwardingRule='forwarding-rule-1', project='my-project'))
    else:
      return (self.compute.forwardingRules, 'Get',
              self.messages.ComputeForwardingRulesGetRequest(
                  forwardingRule='forwarding-rule-1',
                  project='my-project',
                  region='us-central2'))

  def _MakePatchRequest(self, is_global, **kwargs):
    patch_map = {'name': 'forwarding-rule-1'}
    patch_map.update(kwargs)
    if is_global:
      return (self.compute.globalForwardingRules, 'Patch',
              self.messages.ComputeGlobalForwardingRulesPatchRequest(
                  forwardingRule='forwarding-rule-1',
                  forwardingRuleResource=self.messages.ForwardingRule(
                      **patch_map),
                  project='my-project'))
    else:
      return (self.compute.forwardingRules, 'Patch',
              self.messages.ComputeForwardingRulesPatchRequest(
                  forwardingRule='forwarding-rule-1',
                  forwardingRuleResource=self.messages.ForwardingRule(
                      **patch_map),
                  project='my-project',
                  region='us-central2'))

  def _MakeLabels(self, labels_value, labels):
    return labels_value(additionalProperties=[
        labels_value.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels
    ])

  def _MakeSetLabelsRequest(self, is_global, label_fingerprint, labels):
    if is_global:
      return (self.compute.globalForwardingRules, 'SetLabels',
              self.messages.ComputeGlobalForwardingRulesSetLabelsRequest(
                  resource='forwarding-rule-1',
                  globalSetLabelsRequest=self.messages.GlobalSetLabelsRequest(
                      labelFingerprint=label_fingerprint,
                      labels=self._MakeLabels(
                          self.messages.GlobalSetLabelsRequest.LabelsValue,
                          labels)),
                  project='my-project'))
    else:
      return (self.compute.forwardingRules, 'SetLabels',
              self.messages.ComputeForwardingRulesSetLabelsRequest(
                  resource='forwarding-rule-1',
                  regionSetLabelsRequest=self.messages.RegionSetLabelsRequest(
                      labelFingerprint=label_fingerprint,
                      labels=self._MakeLabels(
                          self.messages.RegionSetLabelsRequest.LabelsValue,
                          labels)),
                  project='my-project',
                  region='us-central2'))

  def _CheckPatchRequest(self, is_global, **kwargs):
    get_request = self._MakeGetRequest(is_global)

    if not kwargs:
      self.CheckRequests([get_request])
    else:
      patch_request = self._MakePatchRequest(is_global, **kwargs)
      self.CheckRequests([get_request], [patch_request])

  def _CheckSetLabelsRequest(self, is_global, label_fingerprint, labels,
                             **kwargs):
    get_request = self._MakeGetRequest(is_global)
    set_labels_request = self._MakeSetLabelsRequest(is_global,
                                                    label_fingerprint, labels)
    self.CheckRequests([get_request], [set_labels_request])

  def _CheckNoUpdateRequest(self, is_global):
    get_request = self._MakeGetRequest(is_global)

    self.CheckRequests([get_request], [])

  def _CheckPatchAndSetLabelsRequest(self, is_global, label_fingerprint, labels,
                                     **kwargs):
    get_request = self._MakeGetRequest(is_global)
    patch_request = self._MakePatchRequest(is_global, **kwargs)
    set_labels_request = self._MakeSetLabelsRequest(is_global,
                                                    label_fingerprint, labels)

    self.CheckRequests([get_request], [patch_request, set_labels_request])
