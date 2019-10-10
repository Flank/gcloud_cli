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
"""Tests for the commitments create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import commitments_test_base as test_base


class CommitmentsCreateTestGA(test_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSimpleInsert(self):
    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12
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
          --resources vcpu=500,memory=12
          --region erech-stone
          """)

  def testSimpleInsertWithUnit(self):
    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12288MB
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
        --resources vcpu=500,memory=12
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

  def testValidatePlan(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
        compute commitments create pledge
        --plan 3.1536e25as
        --resources vcpu=12,memory=3
        --region erech-stone
        """)

  def testCreateWithReservation(self):
    commitment = self.MakeCommitment(
        reservations=[self.MakeReservation('my-reservation')])

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12
        --region commitment-region
        --reservation my-reservation
        --reservation-zone=fake-zone
        --require-specific-reservation
        --vm-count 1
        --min-cpu-platform="Intel Haswell"
        --machine-type=n1-standard-1
        --accelerator count=1,type=nvidia-tesla-k80
        --local-ssd interface=scsi,size=375
        --local-ssd interface=nvme,size=375
        """)

    self.CheckRequests(
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=commitment,
              project='my-project',
              region='commitment-region',
          ))],)

  def testCreatWithReservationsFromFile(self):
    commitment = self.MakeCommitment(reservations=[
        self.MakeReservation('my-reservation'),
        self.MakeReservation('another-reservation'),
    ])
    reservations_file = self.Touch(
        self.temp_path,
        'reservations.yaml',
        contents="""\
-  reservation: my-reservation
   reservation_zone: fake-zone
   require_specific_reservation: true
   vm_count: 1
   machine_type: n1-standard-1
   min_cpu_platform: "Intel Haswell"
   accelerator:
   - count: 1
     type: nvidia-tesla-k80
   local_ssd:
   - interface: scsi
     size: 375
   - interface: nvme
     size: 375
-  reservation: another-reservation
   reservation_zone: fake-zone
   require_specific_reservation: true
   vm_count: 1
   machine_type: n1-standard-1
   min_cpu_platform: "Intel Haswell"
   accelerator:
   - count: 1
     type: nvidia-tesla-k80
   local_ssd:
   - interface: scsi
     size: 375
   - interface: nvme
     size: 375
""")

    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12
        --region commitment-region
        --reservations-from-file {}
        """.format(reservations_file))

    self.CheckRequests(
        [(self.compute.regionCommitments,
          'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=commitment,
              project='my-project',
              region='commitment-region',
          ))],)


class CommitmentsCreateTestBeta(CommitmentsCreateTestGA,
                                parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateWithLocalSsd(self):
    resources = [
        self.MakeVCPUResourceCommitment(),
        self.MakeMemoryResourceCommitment(),
        self.MakeLocalSsdResourceCommitment()
    ]
    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12,local-ssd=1
        --region erech-stone
        """)

    self.CheckRequests(
        [(self.compute.regionCommitments, 'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=self.MakeCommitment(resource_commitments=resources),
              project='my-project',
              region='erech-stone',
          ))])

  def testCreateWithAllResources(self):
    resources = [
        self.MakeVCPUResourceCommitment(),
        self.MakeMemoryResourceCommitment(),
        self.MakeLocalSsdResourceCommitment(),
        self.MakeAcceleratorResourceCommitment(),
    ]
    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12,local-ssd=1
        --resources-accelerator count=3,type=ace-type
        --region erech-stone
        """)

    self.CheckRequests(
        [(self.compute.regionCommitments, 'Insert',
          self.messages.ComputeRegionCommitmentsInsertRequest(
              commitment=self.MakeCommitment(resource_commitments=resources),
              project='my-project',
              region='erech-stone',
          ))])

  @parameterized.named_parameters(
      ('DefaultSpecified', '--type general-purpose', 'GENERAL_PURPOSE'),
      ('Default', '', 'GENERAL_PURPOSE'),
      ('MemoryOptimizedSpecified', '--type memory-optimized',
       'MEMORY_OPTIMIZED'))
  def testCreateWithTypeSpecified(self, flag_string, expected_type):
    self.Run("""
        compute commitments create pledge
        --plan 12-month
        --resources vcpu=500,memory=12
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


class CommitmentsCreateAlphaTest(CommitmentsCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
