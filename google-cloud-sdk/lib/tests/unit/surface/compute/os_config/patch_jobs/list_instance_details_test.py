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
"""Tests for google3.third_party.py.tests.unit.surface.compute.os_config.patch_jobs.list_instance_details."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.os_config import test_base


# TODO(b/140685325): convert to scenario test
class ListInstanceDetailsTestAlpha(test_base.OsConfigBaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SetUpMockApis(self.track)
    self.instance_details = [
        self.messages.PatchJobInstanceDetails(
            name='projects/my-project/zones/zone-1/instances/instance-1',
            state=self.messages.PatchJobInstanceDetails.StateValueValuesEnum
            .SUCCEEDED),
        self.messages.PatchJobInstanceDetails(
            name='projects/my-project/zones/zone-2/instances/instance-2',
            state=self.messages.PatchJobInstanceDetails.StateValueValuesEnum
            .FAILED,
            failureReason='Encountered Exception')
    ]

  def testListInstanceDetailsNoPatchJobArg(self):
    with self.AssertRaisesArgumentError():
      self.Run("""compute os-config patch-jobs list-instance-details""")

    self.AssertErrContains('argument PATCH_JOB: Must be specified.')

  def testListInstanceDetailsWithUri(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        --uri
        """)

    self.AssertErrContains('unrecognized arguments: --uri')

  def testListInstanceDetailsWithPatchJobName(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   STATE     FAILURE_REASON
            instance-1 zone-1 SUCCEEDED
            instance-2 zone-2 FAILED    Encountered Exception
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithRelativePatchJobPath(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details
        projects/my-project/patchJobs/my-patch-job
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   STATE     FAILURE_REASON
            instance-1 zone-1 SUCCEEDED
            instance-2 zone-2 FAILED    Encountered Exception
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithPatchJobUri(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details
        https://osconfig.googleapis.com/v1alpha2/projects/my-project/patchJobs/my-patch-job
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   STATE     FAILURE_REASON
            instance-1 zone-1 SUCCEEDED
            instance-2 zone-2 FAILED    Encountered Exception
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithLimit(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        --limit 1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
                NAME       ZONE   STATE     FAILURE_REASON
                instance-1 zone-1 SUCCEEDED
                """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithPageSize(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            pageSize=1, parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        --page-size 1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   STATE     FAILURE_REASON
            instance-1 zone-1 SUCCEEDED

            NAME       ZONE   STATE  FAILURE_REASON
            instance-2 zone-2 FAILED Encountered Exception
            """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithSortBy(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        --sort-by="~name"
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   STATE     FAILURE_REASON
            instance-2 zone-2 FAILED    Encountered Exception
            instance-1 zone-1 SUCCEEDED
                """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testListInstanceDetailsWithFilter(self):
    self.mock_osconfig_client.projects_patchJobs_instanceDetails.List.Expect(
        request=self.messages
        .OsconfigProjectsPatchJobsInstanceDetailsListRequest(
            parent='projects/my-project/patchJobs/my-patch-job'),
        response=self.messages.ListPatchJobInstanceDetailsResponse(
            patchJobInstanceDetails=self.instance_details))

    self.Run("""
        compute os-config patch-jobs list-instance-details my-patch-job
        --filter="zone=zone-1"
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
                NAME       ZONE   STATE     FAILURE_REASON
                instance-1 zone-1 SUCCEEDED
                """),
        normalize_space=True)
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
