# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Test of the 'dataflow jobs list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base
from six.moves import range  # pylint: disable=redefined-builtin

JOB_1_ID = base.JOB_1_ID
JOB_2_ID = base.JOB_2_ID

REGION = 'europe-west1'


class ListUnitTest(base.DataflowMockingTestBase,
                   sdk_test_base.WithOutputCapture):

  def SetUp(self):
    env_class = base.MESSAGE_MODULE.Environment
    self.fake_environment = env_class(
        dataset='dataset',
        experiments=['exp1', 'exp2'])
    self.get_job_req_class = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest)

  def testListNoJobs(self):
    self.MockAggregatedListJobs([])
    result = self.Run('beta dataflow jobs list')
    self.assertEqual([], list(result))

  def testListOneJobNoCreationTime(self):
    job = self.SampleJob(job_id='the_job')
    job.createTime = '1970-01-01T00:00:00.000Z'
    jobs = [job]
    self.MockAggregatedListJobs(jobs)

    self.Run('beta dataflow jobs list')
    self.AssertOutputEquals("""\
JOB_ID   NAME          TYPE   CREATION_TIME  STATE  REGION
the_job  the_job_name  Batch  -              Done   us-central1
""")

  def testListOneJob(self):
    jobs = [self.SampleJob(job_id='the_job')]
    self.MockAggregatedListJobs(jobs)

    self.Run('beta dataflow jobs list')
    self.AssertOutputEquals("""\
JOB_ID   NAME          TYPE   CREATION_TIME        STATE  REGION
the_job  the_job_name  Batch  2013-09-06 17:54:10  Done   us-central1
""")

  def testListPaging(self):
    self.MockAggregatedListJobs(
        [self.SampleJob(job_id='job%d' % n) for n in range(1, 5)],
        next_page_token='pageToken')
    self.MockAggregatedListJobs(
        [self.SampleJob(job_id='job%d' % n) for n in range(5, 6)],
        page_token='pageToken')

    self.Run('beta dataflow jobs list')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE  REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Done   us-central1
job2    job2_name  Batch  2013-09-06 17:54:10  Done   us-central1
job3    job3_name  Batch  2013-09-06 17:54:10  Done   us-central1
job4    job4_name  Batch  2013-09-06 17:54:10  Done   us-central1
job5    job5_name  Batch  2013-09-06 17:54:10  Done   us-central1
""")

  def testListAll(self):
    status_enum = (
        base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockAggregatedListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1),
                job_status=status,
                region='test%d' % (n + 1))
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_DONE,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_CANCELLED,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsJobsAggregatedRequest.
        FilterValueValuesEnum.ALL)

    self.Run('beta dataflow jobs list --status=all')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE      REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Running    test1
job2    job2_name  Batch  2013-09-06 17:54:10  Done       test2
job3    job3_name  Batch  2013-09-06 17:54:10  Updated    test3
job4    job4_name  Batch  2013-09-06 17:54:10  Cancelled  test4
job5    job5_name  Batch  2013-09-06 17:54:10  Updated    test5
job6    job6_name  Batch  2013-09-06 17:54:10  Done       test6
""")

  def testListTerminated(self):
    status_enum = (
        base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockAggregatedListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1),
                job_status=status,
                region='test%d' % (n + 1))
            for n, status in enumerate([
                status_enum.JOB_STATE_DONE, status_enum.JOB_STATE_UPDATED,
                status_enum.JOB_STATE_CANCELLED, status_enum.JOB_STATE_UPDATED,
                status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsJobsAggregatedRequest.
        FilterValueValuesEnum.TERMINATED)

    self.Run('beta dataflow jobs list --status=terminated')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE      REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Done       test1
job2    job2_name  Batch  2013-09-06 17:54:10  Updated    test2
job3    job3_name  Batch  2013-09-06 17:54:10  Cancelled  test3
job4    job4_name  Batch  2013-09-06 17:54:10  Updated    test4
job5    job5_name  Batch  2013-09-06 17:54:10  Done       test5
""")

  def testListActive(self):
    status_enum = (
        base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockAggregatedListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1),
                job_status=status,
                region='test%d' % (n + 1))
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_RUNNING,
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_RUNNING,
                status_enum.JOB_STATE_RUNNING
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsJobsAggregatedRequest.
        FilterValueValuesEnum.ACTIVE)

    self.Run('beta dataflow jobs list --status=active')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE    REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Running  test1
job2    job2_name  Batch  2013-09-06 17:54:10  Running  test2
job3    job3_name  Batch  2013-09-06 17:54:10  Running  test3
job4    job4_name  Batch  2013-09-06 17:54:10  Running  test4
job5    job5_name  Batch  2013-09-06 17:54:10  Running  test5
""")

  def testRegionalListAll(self):
    status_enum = (base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1), job_status=status, region=REGION)
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_DONE,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_CANCELLED,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsLocationsJobsListRequest.
        FilterValueValuesEnum.ALL,
        location=REGION)

    self.Run('beta dataflow jobs list --status=all --region=' + REGION)
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE      REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Running    europe-west1
job2    job2_name  Batch  2013-09-06 17:54:10  Done       europe-west1
job3    job3_name  Batch  2013-09-06 17:54:10  Updated    europe-west1
job4    job4_name  Batch  2013-09-06 17:54:10  Cancelled  europe-west1
job5    job5_name  Batch  2013-09-06 17:54:10  Updated    europe-west1
job6    job6_name  Batch  2013-09-06 17:54:10  Done       europe-west1
""")

  def testRegionalListTerminated(self):
    status_enum = (base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1), job_status=status, region=REGION)
            for n, status in enumerate([
                status_enum.JOB_STATE_DONE, status_enum.JOB_STATE_UPDATED,
                status_enum.JOB_STATE_CANCELLED, status_enum.JOB_STATE_UPDATED,
                status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsLocationsJobsListRequest.
        FilterValueValuesEnum.TERMINATED,
        location=REGION)

    self.Run('beta dataflow jobs list --status=terminated --region=' + REGION)
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE      REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Done       europe-west1
job2    job2_name  Batch  2013-09-06 17:54:10  Updated    europe-west1
job3    job3_name  Batch  2013-09-06 17:54:10  Cancelled  europe-west1
job4    job4_name  Batch  2013-09-06 17:54:10  Updated    europe-west1
job5    job5_name  Batch  2013-09-06 17:54:10  Done       europe-west1
""")

  def testRegionalListActive(self):
    status_enum = (base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1), job_status=status, region=REGION)
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_RUNNING,
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_RUNNING,
                status_enum.JOB_STATE_RUNNING
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsLocationsJobsListRequest.
        FilterValueValuesEnum.ACTIVE,
        location=REGION)

    self.Run('beta dataflow jobs list --status=active --region=' + REGION)
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE    REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Running  europe-west1
job2    job2_name  Batch  2013-09-06 17:54:10  Running  europe-west1
job3    job3_name  Batch  2013-09-06 17:54:10  Running  europe-west1
job4    job4_name  Batch  2013-09-06 17:54:10  Running  europe-west1
job5    job5_name  Batch  2013-09-06 17:54:10  Running  europe-west1
""")

  def testListByCreatedBefore(self):
    self.MockAggregatedListJobs([
        self.SampleJob(job_id='job%d' % (n + 1), creation_time=time)
        for n, time in enumerate([
            '2013-09-06 17:54:10', '2013-09-06 17:55:15', '2013-09-06 17:57:16'
        ])
    ])

    self.Run('beta dataflow jobs list --created-before="2013-09-06 17:56:15"')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE  REGION
job1    job1_name  Batch  2013-09-06 17:54:10  Done   us-central1
job2    job2_name  Batch  2013-09-06 17:55:15  Done   us-central1
""")

  def testListByCreatedAfter(self):
    self.MockAggregatedListJobs([
        self.SampleJob(job_id='job%d' % (n + 1), creation_time=time)
        for n, time in enumerate([
            '2013-09-06 17:54:10', '2013-09-06 17:55:15', '2013-09-06 17:57:16'
        ])
    ])

    self.Run('beta dataflow jobs list '
             '--created-after="2013-09-06 17:54:11"')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE  REGION
