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
"""Tests that exercise the 'gcloud kms import-jobs create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.kms import maps
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


class ImportJobsCreateTestGA(base.KmsMockTest, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.import_job_name = self.project_name.ImportJob(
        'us-central1/my_kr/my_ij')

  @parameterized.parameters(('hsm', 'rsa-oaep-3072-sha1-aes-256'),
                            ('hsm', 'rsa-oaep-4096-sha1-aes-256'),
                            ('software', 'rsa-oaep-3072-sha1-aes-256'),
                            ('software', 'rsa-oaep-4096-sha1-aes-256'))
  def testCreateSuccess(self, protection_level, import_method):
    self.kms.projects_locations_keyRings_importJobs.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsCreateRequest(
            parent=self.import_job_name.Parent().RelativeName(),
            importJobId=self.import_job_name.import_job_id,
            importJob=self.messages.ImportJob(
                importMethod=maps.IMPORT_METHOD_MAPPER.GetEnumForChoice(
                    import_method),
                protectionLevel=maps.IMPORT_PROTECTION_LEVEL_MAPPER
                .GetEnumForChoice(protection_level))),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            importMethod=maps.IMPORT_METHOD_MAPPER.GetEnumForChoice(
                import_method),
            protectionLevel=maps.IMPORT_PROTECTION_LEVEL_MAPPER
            .GetEnumForChoice(protection_level)))

    self.Run(
        'kms import-jobs create '
        '--location={0} --keyring={1} {2} '
        '--import-method={3} --protection-level={4}'.format(
            self.import_job_name.location_id, self.import_job_name.key_ring_id,
            self.import_job_name.import_job_id, import_method,
            protection_level))

  def testCreateFullNameSuccess(self):

    self.kms.projects_locations_keyRings_importJobs.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsCreateRequest(
            parent=self.import_job_name.Parent().RelativeName(),
            importJobId=self.import_job_name.import_job_id,
            importJob=self.messages.ImportJob(
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_4096_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM)),
        self.messages.ImportJob(
            name=self.import_job_name.RelativeName(),
            importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
            .RSA_OAEP_4096_SHA1_AES_256,
            protectionLevel=self.messages.ImportJob
            .ProtectionLevelValueValuesEnum.HSM))

    self.Run('kms import-jobs create {} '
             '--import-method=rsa-oaep-4096-sha1-aes-256 --protection-level=hsm'
             .format(self.import_job_name.RelativeName()))

  def testCreateImportJobMissingProtectionLevel(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --protection-level: Must be specified'):
      self.Run('kms import-jobs create '
               '--location={0} --keyring={1} {2} '
               '--import-method=rsa-oaep-4096-sha1-aes-256'.format(
                   self.import_job_name.location_id,
                   self.import_job_name.key_ring_id,
                   self.import_job_name.import_job_id))

  def testCreateImportJobMissingImportMethod(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --import-method: Must be specified'):
      self.Run('kms import-jobs create '
               '--location={0} --keyring={1} {2} '
               '--protection-level=hsm'.format(
                   self.import_job_name.location_id,
                   self.import_job_name.key_ring_id,
                   self.import_job_name.import_job_id))

  def testCreateImportJobMissingImportJobId(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument IMPORT_JOB: Must be specified.'):
      self.Run(
          'kms import-jobs create '
          '--location={0} --keyring={1} '
          '--protection-level=hsm --import-method=rsa-oaep-4096-sha1-aes-256'
          .format(self.import_job_name.location_id,
                  self.import_job_name.key_ring_id))


class ImportJobsCreateTestBeta(ImportJobsCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ImportJobsCreateTestAlpha(ImportJobsCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
