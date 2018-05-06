# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Test of the 'dataflow jobs cancel' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID
JOB_2_ID = base.JOB_2_ID
JOB_3_ID = base.JOB_3_ID


class CancelUnitTest(base.DataflowMockingTestBase,
                     sdk_test_base.WithOutputCapture):

  def testCancelSuccess(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_1_ID), response=self.SampleJob(JOB_1_ID))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_2_ID), response=self.SampleJob(JOB_2_ID))

    self.Run('beta dataflow jobs cancel %s %s' % (JOB_1_ID, JOB_2_ID))
    self.AssertErrEquals("""\
Cancelled job [{0}]
Cancelled job [{1}]
""".format(JOB_1_ID, JOB_2_ID, normalize_space=True))

  def testCancelSuccessWithRegion(self):
    my_region = 'europe-west1'
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_1_ID, region=my_region),
        response=self.SampleJob(JOB_1_ID, region=my_region))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_2_ID, region=my_region),
        response=self.SampleJob(JOB_2_ID, region=my_region))

    self.Run('beta dataflow jobs cancel --region=%s %s %s' %
             (my_region, JOB_1_ID, JOB_2_ID))
    self.AssertErrEquals("""\
Cancelled job [{0}]
Cancelled job [{1}]
""".format(JOB_1_ID, JOB_2_ID, normalize_space=True))

  def testCancelReturnsPermissionsError(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_1_ID), response=self.SampleJob(JOB_1_ID))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_2_ID),
        exception=http_error.MakeHttpError(403))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_3_ID), response=self.SampleJob(JOB_3_ID))

    self.Run('beta dataflow jobs cancel %s %s %s' %
             (JOB_1_ID, JOB_2_ID, JOB_3_ID))
    self.AssertErrEquals("""\
Cancelled job [{0}]
Failed to cancel job [{1}]: Permission denied.
Cancelled job [{2}]
""".format(JOB_1_ID, JOB_2_ID, JOB_3_ID, normalize_space=True))

  def testCancelContinuesOnFailure(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_1_ID), response=self.SampleJob(JOB_1_ID))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_2_ID),
        exception=http_error.MakeHttpError(404))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._CancelReq(JOB_3_ID), response=self.SampleJob(JOB_3_ID))

    self.Run('beta dataflow jobs cancel %s %s %s' %
             (JOB_1_ID, JOB_2_ID, JOB_3_ID))
    self.AssertErrEquals("""\
Cancelled job [{0}]
Failed to cancel job [{1}]: Resource not found.
Cancelled job [{2}]
""".format(JOB_1_ID, JOB_2_ID, JOB_3_ID, normalize_space=True))

  def _CancelReq(self, job_id, region=None):
    region = region or base.DEFAULT_REGION
    req_class = (base.MESSAGE_MODULE.DataflowProjectsLocationsJobsUpdateRequest)
    return req_class(
        projectId=self.Project(),
        jobId=job_id,
        location=region,
        job=base.MESSAGE_MODULE.Job(
            requestedState=(base.MESSAGE_MODULE.Job.
                            RequestedStateValueValuesEnum.JOB_STATE_CANCELLED)))


if __name__ == '__main__':
  test_case.main()