job2    job2_name  Batch  2013-09-06 17:55:15  Done   us-central1
job3    job3_name  Batch  2013-09-06 17:57:16  Done   us-central1
""")

  def testListByCreatedBeforeAndAfter(self):
    self.MockAggregatedListJobs([
        self.SampleJob(job_id='job%d' % (n + 1), creation_time=time)
        for n, time in enumerate([
            '2013-09-06 17:54:10', '2013-09-06 17:55:15', '2013-09-06 17:57:16'
        ])
    ])

    self.Run('beta dataflow jobs list '
             '--created-before="2013-09-06 17:56:15" '
             '--created-after="2013-09-06 17:54:11"')
    self.AssertOutputEquals("""\
JOB_ID  NAME       TYPE   CREATION_TIME        STATE  REGION
job2    job2_name  Batch  2013-09-06 17:55:15  Done   us-central1
""")

  def testListUriFlag(self):
    status_enum = (
        base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockAggregatedListJobs(
        [
            self.SampleJob(job_id='job%d' % (n + 1), job_status=status)
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_DONE,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_CANCELLED,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsJobsAggregatedRequest.
        FilterValueValuesEnum.ALL)

    self.Run('beta dataflow jobs list --uri')
    self.AssertOutputEquals("""\
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job1
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job2
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job3
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job4
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job5
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/us-central1/jobs/job6
""")

  def testListUriFlagWithRegion(self):
    status_enum = (base.MESSAGE_MODULE.Job.CurrentStateValueValuesEnum)
    self.MockListJobs(
        [
            self.SampleJob(
                job_id='job%d' % (n + 1), job_status=status, region=REGION)
            for n, status in enumerate([
                status_enum.JOB_STATE_RUNNING, status_enum.JOB_STATE_DONE,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_CANCELLED,
                status_enum.JOB_STATE_UPDATED, status_enum.JOB_STATE_DONE
            ])
        ],
        filter=base.MESSAGE_MODULE.DataflowProjectsLocationsJobsListRequest.
        FilterValueValuesEnum.ALL,
        location=REGION)

    self.Run('beta dataflow jobs list --uri --region=' + REGION)
    self.AssertOutputEquals("""\
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job1
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job2
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job3
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job4
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job5
https://dataflow.googleapis.com/v1b3/projects/fake-project/locations/europe-west1/jobs/job6
""")


if __name__ == '__main__':
  test_case.main()
