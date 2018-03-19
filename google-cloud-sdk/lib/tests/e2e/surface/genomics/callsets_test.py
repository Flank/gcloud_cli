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
"""Integration test for 'genomics callsets' commands."""

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.genomics import base

# Regular expression to match a timestamp such as: '2015-07-08T21:26:16.000Z'
TIMESTAMP_RE = '[0-9]*'


class CallsetsIntegrationTest(base.GenomicsIntegrationTest):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)
    try:
      dataset_name = e2e_utils.GetResourceNameGenerator(
          prefix='callsetstest').next()
      self.dataset = self.RunGenomics(['datasets', 'create', '--name',
                                       dataset_name])
      variantset = self.RunGenomics(
          ['variantsets', 'create',
           '--name', 'foo',
           '--dataset-id', self.dataset.id])
      self.vs_id = variantset.id
    except Exception as e:
      self.CleanUpDatasetAndVariantset()
      raise e

  def CleanUpDatasetAndVariantset(self):
    # This command will delete the variant set associated with the dataset
    # automatically, if it exists.
    if self.dataset:
      self.RunGenomics(['datasets', 'delete', self.dataset.id])

  def TearDown(self):
    self.CleanUpDatasetAndVariantset()

  def CleanUpCallsets(self, callset_ids):
    failed_cleanup_list = []
    for delete_id in callset_ids:
      try:
        self.RunGenomics(['callsets', 'delete', delete_id])
      # pylint:disable=bare-except
      except:
        failed_cleanup_list.append(delete_id)

    return failed_cleanup_list

  def testCreateUpdateDescribe(self):
    result = self.RunGenomics(['callsets', 'create', '--name', 'cs-name',
                               '--variant-set-id', self.vs_id])
    try:
      # Check the output
      properties.VALUES.core.user_output_enabled.Set(True)
      call_set = self.RunGenomics(['callsets', 'describe', result.id])
      # This field is currently a mess - it seems to get set to an empty
      # array about 50% of the time, which causes the test to fail.
      call_set.info = None
      self.assertEquals(
          call_set,
          self.messages.CallSet(
              created=call_set.created,
              id=result.id,
              name='cs-name',
              sampleId='cs-name',
              variantSetIds=[self.vs_id]))
      self.AssertOutputContains('cs-name')
      self.AssertOutputContains(result.id)
      self.ClearOutput()

      # Update the callset
      properties.VALUES.core.user_output_enabled.Set(False)
      self.RunGenomics([
          'callsets', 'update', result.id, '--name', 'new-name'])

      # Check the output
      properties.VALUES.core.user_output_enabled.Set(True)
      call_set = self.RunGenomics(['callsets', 'describe', result.id])
      # This field is currently a mess - it seems to get set to an empty
      # array about 50% of the time, which causes the test to fail.
      call_set.info = None
      self.assertEquals(
          call_set,
          self.messages.CallSet(
              created=call_set.created,
              id=result.id,
              name='new-name',
              sampleId='new-name',
              variantSetIds=[self.vs_id]))
      self.AssertOutputContains('new-name')
      self.AssertOutputNotContains('cs-name')
      self.AssertOutputContains(result.id)

    finally:
      # Clean up
      failed_cleanup_list = self.CleanUpCallsets([result.id])

    self.assertEqual([], failed_cleanup_list)

  def testCallsetCreateListDelete(self):
    # Generate a list of callset names
    new_callset_names = set(e2e_utils.GetResourceNameGenerator(
        prefix='genomics-integration', sequence_start=0, count=3))

    # Create the callsets
    result_callset_ids = []
    for name in new_callset_names:
      try:
        result = self.RunGenomics(['callsets', 'create', '--name', name,
                                   '--variant-set-id', self.vs_id])
        result_callset_ids.append(result.id)
      # pylint:disable=broad-except
      except Exception as ex:
        log.Print('Failed to create callset: {0}'.format(name))
        log.Print(ex)

        failed_cleanup_list = self.CleanUpCallsets(result_callset_ids)
        self.assertEqual([], failed_cleanup_list)
        return

    try:
      # List the callsets
      results = self.RunGenomics(
          ['callsets', 'list', self.vs_id])

      # Get the names
      result_callset_names = set([callset.name for callset in results])

      self.assertTrue(
          new_callset_names <= result_callset_names,
          'Result callset names ({0}) does not include all newly created '
          'callset names ({1})'.format(result_callset_names, new_callset_names))

      # Remove a callset
      remove_id = str(result_callset_ids[0])
      self.RunGenomics(['callsets', 'delete', remove_id])

      # Verify it is gone
      results = self.RunGenomics(
          ['callsets', 'list', self.vs_id])
      self.assertFalse(remove_id in [result.id for result in results])
    finally:
      self.CleanUpCallsets(result_callset_ids)


if __name__ == '__main__':
  test_case.main()
