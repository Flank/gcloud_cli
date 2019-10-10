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
"""Tests that exercise 'gcloud kms import-jobs describe'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base


class ImportJobsDescribeTestBeta(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.import_job_name = self.project_name.ImportJob(
        'us-central1/my_kr/my_ij/')

  def testDescribeHsmImportJobWithAttestation(self):
    attestation_file_path = self.Touch(self.temp_path)

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=self.import_job_name.RelativeName()),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.HSM,
            attestation=self.messages.KeyOperationAttestation(
                format=self.messages.KeyOperationAttestation
                .FormatValueValuesEnum.CAVIUM_V1_COMPRESSED,
                content=b'attestation content')))

    self.Run('kms import-jobs describe {0} --location={1} --keyring={2} '
             '--attestation-file={3}'.format(self.import_job_name.import_job_id,
                                             self.import_job_name.location_id,
                                             self.import_job_name.key_ring_id,
                                             attestation_file_path))

    self.AssertOutputContains(
        'name: {}'.format(self.import_job_name.Parent().RelativeName()),
        normalize_space=True)

    self.AssertOutputContains('format: CAVIUM_V1_COMPRESSED')
    # The attestation 'content' subfield should be omitted from the output,
    # since it's written to the file instead.
    self.AssertOutputNotContains('content:')

    self.AssertBinaryFileEquals(b'attestation content', attestation_file_path)

  def testDescribeHsmImportJobWithoutAttestationFlag(self):
    attestation_file_path = self.Touch(self.temp_path)

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=self.import_job_name.RelativeName()),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.HSM,
            attestation=self.messages.KeyOperationAttestation(
                format=self.messages.KeyOperationAttestation
                .FormatValueValuesEnum.CAVIUM_V1_COMPRESSED,
                content=b'attestation content')))

    self.Run('kms import-jobs describe {0} --location={1} --keyring={2}'.format(
        self.import_job_name.import_job_id, self.import_job_name.location_id,
        self.import_job_name.key_ring_id))

    self.AssertOutputContains(
        'name: {}'.format(self.import_job_name.Parent().RelativeName()),
        normalize_space=True)

    self.AssertOutputContains('format: CAVIUM_V1_COMPRESSED')
    # The attestation 'content' subfield should be omitted from the output.
    self.AssertOutputNotContains('content:')

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribeSoftwareImportJobWithAttestationThrowsException(self):
    attestation_file_path = self.Touch(self.temp_path)

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=self.import_job_name.RelativeName()),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.SOFTWARE))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'Attestations are only available for HSM import jobs.'):
      self.Run('kms import-jobs describe {0} --location={1} --keyring={2} '
               '--attestation-file={3}'.format(
                   self.import_job_name.import_job_id,
                   self.import_job_name.location_id,
                   self.import_job_name.key_ring_id, attestation_file_path))

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribePendingImportJobWithAttestationThrowsException(self):
    attestation_file_path = self.Touch(self.temp_path)

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=self.import_job_name.RelativeName()),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.HSM,
            state=self.messages.ImportJob.StateValueValuesEnum
            .PENDING_GENERATION))

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'The attestation is unavailable until the import job is generated.'):
      self.Run('kms import-jobs describe {0} --location={1} --keyring={2} '
               '--attestation-file={3}'.format(
                   self.import_job_name.import_job_id,
                   self.import_job_name.location_id,
                   self.import_job_name.key_ring_id, attestation_file_path))

    self.AssertBinaryFileEquals(b'', attestation_file_path)

  def testDescribeImportJobWithInvalidAttestationFile(self):
    attestation_file_path = os.path.join(self.temp_path, 'nested',
                                         'nonexistent', 'file')

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=self.import_job_name.RelativeName()),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.HSM,
            attestation=self.messages.KeyOperationAttestation(
                format=self.messages.KeyOperationAttestation
                .FormatValueValuesEnum.CAVIUM_V1_COMPRESSED,
                content=b'attestation content')))

    with self.AssertRaisesExceptionMatches(exceptions.BadFileException,
                                           attestation_file_path):
      self.Run('kms import-jobs describe {0} --location={1} --keyring={2} '
               '--attestation-file={3}'.format(
                   self.import_job_name.import_job_id,
                   self.import_job_name.location_id,
                   self.import_job_name.key_ring_id, attestation_file_path))


class ImportJobsDescribeTestAlpha(ImportJobsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
