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
"""ai-platform jobs submit batch prediction tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class SubmitPredictionBase(object):

  def SetUp(self):
    prediction_input_class = self.short_msgs.PredictionInput
    self.data_formats = prediction_input_class.DataFormatValueValuesEnum
    self.states = self.short_msgs.Job.StateValueValuesEnum
    # For consistent output of times
    self.StartObjectPatch(times, 'LOCAL', times.GetTimeZone('PST'))

  def _MakeCreateRequest(self, job, parent):
    raise NotImplementedError()

  def testBatchPrediction(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job(
            jobId='my_job',
            state=self.states.QUEUED,
            startTime='2016-01-01T00:00:00Z'))

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central-1c'.format(module_name))
    self.AssertOutputEquals("""\
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: QUEUED
        """, normalize_space=True)
    self.AssertErrContains(
        """\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ai-platform jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ai-platform jobs stream-logs my_job
        """,
        normalize_space=True)

  def testBatchPredictionRepeatedInput(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instance',
                                'gs://bucket/instance2'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instance,gs://bucket/instance2 '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central-1c'.format(module_name))

  def testBatchPredictionNoVersion(self, module_name):
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TEXT,
                    inputPaths=['gs://bucket/instances'],
                    modelName='projects/fake-project/models/my_model',
                    outputPath='gs://bucket/output',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --input-paths gs://bucket/instances '
             '    --data-format TEXT '
             '    --output-path gs://bucket/output '
             '    --region us-central-1c'.format(module_name))

  def testBatchPredictionGzipTFRecord(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD_GZIP,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD_GZIP '
             '    --output-path gs://bucket/output '
             '    --region us-central-1c'.format(module_name))

  def testBatchPredictionRuntimeVersion(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD_GZIP,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    runtimeVersion='0.12',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD_GZIP '
             '    --output-path gs://bucket/output '
             '    --runtime-version 0.12 '
             '    --region us-central-1c'.format(module_name))

  def _MakeLabels(self, labels):
    labels_cls = self.short_msgs.Job.LabelsValue
    return labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key=key, value=value) for key, value in
        sorted(labels.items())
    ])

  def testBatchPredictionLabels(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    labels = self._MakeLabels({'key': 'value'})
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                labels=labels,
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD_GZIP,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central-1c')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD_GZIP '
             '    --output-path gs://bucket/output '
             '    --labels key=value'
             '    --region us-central-1c'.format(module_name))

  def testBatchPredictionModelDir(self, module_name):
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            job=self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD_GZIP,
                    inputPaths=['gs://bucket/instances'],
                    uri='gs://some_bucket/models',
                    outputPath='gs://bucket/output',
                    region='us-central1')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model-dir gs://some_bucket/models '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD_GZIP '
             '    --output-path gs://bucket/output '
             '    --region us-central1'.format(module_name))

  def testBatchPredictionVersionWithModelDir(self, module_name):
    with self.assertRaisesRegex(
        core_exceptions.Error, '`--version` cannot be set with `--model-dir`'):
      self.Run('{} jobs submit prediction my_job '
               '    --model-dir gs://some_bucket/models '
               '    --version v1 '
               '    --input-paths gs://bucket/instances '
               '    --data-format TF_RECORD '
               '    --output-path gs://bucket/output '
               '    --region us-central1'.format(module_name))

  def testBatchPredictionMaxWorkerCount(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            job=self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central',
                    maxWorkerCount=3)),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central '
             '    --max-worker-count 3'.format(module_name))

  def testBatchPredictionBatchSize(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            job=self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central',
                    batchSize=128)),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central '
             '    --batch-size 128'.format(module_name))

  def testBatchPredictionSignatureName(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            job=self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central',
                    signatureName='my-custom-signature')),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central '
             '    --signature-name my-custom-signature'.format(module_name))


class SubmitPredictionGaTest(SubmitPredictionBase,
                             base.MlGaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(SubmitPredictionGaTest, self).SetUp()


class SubmitPredictionBetaTest(SubmitPredictionBase,
                               base.MlBetaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(SubmitPredictionBetaTest, self).SetUp()


class SubmitPredictionAlphaTest(SubmitPredictionBase,
                                base.MlBetaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(SubmitPredictionAlphaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.ALPHA

  @parameterized.parameters(
      # Bad accelerator type no accelerator count.
      {'acc_type_flag': '--accelerator-type IN_VALID',
       'acc_count_flag': '', 'error_msg': (r'argument --accelerator-type: '
                                           r'Invalid choice: \'in-valid\'')},
      # Bad accelerator type
      {'acc_type_flag': '--accelerator-type IN_VALID',
       'acc_count_flag': '--accelerator-count 2',
       'error_msg': (r'argument --accelerator-type: '
                     r'Invalid choice: \'in-valid\'')},
      # Good accelerator type and no count
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '', 'error_msg': (r'argument --accelerator-count: '
                                           r'Must be specified.')},
      # Good accelerator type and bad count (negative)
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '--accelerator-count -1', 'error_msg':
       (r'argument --accelerator-count: '
        r'Value must be greater than or equal to 1')},
      # Good accelerator type and bad count (non-int)
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '--accelerator-count 2.5', 'error_msg':
       (r'argument --accelerator-count: Value must be an integer')},
      # No accelerator type
      {'acc_type_flag': '', 'acc_count_flag': '--accelerator-count 2',
       'error_msg': r'argument --accelerator-type: Must be specified.'},
  )
  def testBatchPredictInvalidAcceleratorTypeAndCount_ml_engine(
      self, acc_type_flag, acc_count_flag, error_msg):
    self._TestBatchPredictInvalidAcceleratorTypeAndCount(
        acc_type_flag, acc_count_flag, error_msg, 'ml-engine')

  @parameterized.parameters(
      # Bad accelerator type no accelerator count.
      {'acc_type_flag': '--accelerator-type IN_VALID',
       'acc_count_flag': '', 'error_msg': (r'argument --accelerator-type: '
                                           r'Invalid choice: \'in-valid\'')},
      # Bad accelerator type
      {'acc_type_flag': '--accelerator-type IN_VALID',
       'acc_count_flag': '--accelerator-count 2',
       'error_msg': (r'argument --accelerator-type: '
                     r'Invalid choice: \'in-valid\'')},
      # Good accelerator type and no count
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '', 'error_msg': (r'argument --accelerator-count: '
                                           r'Must be specified.')},
      # Good accelerator type and bad count (negative)
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '--accelerator-count -1', 'error_msg':
       (r'argument --accelerator-count: '
        r'Value must be greater than or equal to 1')},
      # Good accelerator type and bad count (non-int)
      {'acc_type_flag': '--accelerator-type nvidia-tesla-k80',
       'acc_count_flag': '--accelerator-count 2.5', 'error_msg':
       (r'argument --accelerator-count: Value must be an integer')},
      # No accelerator type
      {'acc_type_flag': '', 'acc_count_flag': '--accelerator-count 2',
       'error_msg': r'argument --accelerator-type: Must be specified.'},
  )
  def testBatchPredictInvalidAcceleratorTypeAndCount(self, acc_type_flag,
                                                     acc_count_flag, error_msg):
    self._TestBatchPredictInvalidAcceleratorTypeAndCount(
        acc_type_flag, acc_count_flag, error_msg, 'ai-platform')

  def _TestBatchPredictInvalidAcceleratorTypeAndCount(
      self, acc_type_flag, acc_count_flag, error_msg, module_name):
    with self.AssertRaisesArgumentErrorRegexp(error_msg):
      self.Run('{module_name} jobs submit prediction my_job '
               '    --model my_model '
               '    --version v1 '
               '    --input-paths gs://bucket/instances '
               '    --data-format TF_RECORD '
               '    --output-path gs://bucket/output '
               '    --region us-central '
               '{accelerator_type} {accelerator_count}'.format(
                   module_name=module_name,
                   accelerator_type=acc_type_flag,
                   accelerator_count=acc_count_flag))

  def testBatchPredictAcceleratorTypeAndCount_ml_engine(self):
    self._TestBatchPredictAcceleratorTypeAndCount('ml-engine')

  def testBatchPredictAcceleratorTypeAndCount(self):
    self._TestBatchPredictAcceleratorTypeAndCount('ai-platform')

  def _TestBatchPredictAcceleratorTypeAndCount(self, module_name):
    version_name = 'projects/fake-project/models/my_model/versions/v1'
    accelerator_config = (self.short_msgs.AcceleratorConfig(
        count=4, type=self.short_msgs.AcceleratorConfig.
        TypeValueValuesEnum('NVIDIA_TESLA_P100')))
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            job=self.short_msgs.Job(
                jobId='my_job',
                predictionInput=self.short_msgs.PredictionInput(
                    dataFormat=self.data_formats.TF_RECORD,
                    inputPaths=['gs://bucket/instances'],
                    versionName=version_name,
                    outputPath='gs://bucket/output',
                    region='us-central',
                    accelerator=accelerator_config)),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

    self.Run('{} jobs submit prediction my_job '
             '    --model my_model '
             '    --version v1 '
             '    --input-paths gs://bucket/instances '
             '    --data-format TF_RECORD '
             '    --output-path gs://bucket/output '
             '    --region us-central '
             '    --accelerator-type nvidia-tesla-p100'
             '    --accelerator-count 4'.format(module_name))


if __name__ == '__main__':
  test_case.main()
