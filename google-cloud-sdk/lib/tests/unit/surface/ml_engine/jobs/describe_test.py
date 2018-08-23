# -*- coding: utf-8 -*- #
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
"""ml-engine jobs describe tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.ml_engine import base
from six.moves import range


class DescribeTestBase(object):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def ExpectJob(self, job):
    """Add expected job output to Mock client.

    Args:
      job: job message to add to expected output.
    """
    self.client.projects_jobs.Get.Expect(
        self.msgs.MlProjectsJobsGetRequest(
            name='projects/{}/jobs/opId'.format(self.Project())),
        job
    )

  def _GetJobSuccess(self, training=True, num_trials=0):
    """Build expected job output to Mock client.

    Args:
      training: boolean- If True set up a training job expectation on the mock
        client. Otherwise set up a prediction job.
      num_trials: int- Number of hyper parameter results to include for training
        jobs. Ignored for prediction jobs.

    Returns:
       ml.job Message
    """
    msgs = self.GetShortNameMessageObject()

    # Build Training Job output
    if training:
      training_input = msgs.TrainingInput(
          args=['--train_dir=gs://my_bucket/my_job/train'],
          masterType='master-type',
          packageUris=[
              'gs://my-bucket/cloudmldist/012345/trainer-0.0.0.tar.gz'
          ],
          parameterServerCount=10,
          parameterServerType='parameter-server-type',
          pythonModule='trainer.task',
          region='us-central1',
          scaleTier=msgs.TrainingInput.ScaleTierValueValuesEnum.BASIC,
          workerCount=100,
          workerType='worker-type')

      training_output = msgs.TrainingOutput(consumedMLUnits=0.5)

      if num_trials > 0:  # Add hyperparameter output
        training_output.completedTrialCount = num_trials
        scale_values = msgs.ParameterSpec.ScaleTypeValueValuesEnum
        type_values = msgs.ParameterSpec.TypeValueValuesEnum
        training_input.hyperparameters = msgs.HyperparameterSpec(
            goal=msgs.HyperparameterSpec.GoalValueValuesEnum.MAXIMIZE,
            maxParallelTrials=1,
            maxTrials=num_trials,
            params=[
                msgs.ParameterSpec(
                    maxValue=300.0,
                    minValue=400.0,
                    parameterName='param',
                    scaleType=scale_values.UNIT_LOG_SCALE,
                    type=type_values.DOUBLE)
            ])
        prop = msgs.HyperparameterOutput.HyperparametersValue.AdditionalProperty
        training_output.trials = []

        for x in range(num_trials):
          training_output.trials.append(
              msgs.HyperparameterOutput(
                  allMetrics=[
                      msgs.HyperparameterOutputHyperparameterMetric(
                          objectiveValue=0.9, trainingStep=100)
                  ],
                  finalMetric=msgs.HyperparameterOutputHyperparameterMetric(
                      objectiveValue=0.99, trainingStep=200),
                  hyperparameters=msgs.
                  HyperparameterOutput.HyperparametersValue(
                      additionalProperties=[prop(key='key1', value='value1'),
                                            prop(key='key2', value='value2'),
                                            prop(key='key3', value='value3')
                                           ]),
                  trialId='trial-{}'.format(x+1)))

      return msgs.Job(
          jobId='my_job',
          createTime='2016-01-01T00:00:00Z',
          endTime='2016-01-01T02:01:00Z',
          errorMessage=None,
          startTime='2016-01-01T01:01:00Z',
          state=msgs.Job.StateValueValuesEnum.SUCCEEDED,
          trainingInput=training_input,
          trainingOutput=training_output)

    # Build Prediction Job output
    prediction_input = msgs.PredictionInput(
        dataFormat=msgs.PredictionInput.DataFormatValueValuesEnum.TF_RECORD,
        inputPaths=['gs://my_bucket/zjn_test_job/input'],
        maxWorkerCount=4,
        modelName='my_model',
        outputPath='gs://my_bucket/zjn_test_job/prediction_output',
        region='us-central1',
        versionName='my_version')

    prediction_output = msgs.PredictionOutput(
        errorCount=0,
        outputPath='gs://my_bucket/my_job/prediction_output',
        predictionCount=20)

    return msgs.Job(
        jobId='my_job',
        createTime='2016-01-01T00:00:00Z',
        endTime='2016-01-01T02:01:00Z',
        errorMessage=None,
        predictionInput=prediction_input,
        predictionOutput=prediction_output,
        startTime='2016-01-01T01:01:00Z',
        state=msgs.Job.StateValueValuesEnum.SUCCEEDED)

  def testDescribe(self):
    expected_job = self._GetJobSuccess()
    self.ExpectJob(expected_job)
    self.assertEqual(
        self.Run('ml-engine jobs describe opId'),
        expected_job)

  def testDescribe_Epilogue(self):
    self.ExpectJob(self._GetJobSuccess())
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('ml-engine jobs describe opId')

    self.AssertErrContains("""\

