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

"""Integration test for 'genomics datasets' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DatasetsIntegrationTest(base.GenomicsIntegrationTest):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def CleanUpDatasets(self, dataset_ids):
    failed_cleanup_list = []
    for delete_id in dataset_ids:
      try:
        self.RunGenomics(['datasets', 'delete', delete_id])
      # pylint:disable=bare-except
      except:
        failed_cleanup_list.append(delete_id)

    return failed_cleanup_list

  def testCreateUpdateDescribe(self):
    name = next(e2e_utils.GetResourceNameGenerator(
        prefix='genomics-integration'))
    result = self.RunGenomics(['datasets', 'create', '--name', name])

    try:
      dataset_result = self.RunGenomics(['datasets', 'describe', result.id])
      self.assertIsNotNone(
          arg_parsers.Datetime.Parse(dataset_result.createTime))
      self.assertEqual(result.id, dataset_result.id)
      self.assertEqual(name, dataset_result.name)
      self.assertEqual(self.Project(), dataset_result.projectId)

      # Update the dataset
      self.RunGenomics(['datasets', 'update', result.id,
                        '--name', name + '-updated'])

      dataset_result = self.RunGenomics(['datasets', 'describe', result.id])
      self.assertIsNotNone(
          arg_parsers.Datetime.Parse(dataset_result.createTime))
      self.assertEqual(result.id, dataset_result.id)
      self.assertEqual(name + '-updated', dataset_result.name)
      self.assertEqual(self.Project(), dataset_result.projectId)

    finally:
      # Clean up
      failed_cleanup_list = self.CleanUpDatasets([result.id])

    self.assertEqual([], failed_cleanup_list)

  def testDatasetCreateListDeleteRestore(self):
    # Generate a list of dataset names
    new_dataset_names = set(e2e_utils.GetResourceNameGenerator(
        prefix='genomics-integration', sequence_start=0, count=3))

    # Create the datasets
    result_dataset_ids = []
    for name in new_dataset_names:
      try:
        result = self.RunGenomics(['datasets', 'create', '--name', name])
        result_dataset_ids.append(result.id)
      # pylint:disable=broad-except
      except Exception as ex:
        log.Print('Failed to create dataset: {0}'.format(name))
        log.Print(ex)

        failed_cleanup_list = self.CleanupDatasets(result_dataset_ids)
        self.assertEqual([], failed_cleanup_list)
        return

    try:
      # List the datasets
      results = self.RunGenomics(
          ['datasets', 'list'])

      # Get the names
      result_dataset_names = set([dataset.name for dataset in results])

      self.assertTrue(
          new_dataset_names <= result_dataset_names,
          'Result dataset names ({0}) does not include all newly created '
          'dataset names ({1})'.format(result_dataset_names, new_dataset_names))

      # Remove a dataset
      remove_id = str(result_dataset_ids[0])
      self.RunGenomics(['datasets', 'delete', remove_id])

      # Verify it is gone
      results = self.RunGenomics(
          ['datasets', 'list'])
      self.assertFalse(remove_id in [result.id for result in results])

      # Restore the dataset
      self.RunGenomics(['datasets', 'restore', remove_id])

      # Verify it is back
      results = self.RunGenomics(
          ['datasets', 'list'])
      self.assertTrue(remove_id in [result.id for result in results])

    finally:
      failed_cleanup_list = self.CleanUpDatasets(result_dataset_ids)

    self.assertEqual([], failed_cleanup_list)


if __name__ == '__main__':
  test_case.main()
