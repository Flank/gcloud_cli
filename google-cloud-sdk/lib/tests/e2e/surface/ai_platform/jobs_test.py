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
"""e2e tests for ai-platform jobs command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import test_case


@parameterized.parameters('ml-engine', 'ai-platform')
class MlJobsTests(e2e_base.WithServiceAuth, parameterized.TestCase):
  """e2e tests for ai-platform jobs command group."""

  MODEL_ID = 'do_not_delete_model'
  VERSION_ID = 'do_not_delete_version'
  BUCKET_REF = storage_util.BucketReference.FromUrl(
      'gs://cloud-sdk-integration-testing-ml')

  @contextlib.contextmanager
  def SubmitJob(self, type_, job_id, arguments, module_name):
    try:
      self.Run('{} jobs submit {} {} {}'.format(module_name, type_, job_id,
                                                arguments))
      yield
    finally:
      storage_client = storage_api.StorageClient()
      for obj in storage_client.ListBucket(self.BUCKET_REF):
        if obj.name.startswith(job_id + '/'):
          storage_client.DeleteObject(
              storage_util.ObjectReference.FromMessage(obj))

  def testJobsSubmitTraining(self, module_name):
    job_id = next(e2e_utils.GetResourceNameGenerator(prefix='ml_job',
                                                     delimiter='_'))
    package = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                            'testdata', 'trainer-0.0.0.tar.gz')

    with self.SubmitJob(
        'training', job_id,
        ('    --staging-bucket {bucket_url} '
         '    --region us-central1 '
         '    --module-name trainer.task '
         '    --packages {package} '
         '    --master-image-uri gcr.io/deeplearning-platform-release/tf2-cpu '
         '    --async').format(bucket_url=self.BUCKET_REF.ToUrl(),
                               package=package), module_name):
      # Cancel immediately so we don't do any real work
      self.Run('{} jobs cancel '.format(module_name) + job_id)
      # Check that the job was created
      self.ClearOutput()
      self.Run('{} jobs describe '.format(module_name) + job_id)
      self.AssertOutputContains('jobId: ' + job_id)

  def testJobsSubmitPrediction(self, module_name):
    r"""Tests creating a prediction job.

    This test is predicated on the existence of a trained model in the project.
    This model can easily be reproduced; it just takes
    several minutes:

    $ gcloud config set project $PROJECT
    $ gcloud ml-engine models create do_not_delete_model --regions=us-central1
    $ gcloud ml-engine versions create do_not_delete_version \
        --model do_not_delete_model \
        --origin ${CLOUDSDK_TEST_DIR}/e2e/surface/ml_engine/testdata/model \
        --staging-bucket gs://${PROJECT}-ml

    Args:
      module_name : The surface command to run. One of "ai-platform" or it's
        alias "ml-engine".
    """
    job_id = next(e2e_utils.GetResourceNameGenerator(prefix='ml_job',
                                                     delimiter='_'))
    with self.SubmitJob(
        'prediction', job_id,
        ('  --model={model_id} '
         '  --version={version_id} '
         '  --runtime-version=2.1 '
         '  --data-format TEXT '
         '  --input-paths gs://cloud-ml-data/mnist/predict_sample.tensor.json '
         '  --output-path {bucket_url}/{job_id} '
         '  --region us-central1').format(
             job_id=job_id,
             bucket_url=self.BUCKET_REF.ToUrl(),
             model_id=self.MODEL_ID,
             version_id=self.VERSION_ID), module_name):
      # Cancel immediately so we don't do any real work
      self.Run('{} jobs cancel '.format(module_name) + job_id)
      # Check that the job was created
      self.ClearOutput()
      self.Run('{} jobs describe '.format(module_name) + job_id)
      self.AssertOutputContains('jobId: ' + job_id)

  def testJobsSubmitTrainingCustomServer(self, module_name):
    job_id = next(e2e_utils.GetResourceNameGenerator(prefix='ml_job',
                                                     delimiter='_'))
    package = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                            'testdata', 'trainer-0.0.0.tar.gz')

    with self.SubmitJob('training', job_id,
                        ('    --staging-bucket {bucket_url} '
                         '    --region us-central1 '
                         '    --runtime-version 1.12 '
                         '    --scale-tier CUSTOM  '
                         '    --master-machine-type n1-standard-16 '
                         '    --worker-machine-type n1-standard-16'
                         '    --worker-count 2'
                         '    --module-name trainer.task '
                         '    --packages {package} '
                         '    --async').format(
                             bucket_url=self.BUCKET_REF.ToUrl(),
                             package=package), module_name):
      # Cancel immediately so we don't do any real work
      self.Run('{} jobs cancel '.format(module_name) + job_id)
      # Check that the job was created
      self.ClearOutput()
      self.Run('{} jobs describe '.format(module_name) + job_id)
      self.AssertOutputContains('jobId: ' + job_id)


@parameterized.parameters('ml-engine', 'ai-platform')
class MlJobsTestsBeta(MlJobsTests, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class MlJobsTestsAlpha(MlJobsTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
