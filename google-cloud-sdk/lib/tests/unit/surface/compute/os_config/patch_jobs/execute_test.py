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
"""Tests for google3.third_party.py.tests.unit.surface.compute.os_config.patch_jobs.execute."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute.os_config import test_base


class ExecuteTest(test_base.OsConfigBaseTest, waiter_test_base.Base):

  def _CreatePatchJob(self):
    return self.messages.PatchJob()

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SetUpMockApis(self.track)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testExecuteNoInstanceFilterFlag(self):
    with self.AssertRaisesArgumentError():
      self.Run("""compute os-config patch-jobs execute""")

    self.AssertErrContains('argument --instance-filter: Must be specified.')

  def testSyncExecuteWithEmptyInstanceFilter(self):
    expected_response = self.CreatePatchJob(
        'my-project',
        'my-patch-job',
        state=self.messages.PatchJob.StateValueValuesEnum.SUCCEEDED)
    self.mock_osconfig_client.projects_patchJobs.Execute.Expect(
        request=self.messages.OsconfigProjectsPatchJobsExecuteRequest(
            parent='projects/my-project',
            executePatchJobRequest=self.messages.ExecutePatchJobRequest(
                filter='id=*',
                dryRun=False,
                patchConfig=self.messages.PatchConfig())),
        response=expected_response)
    # Poller performs a Get.
    self.mock_osconfig_client.projects_patchJobs.Get.Expect(
        request=self.messages.OsconfigProjectsPatchJobsGetRequest(
            name='projects/my-project/patchJobs/my-patch-job'),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs execute --instance-filter=""
        """)

    self.assertEqual(expected_response, response)

  def testAsyncExecuteWithEmptyInstanceFilter(self):
    expected_response = self.CreatePatchJob('my-project', 'my-patch-job')
    self.mock_osconfig_client.projects_patchJobs.Execute.Expect(
        request=self.messages.OsconfigProjectsPatchJobsExecuteRequest(
            parent='projects/my-project',
            executePatchJobRequest=self.messages.ExecutePatchJobRequest(
                filter='id=*',
                dryRun=False,
                patchConfig=self.messages.PatchConfig())),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs execute --instance-filter="" --async
        """)

    self.assertEqual(expected_response, response)

  def testAsyncExecuteWithAllTopLevelFlags(self):
    expected_response = self.CreatePatchJob(
        'my-project',
        'my-patch-job',
        filter='name=instance-1',
        dry_run=True,
        description='test execute',
        duration='600s')
    self.mock_osconfig_client.projects_patchJobs.Execute.Expect(
        request=self.messages.OsconfigProjectsPatchJobsExecuteRequest(
            parent='projects/my-project',
            executePatchJobRequest=self.messages.ExecutePatchJobRequest(
                filter='name=instance-1',
                description='test execute',
                dryRun=True,
                duration='600s',
                patchConfig=self.messages.PatchConfig())),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs execute
        --instance-filter="name=instance-1"
        --description="test execute"
        --dry-run
        --duration="10m"
        --async
        """)

    self.assertEqual(expected_response, response)

  def testAsyncExecuteWithAllPatchConfigFlags(self):
    expected_patch_config = self.messages.PatchConfig(
        apt=self.messages.AptSettings(
            type=self.messages.AptSettings.TypeValueValuesEnum.DIST),
        rebootConfig=self.messages.PatchConfig.RebootConfigValueValuesEnum
        .ALWAYS,
        retryStrategy=self.messages.RetryStrategy(enabled=True),
        windowsUpdate=self.messages.WindowsUpdateSettings(
            classifications=[
                self.messages.WindowsUpdateSettings
                .ClassificationsValueListEntryValuesEnum.CRITICAL,
                self.messages.WindowsUpdateSettings
                .ClassificationsValueListEntryValuesEnum.FEATURE_PACK
            ],
            excludes=['KB123', 'KB456']),
        yum=self.messages.YumSettings(
            excludes=['789', '987'], minimal=True, security=True))
    expected_response = self.CreatePatchJob(
        'my-project', 'my-patch-job', patch_config=expected_patch_config)
    self.mock_osconfig_client.projects_patchJobs.Execute.Expect(
        request=self.messages.OsconfigProjectsPatchJobsExecuteRequest(
            parent='projects/my-project',
            executePatchJobRequest=self.messages.ExecutePatchJobRequest(
                filter='id=*', dryRun=False,
                patchConfig=expected_patch_config)),
        response=expected_response)

    response = self.Run("""
        compute os-config patch-jobs execute
        --instance-filter=""
        --apt-dist
        --reboot-config="ALWAYS"
        --retry
        --windows-classifications="critical,feature-pack"
        --windows-excludes KB123,KB456
        --yum-excludes="789,987"
        --yum-minimal
        --yum-security
        --async
        """)

    self.assertEqual(expected_response, response)


if __name__ == '__main__':
  test_case.main()
