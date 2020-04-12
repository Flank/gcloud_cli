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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import test_case


class MlPlatformModelsIntegrationTest(e2e_base.WithServiceAuth):
  """Base class for AI Platform models integration test."""

  _STAGING_BUCKET_URL = 'gs://cloud-sdk-integration-testing-ml'

  def SetUp(self):
    self.id_gen = e2e_utils.GetResourceNameGenerator(
        prefix='ml_platform', delimiter='_')
    self.delete_retryer = retry.Retryer(max_retrials=3,
                                        exponential_sleep_multiplier=2)

  @contextlib.contextmanager
  def _CreateModel(self, module_name, region=None):
    model_id = next(self.id_gen)
    created = False
    create_model_cmd = '{} models create {}'.format(module_name, model_id)
    delete_model_cmd = '{} models delete {}'.format(module_name, model_id)
    if region is not None:
      region_flag = ' --region {}'.format(region)
      create_model_cmd = create_model_cmd + region_flag
      delete_model_cmd = delete_model_cmd + region_flag
    try:
      self.Run(create_model_cmd)
      created = True
      yield model_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(self.Run, (delete_model_cmd,))

  @contextlib.contextmanager
  def _CreateVersion(self, model_id, module_name, region=None, other_args=''):
    version_id = next(self.id_gen)
    created = False
    create_version_cmd = '{} versions create --model {} {} {}'.format(
        module_name, model_id, version_id, other_args)
    delete_version_cmd = '{} versions delete --model {} {}'.format(
        module_name, model_id, version_id)
    if region is not None:
      region_flag = ' --region {}'.format(region)
      create_version_cmd = create_version_cmd + region_flag
      delete_version_cmd = delete_version_cmd + region_flag
    try:
      self.Run(create_version_cmd)
      created = True
      yield version_id
    finally:
      if created:
        self.delete_retryer.RetryOnException(self.Run, (delete_version_cmd,))


@parameterized.parameters('ml-engine', 'ai-platform')
class MlPlatformModelsIntegrationTestGA(MlPlatformModelsIntegrationTest,
                                        parameterized.TestCase):
  """e2e tests for ai-platform models command group."""

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
      with self._CreateVersion(
          model, module_name, other_args=create_version_args) as version:
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


@parameterized.parameters('ml-engine', 'ai-platform')
class MlPlatformModelsIntegrationTestBeta(MlPlatformModelsIntegrationTest,
                                          parameterized.TestCase):
  """e2e tests for ai-platform beta models command group."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testRegionalModelVersion(self, module_name):
    region = 'europe-west4'
    with self._CreateModel(module_name, region=region) as model:
      # Confirm the model exists
      self.ClearOutput()
      self.Run('{} models list --region {}'.format(module_name, region))
      self.AssertOutputContains(model)

      # Create a version within the model
      savedmodel_dir = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                     'testdata', 'savedmodel')
      # TODO(b/151400378) rely on default for --machine-type.
      create_version_args = (
          '--origin {model_dir} --staging-bucket {staging_bucket} '
          '--description "My Description" --machine-type n1-standard-2 '
          '--runtime-version=1.14'
      ).format(
          model_dir=savedmodel_dir, staging_bucket=self._STAGING_BUCKET_URL)
      with self._CreateVersion(
          model, module_name, region=region,
          other_args=create_version_args) as version:
        # Confirm the version exists
        self.ClearOutput()
        self.Run('{} versions list --model {} --region {}'.format(
            module_name, model, region))
        self.AssertOutputContains(version)

        # Set the version as default; confirm it's shown on the model
        self.Run('{} versions set-default --region {} --model {} {}'.format(
            module_name, region, model, version))
        self.ClearOutput()
        self.Run('{} models describe {} --region {}'.format(
            module_name, model, region))
        self.AssertOutputContains(model)
        self.AssertOutputContains(version)
        self.Run('{} models get-iam-policy {} --region {}'.format(
            module_name, model, region))
      self.ClearOutput()
      self.AssertOutputNotContains(version)
    self.ClearOutput()
    self.Run('{} models list --region {}'.format(module_name, region))
    self.AssertOutputNotContains(model)


if __name__ == '__main__':
  test_case.main()
