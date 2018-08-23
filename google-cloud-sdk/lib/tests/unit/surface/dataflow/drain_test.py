# -*- coding: utf-8 -*- #
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

"""Test of the 'dataflow jobs drain' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID
JOB_2_ID = base.JOB_2_ID
JOB_3_ID = base.JOB_3_ID
JOB_4_ID = base.JOB_4_ID


class DrainUnitTest(base.DataflowMockingTestBase,
                    sdk_test_base.WithOutputCapture):

  def SetUp(self):
    pass

  def testDrainSuccess(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_1_ID), response=self.SampleJob(JOB_1_ID))

    self.Run('beta dataflow jobs drain ' + JOB_1_ID)
    self.AssertErrEquals("""\
Started draining job [{0}]
""".format(JOB_1_ID, normalize_space=True))

  def testDrainSuccessWithRegion(self):
    my_region = 'europe-west1'
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_1_ID, region=my_region),
        response=self.SampleJob(JOB_1_ID, region=my_region))

    self.Run('beta dataflow jobs drain --region=%s %s' % (my_region, JOB_1_ID))
    self.AssertErrEquals("""\
Started draining job [{0}]
""".format(JOB_1_ID, normalize_space=True))

  def testDrainContinuesOnFailure(self):
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_1_ID), response=self.SampleJob(JOB_1_ID))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_2_ID),
        exception=http_error.MakeHttpError(404))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_3_ID), response=self.SampleJob(JOB_3_ID))
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request=self._DrainReq(JOB_4_ID),
        exception=http_error.MakeHttpError(403))

    self.Run('beta dataflow jobs drain {0} {1} {2} {3}'.format(
        JOB_1_ID, JOB_2_ID, JOB_3_ID, JOB_4_ID, normalize_space=True))
    self.AssertErrEquals("""\
Started draining job [{0}]
Failed to drain job [{1}]: Resource not found.
Started draining job [{2}]
Failed to drain job [{3}]: Permission denied.
""".format(JOB_1_ID, JOB_2_ID, JOB_3_ID, JOB_4_ID, normalize_space=True))

  def _DrainReq(self, job_id, region=None):
    region = region or base.DEFAULT_REGION
    req_class = (base.MESSAGE_MODULE.DataflowProjectsLocationsJobsUpdateRequest)
    return req_class(
        projectId=self.Project(),
        jobId=job_id,
        location=region,
        job=base.MESSAGE_MODULE.Job(
            requestedState=(base.MESSAGE_MODULE.Job.
                            RequestedStateValueValuesEnum.JOB_STATE_DRAINED)))


if __name__ == '__main__':
  test_case.main()
