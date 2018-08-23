# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""e2e tests for ml-engine jobs command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class MlJobsTests(e2e_base.WithServiceAuth):
  """E2E tests for ml-engine jobs command group."""

  MODEL_ID = 'do_not_delete_model'
  VERSION_ID = 'do_not_delete_version'
  BUCKET_REF = storage_util.BucketReference.FromBucketUrl(
      'gs://cloud-sdk-integration-testing-ml')

  def RunTracked(self, command):
    return self.Run(command)

  @contextlib.contextmanager
  def _SubmitJob(self, type_, job_id, arguments):
    try:
      self.RunTracked('ml-engine jobs submit {} {} {}'.format(type_, job_id,
                                                              arguments))
      yield
    finally:
      storage_client = storage_api.StorageClient()
      for obj in storage_client.ListBucket(self.BUCKET_REF):
        if obj.name.startswith(job_id + '/'):
          storage_client.DeleteObject(self.BUCKET_REF, obj.name)

  def testJobsSubmitTraining(self):
    job_id = next(e2e_utils.GetResourceNameGenerator(prefix='ml_job',
                                                     delimiter='_'))
    package = self.Resource('tests', 'e2e', 'surface', 'ml_engine', 'testdata',
                            'trainer-0.0.0.tar.gz')

    with self._SubmitJob(
        'training', job_id,
        ('    --staging-bucket {bucket_url} '
         '    --region us-central1 '
         '    --module-name trainer.task '
         '    --packages {package} '
         '    --async').format(bucket_url=self.BUCKET_REF.ToBucketUrl(),
                               package=package)):
      # Cancel immediately so we don't do any real work
      self.RunTracked('ml-engine jobs cancel ' + job_id)
      # Check that the job was created
      self.ClearOutput()
      self.RunTracked('ml-engine jobs describe ' + job_id)
      self.AssertOutputContains('jobId: ' + job_id)

  def testJobsSubmitPrediction(self):
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
    """
    job_id = next(e2e_utils.GetResourceNameGenerator(prefix='ml_job',
                                                     delimiter='_'))
    with self._SubmitJob(
        'prediction', job_id,
        ('  --model={model_id} '
         '  --version={version_id} '
         '  --data-format TEXT '
         '  --input-paths gs://cloud-ml-data/mnist/predict_sample.tensor.json '
         '  --output-path {bucket_url}/{job_id} '
         '  --region us-central1').format(
             job_id=job_id,
             bucket_url=self.BUCKET_REF.ToBucketUrl(),
             model_id=self.MODEL_ID,
             version_id=self.VERSION_ID)):
      # Cancel immediately so we don't do any real work
      self.RunTracked('ml-engine jobs cancel ' + job_id)
      # Check that the job was created
      self.ClearOutput()
      self.RunTracked('ml-engine jobs describe ' + job_id)
      self.AssertOutputContains('jobId: ' + job_id)


if __name__ == '__main__':
  test_case.main()
