# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Test of the 'dataflow jobs resume-unsupported-sdk' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID
REGION_1 = 'europe-west1'
TOKEN = '2020-08-13T17:00:00-07:00:Af0vGMUj2ihbosc26pIa0zHO5LwkzF_wjVGKS-7-3KgUM0GmUJ5iPgOJPSHqaaVF-sLYXyMxpKnMM_anFdEY-Qa-1zlD1v8Q7GUtPabg_5IudmaIiA'


class ResumeUnsupportedSDKUnitTest(base.DataflowMockingTestBase,
                                   sdk_test_base.WithOutputCapture):

  def SetUp(self):
    pass

  def testResumeUnsupportedSDKSuccessWithRegion(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._ResumeReq(JOB_1_ID, TOKEN, REGION_1),
        response=self.SampleJob(JOB_1_ID, REGION_1))

    self.Run(
        'alpha dataflow jobs resume-unsupported-sdk --token=%s --region=%s %s' %
        (TOKEN, REGION_1, JOB_1_ID))
    self.AssertErrEquals("""\
Resuming job running on unsupported SDK version [{0}]. This job may be cancelled in the future. For more details, see https://cloud.google.com/dataflow/docs/support/sdk-version-support-status.
""".format(JOB_1_ID, normalize_space=True))

  def testResumeSuccessNoRegion(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._ResumeReq(JOB_1_ID, TOKEN),
        response=self.SampleJob(JOB_1_ID))

    self.Run('alpha dataflow jobs resume-unsupported-sdk %s --token=%s' %
             (JOB_1_ID, TOKEN))
    self.AssertErrEquals("""\
WARNING: `--region` not set; defaulting to 'us-central1'. In an upcoming \
release, users must specify a region explicitly. See \
https://cloud.google.com/dataflow/docs/concepts/regional-endpoints \
for additional details.
Resuming job running on unsupported SDK version [{0}]. This job may be cancelled in the future. For more details, see https://cloud.google.com/dataflow/docs/support/sdk-version-support-status.
""".format(JOB_1_ID, normalize_space=True))

  def testResumeUnsupportedSDKWithoutToken(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --token: Must be specified.'):
      self.Run('alpha dataflow jobs resume-unsupported-sdk --region=%s %s' %
               (REGION_1, JOB_1_ID))

  def testResumeUnsupportedSDKFailure(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._ResumeReq(JOB_1_ID, TOKEN, REGION_1),
        exception=http_error.MakeHttpError(403))

    self.Run(
        'alpha dataflow jobs resume-unsupported-sdk --token=%s --region=%s %s' %
        (TOKEN, REGION_1, JOB_1_ID))
    self.AssertErrEquals("""Failed to resume job [{0}]: Permission denied. \
Please ensure you have permission to access the job, the `--region` flag, {1}, \
is correct for the job and the `--token` flag, {2}, corresponds to the job.
""".format(JOB_1_ID, REGION_1, TOKEN, normalize_space=True))

  def _ResumeReq(self, job_id, token, region=None):
    region = region or base.DEFAULT_REGION
    req_class = (base.MESSAGE_MODULE.DataflowProjectsLocationsJobsUpdateRequest)
    environment = base.MESSAGE_MODULE.Environment(
        experiments=['unsupported_sdk_temporary_override_token=' + token])
    return req_class(
        projectId=self.Project(),
        jobId=job_id,
        location=region,
        job=base.MESSAGE_MODULE.Job(environment=environment))


if __name__ == '__main__':
  test_case.main()
