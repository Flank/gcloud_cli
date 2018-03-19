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

"""Integration test for all 'dataproc jobs' commands."""

import os
import tempfile

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import e2e_base


class JobsIntegrationTest(e2e_base.DataprocIntegrationTestBase):
  """Integration test for all job commands.

  Most tests are run asynchronously with the exception of the Pig tests which
  also test Waiting, Cancellation, and Failure. Those tests are deemed
  sufficient to test polling logic.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  # Location of a script containing "print 'hello world'".
  GCS_PYSPARK_SCRIPT = (
      'gs://dataproc-a63ced4c-fa87-4bea-94a5-4d2f8fbbd783-us/hello_world.py')

  def SetUp(self):
    self.job_id_generator = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-dataproc-integration')

  def testAllJobsCommands(self):
    """Run all tests as one test case reuse a cluster when sharded."""
    self.CreateClusterWithRetries()
    # These two test cases are synchronous, so run them on a fresh cluster not
    # running jobs.
    self.DoTestJobWaiting()
    self.DoTestJobFailure()
    self.DoTestGetSetIAMPolicy()
    # We do not wait for any of these jobs to run, so we submit them last.
    self.DoTestHadoopJobSubmission()
    self.DoTestHiveJobSubmission()
    self.DoTestPigJobSubmission()
    self.DoTestPySparkJobSubmission()
    self.DoTestSparkJobSubmission()
    self.DoTestSparkSqlJobSubmission()
    # Cluster will get deleted in TearDown.

  def DoTestHadoopJobSubmission(self):
    result = self.RunDataproc((
        'jobs submit hadoop '
        '--cluster {0} '
        '--async '
        '--class org.apache.hadoop.fs.FsShell '
        '-- '
        '-ls file:///usr/lib/hadoop/bin '
    ).format(self.cluster_name))
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.hadoopJob)

  def DoTestHiveJobSubmission(self):
    result = self.RunDataproc((
        'jobs submit hive '
        '--cluster {0} '
        '--async '
        '--execute "SELECT(1)" '
    ).format(self.cluster_name))
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.hiveJob)

  def DoTestPigJobSubmission(self):
    result = self.RunDataproc((
        'jobs submit pig '
        '--cluster {0} '
        '--async '
        '--execute "sh echo test pig job submission" '
    ).format(self.cluster_name))
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.pigJob)

  def DoTestPySparkJobSubmission(self):
    local_script = None
    if self.IsBundled():
      # If this is bundled, gsutil is available for uploads.
      with tempfile.NamedTemporaryFile(
          dir=self.temp_path, suffix='.py', delete=False) as local_script:
        local_script.write("print 'hello world'")
      script_uri = local_script.name
    else:
      # Use script file that is known to exist.
      script_uri = self.GCS_PYSPARK_SCRIPT
    result = self.RunDataproc((
        'jobs submit pyspark '
        '--cluster {0} '
        '--async '
        '{1} '
    ).format(self.cluster_name, script_uri))
    if local_script:
      os.remove(local_script.name)
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.pysparkJob)

  def DoTestSparkJobSubmission(self):
    result = self.RunDataproc((
        'jobs submit spark '
        '--cluster {0} '
        '--async '
        '--class org.apache.spark.examples.DriverSubmissionTest '
        '--jars file:///usr/lib/spark/lib/spark-examples.jar '
        '--properties spark.test.foo=bar '
        '-- '
        '0'  # Sleep 0 seconds
    ).format(self.cluster_name))
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.sparkJob)

  def DoTestSparkSqlJobSubmission(self):
    result = self.RunDataproc((
        'jobs submit spark-sql '
        '--cluster {0} '
        '--async '
        '--execute "SELECT(1)" '
    ).format(self.cluster_name))
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)
    self.assertIsNotNone(result.sparkSqlJob)

  def DoTestJobWaiting(self):
    job_id = self.job_id_generator.next()
    result = self.RunDataproc((
        'jobs submit pig '
        '--cluster {0} '
        '--async '
        '--id {1} '
        '--execute "sh echo test job waiting" '
        '--async '
    ).format(self.cluster_name, job_id))
    self.assertEqual(job_id, result.reference.jobId)
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.PENDING,
                     result.status.state)

    result = self.RunDataproc('jobs wait {0}'.format(job_id))
    # The only test of streaming job output.
    self.AssertErrMatches(r'^test job waiting$')
    self.assertEqual(self.messages.JobStatus.StateValueValuesEnum.DONE,
                     result.status.state)

  def DoTestJobFailure(self):
    job_id = self.job_id_generator.next()
    with self.AssertRaisesExceptionMatches(
        exceptions.JobError,
        'Job [{0}] entered state [ERROR] while waiting for [DONE].'.format(
            job_id)):
      self.RunDataproc((
          'jobs submit pig '
          '--cluster {0} '
          '--id {1} '
          '--execute "sh false" '
      ).format(self.cluster_name, job_id))

  def DoTestGetSetIAMPolicy(self):
    pass

  # The following tests do not require a cluster and can be safely sharded.

  def testJobsList(self):
    self.RunDataproc('jobs list --page-size=10 --limit=20')

  def testJobsDescribe(self):
    jobs = list(self.RunDataproc(
        'jobs list --page-size=20 --limit=20 --state-filter=inactive'))
    if not jobs:
      self.skipTest('No jobs to describe')
    job_id = jobs[0].reference.jobId
    job = self.RunDataproc('jobs describe {0}'.format(job_id))
    # TODO(b/35996214): Uncomment after fixing AssertMessagesEqual to handle
    # JsonValue field sorting.
    # self.AssertMessagesEqual(jobs[0], job)
    self.assertEqual(job_id, job.reference.jobId)


class JobsIntegrationTestBeta(JobsIntegrationTest, base.DataprocTestBaseBeta):
  """Integration test for all job commands.

  Most tests are run asynchronously with the exception of the Pig tests which
  also test Waiting, Cancellation, and Failure. Those tests are deemed
  sufficient to test polling logic.

  See DataprocIntegrationTestBase for requirements of tests that create
  clusters.
  """

  def testBeta(self):
    self.assertEqual(self.messages,
                     core_apis.GetMessagesModule('dataproc', 'v1beta2'))
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def DoTestGetSetIAMPolicy(self):
    job_id = self.job_id_generator.next()
    self.RunDataproc((
        'jobs submit pig '
        '--cluster {0} '
        '--async '
        '--id {1} '
        '--execute "sh echo test job iam policy" '
        '--async '
    ).format(self.cluster_name, job_id))
    self.GetSetIAMPolicy('jobs', job_id)


if __name__ == '__main__':
  sdk_test_base.main()
