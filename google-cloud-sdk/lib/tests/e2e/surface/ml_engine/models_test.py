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
"""e2e tests for ml-engine models command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class MlPlatformModelsIntegrationTest(e2e_base.WithServiceAuth):
  """e2e tests for ml-engine models command group."""

  _STAGING_BUCKET_URL = 'gs://cloud-sdk-integration-testing-ml'

  def SetUp(self):
    self.id_gen = e2e_utils.GetResourceNameGenerator(
        prefix='ml_platform', delimiter='_')
    self.delete_retryer = retry.Retryer(max_retrials=3,
                                        exponential_sleep_multiplier=2)

  @contextlib.contextmanager
  def _CreateModel(self):
    model_id = next(self.id_gen)
    created = False
    try:
      self.Run('ml-engine models create {}'.format(model_id))
      created = True
      yield model_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, ('ml-engine models delete {}'.format(model_id),))

  @contextlib.contextmanager
  def _CreateVersion(self, model_id, other_args=''):
    version_id = next(self.id_gen)
    created = False
    try:
      self.Run('ml-engine versions create --model {} {} {}'.format(
          model_id, version_id, other_args))
      created = True
      yield version_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, ('ml-engine versions delete --model {} {}'.format(
                model_id, version_id),))

  @test_case.Filters.skip('Leaking resources', 'b/37768081')
  def testMainOps(self):
    with self._CreateModel() as model:
      # Confirm the model exists
      self.ClearOutput()
      self.Run('ml-engine models list')
      self.AssertOutputContains(model)

      # Create a version within the model
      savedmodel_dir = self.Resource('tests', 'e2e', 'surface', 'ml_engine',
                                     'testdata', 'savedmodel')
      create_version_args = (
          '--origin {model_dir} '
          '--staging-bucket {staging_bucket} '
          '--description "My Description"').format(
              model_dir=savedmodel_dir, staging_bucket=self._STAGING_BUCKET_URL)
      with self._CreateVersion(model, create_version_args) as version:
        # Confirm the version exists
        self.ClearOutput()
        self.Run('ml-engine versions list --model {0}'.format(model))
        self.AssertOutputContains(version)

        # Set the version as default; confirm it's shown on the model
        self.Run('ml-engine versions set-default --model {0} {1}'.format(
            model, version))
        self.ClearOutput()
        self.Run('ml-engine models describe {0}'.format(model))
        self.AssertOutputContains(model)
        self.AssertOutputContains(version)
        self.Run('ml-engine models get-iam-policy {0}'.format(model))
      self.ClearOutput()
      self.AssertOutputNotContains(version)
    self.ClearOutput()
    self.Run('ml-engine models list')
    self.AssertOutputNotContains(model)


if __name__ == '__main__':
  test_case.main()
