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
"""e2e tests for ai-platform models command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import test_case


@parameterized.parameters('ml-engine', 'ai-platform')
class MlPlatformModelsIntegrationTest(e2e_base.WithServiceAuth):
  """e2e tests for ai-platform models command group."""

  _STAGING_BUCKET_URL = 'gs://cloud-sdk-integration-testing-ml'

  def SetUp(self):
    self.id_gen = e2e_utils.GetResourceNameGenerator(
        prefix='ml_platform', delimiter='_')
    self.delete_retryer = retry.Retryer(max_retrials=3,
                                        exponential_sleep_multiplier=2)

  @contextlib.contextmanager
  def _CreateModel(self, module_name):
    model_id = next(self.id_gen)
    created = False
    try:
      self.Run('{} models create {}'.format(module_name, model_id))
      created = True
      yield model_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, ('{} models delete {}'.format(module_name, model_id),))

  @contextlib.contextmanager
  def _CreateVersion(self, model_id, module_name, other_args=''):
    version_id = next(self.id_gen)
    created = False
    try:
      self.Run('{} versions create --model {} {} {}'.format(
          module_name, model_id, version_id, other_args))
      created = True
      yield version_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(
            self.Run, ('{} versions delete --model {} {}'.format(
                module_name, model_id, version_id),))

  def testMainOps(self, module_name):
    with self._CreateModel(module_name) as model:
      # Confirm the model exists
      self.ClearOutput()
      self.Run('{} models list'.format(module_name))
      self.AssertOutputContains(model)

      # Create a version within the model
      savedmodel_dir = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                     'testdata', 'savedmodel')
      create_version_args = (
          '--origin {model_dir} '
          '--staging-bucket {staging_bucket} '
          '--description "My Description"').format(
              model_dir=savedmodel_dir, staging_bucket=self._STAGING_BUCKET_URL)
      with self._CreateVersion(model, module_name,
                               create_version_args) as version:
        # Confirm the version exists
        self.ClearOutput()
        self.Run('{} versions list --model {}'.format(module_name, model))
        self.AssertOutputContains(version)

        # Set the version as default; confirm it's shown on the model
        self.Run('{} versions set-default --model {} {}'.format(
            module_name, model, version))
        self.ClearOutput()
        self.Run('{} models describe {}'.format(module_name, model))
        self.AssertOutputContains(model)
        self.AssertOutputContains(version)
        self.Run('{} models get-iam-policy {}'.format(module_name, model))
      self.ClearOutput()
      self.AssertOutputNotContains(version)
    self.ClearOutput()
    self.Run('{} models list'.format(module_name))
    self.AssertOutputNotContains(model)


if __name__ == '__main__':
  test_case.main()
