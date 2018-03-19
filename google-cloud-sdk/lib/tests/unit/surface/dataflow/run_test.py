# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Test of the 'dataflow jobs run' command."""

from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class RunUnitTest(base.DataflowMockingTestBase,
                  sdk_test_base.WithOutputCapture):

  def SetUp(self):
    env_class = base.MESSAGE_MODULE.Environment
    self.fake_environment = env_class()

  def testRunNoParameters(self):
    self.MockRunJob(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob'),
        job_name='myjob',
        gcs_location='gs://foo')
    result = self.Run('dataflow jobs run myjob --gcs-location=gs://foo')
    self.assertEquals(JOB_1_ID, result.id)
    self.assertEquals('myjob', result.name)

  def testRunBadGcs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        """Must begin with 'gs://'"""):
      self.Run('dataflow jobs run myjob --gcs-location=foo')

  def testRunBadStagingGcs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        """Must begin with 'gs://'"""):
      self.Run('dataflow jobs run myjob --gcs-location=gs://foo '
               '--staging-location=bar')

  def testRunWithParameters(self):
    self.MockRunJob(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment),
        gcs_location='gs://foo',
        job_name='myjob',
        parameters=dict(
            baz='quux', bar='foo'))
    result = self.Run('dataflow jobs run myjob --gcs-location=gs://foo'
                      ' --parameters=bar=foo,baz=quux')
    self.assertEquals(JOB_1_ID, result.id)

  def testRunWithParametersWithRegion(self):
    my_region = 'europe-west1'
    self.MockRunJob(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, region=my_region),
        gcs_location='gs://foo',
        job_name='myjob',
        parameters=dict(baz='quux', bar='foo'),
        location=my_region)
    result = self.Run('dataflow jobs run myjob --gcs-location=gs://foo'
                      ' --parameters=bar=foo,baz=quux --region=' + my_region)
    self.assertEquals(JOB_1_ID, result.id)

  def testRunNoLocation(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --gcs-location: Must be specified.'):
      self.Run('dataflow jobs run myjob')

  def testRunNoJobName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_NAME: Must be specified.'):
      self.Run('dataflow jobs run --gcs-location=gs://foo')

  def testRunWithRuntimeEnvironmentValues(self):
    self.MockRunJob(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment),
        gcs_location='gs://foo',
        service_account_email='a@b.com',
        zone='us-foo1-a',
        job_name='myjob',
        max_workers=5)
    result = self.Run(
        'dataflow jobs run myjob --gcs-location=gs://foo '
        '--service-account-email=a@b.com --zone=us-foo1-a --max-workers=5')
    self.assertEquals(JOB_1_ID, result.id)

if __name__ == '__main__':
  test_case.main()