View job in the Cloud Console at:
https://console.cloud.google.com/ml/jobs/my_job?project=fake-project

View logs at:
https://console.cloud.google.com/logs?\
resource=ml.googleapis.com%2Fjob_id%2Fmy_job&project=fake-project
""")

  def testDescribeSummarizeTraining(self):
    """Test summarize output for standard training job."""
    properties.VALUES.core.user_output_enabled.Set(True)
    self.ExpectJob(self._GetJobSuccess())
    self.Run('ml-engine jobs describe opId --summarize')
    self.AssertOutputEquals("""\
+-----------------------------------------------------------------------------------------+
|                                       Job Overview                                      |
+--------+----------------------+----------------------+----------------------+-----------+
| JOB_ID |     CREATE_TIME      |      START_TIME      |       END_TIME       |   STATE   |
+--------+----------------------+----------------------+----------------------+-----------+
| my_job | 2016-01-01T00:00:00Z | 2016-01-01T01:01:00Z | 2016-01-01T02:01:00Z | SUCCEEDED |
+--------+----------------------+----------------------+----------------------+-----------+
    +--------------------------------------------------------------------------------------------------------------------------------------+
    |                                                        Training Input Summary                                                        |
    +-------------+------------+---------------+-----------------------+------------------------+-------------+-------------+--------------+
    |    REGION   | SCALE_TIER | PYTHON_MODULE | PARAMETER_SERVER_TYPE | PARAMETER_SERVER_COUNT | MASTER_TYPE | WORKER_TYPE | WORKER_COUNT |
    +-------------+------------+---------------+-----------------------+------------------------+-------------+-------------+--------------+
    | us-central1 | BASIC      | trainer.task  | parameter-server-type | 10                     | master-type | worker-type | 100          |
    +-------------+------------+---------------+-----------------------+------------------------+-------------+-------------+--------------+
    +---------------------------------+
    |     Training Output Summary     |
    +---------------------------------+
    |             ML_UNITS            |
    +---------------------------------+
    | 0.5                             |
    +---------------------------------+
     """, normalize_space=True)

  def testDescribeSummarizeHPTraining(self):
    """Test summarize output for hyper parameter tuning training job."""
    properties.VALUES.core.user_output_enabled.Set(True)
    self.ExpectJob(self._GetJobSuccess(num_trials=5))
    self.Run('ml-engine jobs describe opId --summarize')
    self.AssertOutputEquals("""\
