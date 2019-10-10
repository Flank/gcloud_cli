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
"""Tests for the resource policies create-vm-maintenance command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class CreateVmMaintenanceAlphaTest(resource_policies_base.TestBase,
                                   parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.day_enum = (
        self.messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum)

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeResourcePoliciesInsertRequest(
        project=self.Project(),
        region=self.region,
        resourcePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_ConcurrencyLimitSet(self):
    request = self._ExpectCreate(self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            concurrencyControlGroup= \
              self.messages.ResourcePolicyVmMaintenancePolicyConcurrencyControl(
                  concurrencyLimit=10))))

    self.Run('compute resource-policies create vm-maintenance concurrency-limit'
             ' pol1  --max-percent=10 --region {}'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])

  def testCreate_ConcurrencyDefault(self):
    request = self._ExpectCreate(self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            concurrencyControlGroup= \
              self.messages.ResourcePolicyVmMaintenancePolicyConcurrencyControl(
                  concurrencyLimit=1))))

    self.Run('compute resource-policies create vm-maintenance concurrency-limit'
             ' pol1 --region {}'.format(self.region))
    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])

  def testCreate_ConcurrencyBoundaryValues(self):
    with self.AssertRaisesExceptionMatches(
        expected_message='--max-percent: Value must be less than or equal to '
                         '100',
        expected_exception=cli_test_base.MockArgumentError):
      self.Run('compute resource-policies create vm-maintenance '
               'concurrency-limit pol1 --max-percent=101 --region {} '
               .format(self.region))

    with self.AssertRaisesExceptionMatches(
        expected_message='--max-percent: Value must be greater than or equal '
                         'to 1',
        expected_exception=cli_test_base.MockArgumentError):
      self.Run('compute resource-policies create vm-maintenance '
               'concurrency-limit pol1 --max-percent=0 --region {} '
               .format(self.region))

if __name__ == '__main__':
  test_case.main()
