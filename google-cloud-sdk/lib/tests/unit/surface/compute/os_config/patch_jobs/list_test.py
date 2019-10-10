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
"""Tests for google3.third_party.py.tests.unit.surface.compute.os_config.patch_jobs.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.os_config import test_base


# TODO(b/140685325): convert to scenario test
class ListTest(test_base.OsConfigBaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SetUpMockApis(self.track)
    self.patch_jobs = [
        self.messages.PatchJob(
            name='projects/my-project/patchJobs/my-patch-job-1',
            filter='name=instance-1',
            description='Patch instance-1',
            state=self.messages.PatchJob.StateValueValuesEnum.SUCCEEDED),
        self.messages.PatchJob(
            name='projects/my-project/patchJobs/my-patch-job-2',
            filter='id=*',
            description='Patch all',
            state=self.messages.PatchJob.StateValueValuesEnum
            .COMPLETED_WITH_ERRORS)
    ]

  def testListSuccess(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""compute os-config patch-jobs list""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION      CREATE_TIME STATE                 NUM_INSTANCES
            my-patch-job-1 Patch instance-1             SUCCEEDED
            my-patch-job-2 Patch all                    COMPLETED_WITH_ERRORS
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithDefaultLimit(self):
    input_patch_jobs = [
        self.messages.PatchJob(
            name='projects/my-project/patchJobs/my-patch-job-{}'.format(i),
            filter='id=*') for i in range(0, 15)
    ]

    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(
            patchJobs=input_patch_jobs))

    self.Run("""compute os-config patch-jobs list""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION CREATE_TIME STATE NUM_INSTANCES
            my-patch-job-0
            my-patch-job-1
            my-patch-job-2
            my-patch-job-3
            my-patch-job-4
            my-patch-job-5
            my-patch-job-6
            my-patch-job-7
            my-patch-job-8
            my-patch-job-9
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithLimit(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""compute os-config patch-jobs list --limit 1""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION      CREATE_TIME STATE     NUM_INSTANCES
            my-patch-job-1 Patch instance-1             SUCCEEDED
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithPageSize(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            pageSize=1, parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""compute os-config patch-jobs list --page-size 1""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION      CREATE_TIME STATE     NUM_INSTANCES
            my-patch-job-1 Patch instance-1             SUCCEEDED
            NAME           DESCRIPTION CREATE_TIME STATE                 NUM_INSTANCES
            my-patch-job-2 Patch all               COMPLETED_WITH_ERRORS
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithSortBy(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""
        compute os-config patch-jobs list
        --sort-by="~name" """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION      CREATE_TIME STATE                 NUM_INSTANCES
            my-patch-job-2 Patch all                    COMPLETED_WITH_ERRORS
            my-patch-job-1 Patch instance-1             SUCCEEDED
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithFilter(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""
        compute os-config patch-jobs list
        --filter="state=SUCCEEDED" """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           DESCRIPTION      CREATE_TIME STATE     NUM_INSTANCES
            my-patch-job-1 Patch instance-1             SUCCEEDED
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListWithUri(self):
    self.mock_osconfig_client.projects_patchJobs.List.Expect(
        request=self.messages.OsconfigProjectsPatchJobsListRequest(
            parent='projects/my-project'),
        response=self.messages.ListPatchJobsResponse(patchJobs=self.patch_jobs))

    self.Run("""compute os-config patch-jobs list --uri""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://osconfig.googleapis.com/v1alpha2/projects/my-project/patchJobs/my-patch-job-1
            https://osconfig.googleapis.com/v1alpha2/projects/my-project/patchJobs/my-patch-job-2
            """),
        normalize_space=True)
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
