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
"""Tests for the resource policies create-snapshot-schedule command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class CreateGroupPlacementGaTest(resource_policies_base.TestBase,
                                 parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    pass

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeResourcePoliciesInsertRequest(
        project=self.Project(), region=self.region, resourcePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_spread(self):
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        groupPlacementPolicy=self.messages.ResourcePolicyGroupPlacementPolicy(
            availabilityDomainCount=2))

    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create group-placement pol1'
        ' --availability-domain-count 2 --region {}'
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_collocated(self):
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        groupPlacementPolicy=self.messages.ResourcePolicyGroupPlacementPolicy(
            vmCount=2,
            collocation=self.messages.ResourcePolicyGroupPlacementPolicy
            .CollocationValueValuesEnum.COLLOCATED))

    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create group-placement pol1 --vm-count 2'
        ' --collocation collocated --region {}'
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)


class CreateGroupPlacementBetaTest(CreateGroupPlacementGaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateGroupPlacementAlphaTest(CreateGroupPlacementBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
