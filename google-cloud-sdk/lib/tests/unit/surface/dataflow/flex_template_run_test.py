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
"""Test of the 'dataflow flex_template run' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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

  def testRunBetaBadTemplateFile(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        """Must begin with 'gs://'"""):
      self.Run(
          'dataflow flex-template run myjob '
          '--template-file-gcs-location=foo')

  def testRunBetaNoTemplateFile(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template-file-gcs-location: Must be specified.'):
      self.Run('dataflow flex-template run myjob')

  def testRunBetaNoJobName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_NAME: Must be specified.'):
      self.Run(
          'dataflow flex-template run '
          '--template-file-gcs-location=gs://foo')

  def testRunBetaWithFlexTemplate(self):
    response = base.MESSAGE_MODULE.LaunchFlexTemplateResponse(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob')
        )
    params = [
        ('zone', 'us-foo1-a'),
        ('max_num_workers', 5),
        ('service_account_email', 'a@b.com')
    ]
    self.MockRunFlexTemplateJob(
        job_response=response,
        location='europe-west1',
        gcs_location='gs://foo',
        parameters=params,
        job_name='myjob')
    result = self.Run(
        'dataflow flex-template run myjob '
        '--template-file-gcs-location=gs://foo '
        '--region=europe-west1 '
        '--parameters=zone="us-foo1-a",max_num_workers=5,'
        'service_account_email="a@b.com"')
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testRunBetaNoParameters(self):
    response = base.MESSAGE_MODULE.LaunchFlexTemplateResponse(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob')
        )
    self.MockRunFlexTemplateJob(
        job_response=response,
        location='us-central1',
        gcs_location='gs://foo',
        job_name='myjob')
    result = self.Run(
        'dataflow flex-template run myjob '
        '--template-file-gcs-location=gs://foo')
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testRunWithFlexTemplateRuntimeEnvironmentValues(self):
    response = base.MESSAGE_MODULE.LaunchFlexTemplateResponse(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob')
        )
    labels = [('label1', 'value1')]
    experiments = ['experiment1', 'experiment2']
    self.MockRunFlexTemplateJob(
        job_response=response,
        location='us-central1',
        gcs_location='gs://foo',
        job_name='myjob',
        service_account_email='a@b.com',
        worker_zone='us-foo1-a',
        max_workers=5,
        num_workers=5,
        worker_machine_type='n1-standard-1',
        network='network',
        subnetwork='subnetwork',
        kms_key_name='cloud-kms-key-foobar',
        staging_location='gs://staging',
        additional_user_labels=labels,
        additional_experiments=experiments
        )
    result = self.Run(
        'dataflow flex-template run myjob --template-file-gcs-location=gs://foo '
        '--service-account-email=a@b.com --worker-zone=us-foo1-a --max-workers=5 '
        '--num-workers=5 --worker-machine-type=n1-standard-1 --network=network '
        '--subnetwork=subnetwork --dataflow-kms-key=cloud-kms-key-foobar '
        '--staging-location=gs://staging '
        '--additional-user-labels="label1"="value1" '
        '--additional-experiments="experiment1,experiment2"')
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testRunWithFlexTemplatePrivateIpEnvironmentValue(self):
    response = base.MESSAGE_MODULE.LaunchFlexTemplateResponse(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob')
        )
    self.MockRunFlexTemplateJob(
        job_response=response,
        location='us-central1',
        gcs_location='gs://foo',
        job_name='myjob',
        disable_public_ips=True)
    result = self.Run(
        'dataflow flex-template run myjob --template-file-gcs-location=gs://foo '
        '--disable-public-ips')
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testRunWithFlexTemplateEnableStreamingEngineEnvironmentValue(self):
    response = base.MESSAGE_MODULE.LaunchFlexTemplateResponse(
        job=self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, job_name='myjob')
        )
    self.MockRunFlexTemplateJob(
        job_response=response,
        location='us-central1',
        gcs_location='gs://foo',
        job_name='myjob',
        enable_streaming_engine=True)
    result = self.Run(
        'dataflow flex-template run myjob --template-file-gcs-location=gs://foo '
        '--enable-streaming-engine')
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

if __name__ == '__main__':
  test_case.main()
