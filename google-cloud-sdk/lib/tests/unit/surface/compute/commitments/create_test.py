# -*- coding: utf-8 -*- #
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
"""Tests for the commitments create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class CommitmentsCreateTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def MakeCommitment(self):
    return self.messages.Commitment(
        name='pledge',
        plan=self.messages.Commitment.PlanValueValuesEnum.TWELVE_MONTH,
        resources=[
            self.messages.ResourceCommitment(
                amount=500,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.VCPU),
            ),
            self.messages.ResourceCommitment(
                amount=12*1024,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.MEMORY),
            ),
        ],
    )

  def testSimpleInsert(self):
    self.make_requests.side_effect = iter([
        []
    ])

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources VCPU=500,MEMORY=12
        --region erech-stone
        """)

    self.CheckRequests(
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=self.MakeCommitment(),
              project='my-project',
              region='erech-stone',
          )
         )],
    )

  def testSimpleInsertWithQuotaError(self):
    def AppendQuotaError(requests, http, batch_url, errors):
      _ = requests, http, batch_url
      errors.append((
          403,
          'Quota \'COMMITMENTS\' exceeded. Limit: 5.0'))
      return []

    self.make_requests.side_effect = AppendQuotaError

    with self.AssertRaisesToolExceptionRegexp(
        r' - Quota \'COMMITMENTS\' exceeded. Limit: 5.0 You can request '
        r'commitments quota on https://cloud.google.com/compute/docs/'
        r'instances/signing-up-committed-use-discounts#quota'):
      self.Run("""
          compute commitments create pledge
          --plan 12-month
          --resources VCPU=500,MEMORY=12
          --region erech-stone
          """)

  def testSimpleInsertwithUnit(self):
    self.make_requests.side_effect = iter([
        []
    ])

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources VCPU=500,MEMORY=12288MB
        --region erech-stone
        """)

    self.CheckRequests(
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=self.MakeCommitment(),
              project='my-project',
              region='erech-stone',
          )
         )],
    )

  def testPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],
        []
    ])

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources VCPU=500,MEMORY=12
        """)

    self.CheckRequests(
        self.regions_list_request,
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=self.MakeCommitment(),
              project='my-project',
              region='region-1',
          )
         )],
    )

  def testRequireVcpu(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources MEMORY=12
        --region erech-stone
        """)

  def testRequireMemory(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources VCPU=12
        --region erech-stone
        """)

  def testValidatePlan(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
        compute commitments create pledge
        --plan 3.1536e25as
        --resources VCPU=12,MEMORY=3
        --region erech-stone
        """)


class CommitmentsCreateAlphaTest(CommitmentsCreateTest,
                                 parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def MakeCommitment(self):
    return self.messages.Commitment(
        name='pledge',
        plan=self.messages.Commitment.PlanValueValuesEnum.TWELVE_MONTH,
        resources=[
            self.messages.ResourceCommitment(
                amount=500,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.VCPU),
            ),
            self.messages.ResourceCommitment(
                amount=12*1024,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.MEMORY),
            ),
        ],
        type=self.messages.Commitment.TypeValueValuesEnum.GENERAL_PURPOSE
    )

  @parameterized.named_parameters(
      ('DefaultSpecified', '--type general-purpose', 'GENERAL_PURPOSE'),
      ('Default', '', 'GENERAL_PURPOSE'),
      ('MemoryOptimizedSpecified', '--type memory-optimized',
       'MEMORY_OPTIMIZED'))
  def testCreateWithTypeSpecified(self, flag_string, expected_type):
    self.make_requests.side_effect = iter([
        []
    ])

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources VCPU=500,MEMORY=12
        --region erech-stone
        {}
        """.format(flag_string))
    commitment = self.MakeCommitment()
    commitment.type = self.messages.Commitment.TypeValueValuesEnum(
        expected_type)
    self.CheckRequests(
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=commitment,
              project='my-project',
              region='erech-stone',
          )
         )],
    )

if __name__ == '__main__':
  test_case.main()
