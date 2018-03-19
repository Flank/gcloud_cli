# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Integration test for 'genomics readgroupsets' commands."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base

# 1000 genomes dataset ID.
DATASET_ID_1KG = '10473108253681171589'


class ReadGroupSetsIntegrationTest(base.GenomicsIntegrationTest):
  """Integration test for genomics readgroupsets.

  This test is currently limited to read-only methods against known existing
  datasets. As of 10/13/15, creating a new read group set would require waiting
  for a long asynchoronous operation to complete.
  """

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListReadGroupSets(self):
    results = list(self.RunGenomics(['readgroupsets', 'list', DATASET_ID_1KG,
                                     '--limit', '5']))
    self.assertEqual(5, len(results))

  def testListByNameAndDescribeReadGroupSet(self):
    # List in YAML format to ensure that all fields are returned, this is needed
    # for comparison against the 'describe' result below.
    want_name = 'HG02166'
    results = list(self.RunGenomics(['readgroupsets', 'list', DATASET_ID_1KG,
                                     '--name', want_name, '--format', 'yaml']))
    self.assertEqual(1, len(results))
    self.assertEqual(want_name, results[0].name)

    want_rgset = results[0]
    got_rgset = self.RunGenomics(['readgroupsets', 'describe', want_rgset.id])
    self.assertEqual(want_rgset, got_rgset)

    # Check the console output.
    properties.VALUES.core.user_output_enabled.Set(True)

    self.RunGenomics(['readgroupsets', 'list', DATASET_ID_1KG,
                      '--name', want_name])
    self.AssertOutputContains(want_name)
    self.ClearOutput()

    self.RunGenomics(['readgroupsets', 'describe', want_rgset.id])
    self.AssertOutputContains(want_rgset.id)
    self.AssertOutputContains(want_rgset.name)

if __name__ == '__main__':
  test_case.main()