+-----------------------------------------------------------------------------------------+
|                                       Job Overview                                      |
+--------+----------------------+----------------------+----------------------+-----------+
| JOB_ID |     CREATE_TIME      |      START_TIME      |       END_TIME       |   STATE   |
+--------+----------------------+----------------------+----------------------+-----------+
| my_job | 2016-01-01T00:00:00Z | 2016-01-01T01:01:00Z | 2016-01-01T02:01:00Z | SUCCEEDED |
+--------+----------------------+----------------------+----------------------+-----------+
    +-------------------------------------------+
    |          Training Output Summary          |
    +--------------------+----------------------+
    |       TRIALS       |       ML_UNITS       |
    +--------------------+----------------------+
    | 5                  | 0.5                  |
    +--------------------+----------------------+
    +----------------------------------------------------+
    |               Training Output Trials               |
    +---------+-----------------+------+-----------------+
    |  TRIAL  | OBJECTIVE_VALUE | STEP | HYPERPARAMETERS |
    +---------+-----------------+------+-----------------+
    | trial-1 | 0.99            | 200  | key1=value1     |
    |         |                 |      | key2=value2     |
    |         |                 |      | key3=value3     |
    | trial-2 | 0.99            | 200  | key1=value1     |
    |         |                 |      | key2=value2     |
    |         |                 |      | key3=value3     |
    | trial-3 | 0.99            | 200  | key1=value1     |
    |         |                 |      | key2=value2     |
    |         |                 |      | key3=value3     |
    | trial-4 | 0.99            | 200  | key1=value1     |
    |         |                 |      | key2=value2     |
    |         |                 |      | key3=value3     |
    | trial-5 | 0.99            | 200  | key1=value1     |
    |         |                 |      | key2=value2     |
    |         |                 |      | key3=value3     |
    +---------+-----------------+------+-----------------+
    """, normalize_space=True)

  def testDescribeSummarizePredict(self):
    """Test summarize output for predict job."""
    properties.VALUES.core.user_output_enabled.Set(True)
    self.ExpectJob(self._GetJobSuccess(training=False))
    self.Run('ml-engine jobs describe opId --summarize')
    self.AssertOutputEquals("""\
+-----------------------------------------------------------------------------------------+
|                                       Job Overview                                      |
+--------+----------------------+----------------------+----------------------+-----------+
| JOB_ID |     CREATE_TIME      |      START_TIME      |       END_TIME       |   STATE   |
+--------+----------------------+----------------------+----------------------+-----------+
| my_job | 2016-01-01T00:00:00Z | 2016-01-01T01:01:00Z | 2016-01-01T02:01:00Z | SUCCEEDED |
+--------+----------------------+----------------------+----------------------+-----------+
    +------------------------------------------------------------------------------------------+
    |                                  Predict Input Summary                                   |
    +-------------+--------------+-----------------------------------------------+-------------+
    |    REGION   | VERSION_NAME |                  OUTPUT_PATH                  | DATA_FORMAT |
    +-------------+--------------+-----------------------------------------------+-------------+
    | us-central1 | my_version   | gs://my_bucket/zjn_test_job/prediction_output | TF_RECORD   |
    +-------------+--------------+-----------------------------------------------+-------------+
    +---------------------------------------------------------------------------------------+
    |                                 Predict Output Summary                                |
    +-------------+------------+-----------------------------------------+------------------+
    | ERROR_COUNT | NODE_HOURS |               OUTPUT_PATH               | PREDICTION_COUNT |
    +-------------+------------+-----------------------------------------+------------------+
    | 0           |            | gs://my_bucket/my_job/prediction_output | 20               |
    +-------------+------------+-----------------------------------------+------------------+
    """, normalize_space=True)

  def testDescribeSummarizeWithFormatFlag(self):
    """Test summarize output with --format flag displays warning."""
    properties.VALUES.core.user_output_enabled.Set(True)
    self.ExpectJob(self._GetJobSuccess(training=False))
    self.Run("""\
    ml-engine jobs describe opId --summarize --format='yaml'
    """)
    self.AssertErrContains('WARNING: --format is ignored when '
                           '--summarize is present')


class DescribeGaTest(DescribeTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(DescribeGaTest, self).SetUp()


class DescribeBetaTest(DescribeTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(DescribeBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
