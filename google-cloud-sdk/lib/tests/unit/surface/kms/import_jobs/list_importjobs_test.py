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
"""Tests that exercise the 'gcloud kms import-jobs list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.kms import base


class ImportJobsListTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testList(self):
    ij_1 = self.project_name.ImportJob('global/my_kr1/my_ij1')
    ij_2 = self.project_name.ImportJob('global/my_kr2/my_ij2')

    self.kms.projects_locations_keyRings_importJobs.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsListRequest(
            pageSize=100, parent=ij_1.Parent().RelativeName()),
        self.messages.ListImportJobsResponse(importJobs=[
            self.messages.ImportJob(
                name=ij_1.RelativeName(),
                state=self.messages.ImportJob.StateValueValuesEnum.ACTIVE,
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_3072_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM),
            self.messages.ImportJob(
                name=ij_2.RelativeName(),
                state=self.messages.ImportJob.StateValueValuesEnum.EXPIRED,
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_4096_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM)
        ]))

    self.Run('kms import-jobs list --location={0} --keyring {1}'.format(
        ij_1.location_id, ij_1.key_ring_id))
    self.AssertOutputContains(
        """NAME STATE IMPORT_METHOD PROTECTION_LEVEL LABELS
{0} ACTIVE RSA_OAEP_3072_SHA1_AES_256 HSM
{1} EXPIRED RSA_OAEP_4096_SHA1_AES_256 HSM
""".format(ij_1.RelativeName(), ij_2.RelativeName()),
        normalize_space=True)

  def testListParentFlag(self):
    ij_1 = self.project_name.ImportJob('global/my_kr/my_ij_1')

    ij = self.kms.projects_locations_keyRings_importJobs
    ij.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsImportJobsListRequest(
            pageSize=100, parent=ij_1.Parent().RelativeName()),
        self.messages.ListImportJobsResponse(importJobs=[
            self.messages.ImportJob(
                name=ij_1.RelativeName(),
                state=self.messages.ImportJob.StateValueValuesEnum.EXPIRED,
                importMethod=self.messages.ImportJob.ImportMethodValueValuesEnum
                .RSA_OAEP_4096_SHA1_AES_256,
                protectionLevel=self.messages.ImportJob
                .ProtectionLevelValueValuesEnum.HSM)
        ]))

    self.Run('kms import-jobs list --keyring {0}'.format(
        ij_1.Parent().RelativeName()))
    self.AssertOutputContains(
        """NAME STATE IMPORT_METHOD PROTECTION_LEVEL LABELS
{0} EXPIRED RSA_OAEP_4096_SHA1_AES_256 HSM
""".format(ij_1.RelativeName()),
        normalize_space=True)


class ImportJobsListTestBeta(ImportJobsListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ImportJobsListTestAlpha(ImportJobsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
