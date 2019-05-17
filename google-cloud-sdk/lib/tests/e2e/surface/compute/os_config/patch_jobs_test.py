# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Integration tests for managing a patch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute.os_config import test_base


class PatchJobsTestAlpha(test_base.OsConfigE2EBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self._instance_name = self.GetInstanceName(
        'compute-instances-os-config-patch-jobs')
    self.CreateInstance(self._instance_name)
    self._default_patch_job_filter = 'name=os-config-patch-jobs-no-match-name'

  def TearDown(self):
    self.DeleteInstance(self._instance_name)

  def CreatePatchJob(self, instance_filter):
    return self.Run('compute os-config patch-jobs execute --async'
                    ' --instance-filter="{0}"'
                    ' --no-user-output-enabled'.format(instance_filter))

  def testCancel(self):
    patch_job = self.CreatePatchJob('name={0}'.format(self._instance_name))
    patch_job_id = self.GetPatchJobId(patch_job.name)

    self.Run('compute os-config patch-jobs cancel {0}'.format(patch_job_id))

    self.AssertNewOutputContains('CANCELED')

  def testDescribe(self):
    patch_job = self.CreatePatchJob(self._default_patch_job_filter)
    patch_job_id = self.GetPatchJobId(patch_job.name)

    self.Run('compute os-config patch-jobs describe {0}'.format(patch_job_id))

    self.AssertNewOutputContainsAll([
        'instanceDetailsSummary', 'patchConfig', self._default_patch_job_filter,
        patch_job_id
    ])

  def testExecute(self):
    # Keep user output enabled for assertion.
    patch_job = self.Run('compute os-config patch-jobs execute --async'
                         ' --instance-filter={0}'.format(
                             self._default_patch_job_filter))

    self.AssertNewOutputContainsAll([
        'patchConfig', 'os-config-patch-jobs-no-match-name',
        self._default_patch_job_filter, patch_job.name
    ])

  def testListInstanceDetails(self):
    patch_job = self.CreatePatchJob(self._default_patch_job_filter)
    patch_job_id = self.GetPatchJobId(patch_job.name)

    patch_job = self.Run(
        'compute os-config patch-jobs list-instance-details {0}'.format(
            patch_job_id))

    # No instance details summary for the default patch job with 0 instance.
    self.AssertNewErrContains('Listed 0 items.')

  def testList(self):
    patch_job = self.CreatePatchJob(self._default_patch_job_filter)
    patch_job_id = self.GetPatchJobId(patch_job.name)

    self.Run('compute os-config patch-jobs list --limit 10')

    self.AssertNewOutputContainsAll(['NUM_INSTANCES', patch_job_id])


if __name__ == '__main__':
  test_base.main()
