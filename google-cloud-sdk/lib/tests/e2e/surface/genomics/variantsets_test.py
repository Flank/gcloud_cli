# -*- coding: utf-8 -*- #
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

"""Integration test for the 'variantsets create/delete' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.genomics import base


class VariantSetsIntegrationTest(base.GenomicsIntegrationTest):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testCreateGetDelete(self):
    try:
      # create a dataset to contain the variantset
      name = next(e2e_utils.GetResourceNameGenerator(
          prefix='genomics-integration'))
      dataset = self.RunGenomics(['datasets', 'create', '--name', name])

      # create a variantset
      variantset = self.RunGenomics(
          ['variantsets', 'create',
           '--name', 'foo',
           '--dataset-id', dataset.id])

      # check we see it
      variantset_echo = self.RunGenomics(
          ['variantsets', 'describe', variantset.id])

      self.assertEqual(variantset.datasetId, variantset_echo.datasetId)
      self.assertEqual(variantset.name, variantset_echo.name)

      # delete it
      self.RunGenomics(['variantsets', 'delete', variantset.id])

    finally:
      # Clean up
      failed_cleanup_list = self.CleanUpDatasets([dataset.id])

    self.assertEqual([], failed_cleanup_list)


if __name__ == '__main__':
  test_case.main()
