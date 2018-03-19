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

"""Integration test for 'genomics referenceset' commands."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base

# GRCh38 ReferenceSet assemblyID and md5.
ASSEMBLY_ID = 'GRCh38'
MD5 = '996cbd07017ad2481cb4a593a8b0a0d2'


class ReferenceSetsIntegrationTest(base.GenomicsIntegrationTest):
  """Integration test for genomics referencesets.
  """

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListReferenceSets(self):
    results = list(self.RunGenomics(['referencesets', 'list', '--md5checksums',
                                     MD5]))
    self.assertEqual(1, len(results))
    want_refset = results[0]
    self.assertEqual(ASSEMBLY_ID, want_refset.assemblyId)

    got_refset = self.RunGenomics(['referencesets', 'describe', want_refset.id])
    self.assertEqual(want_refset, got_refset)

    # Check the console output.
    properties.VALUES.core.user_output_enabled.Set(True)

    self.RunGenomics(['referencesets', 'list', '--md5checksums', MD5])
    self.AssertOutputContains(want_refset.id)
    self.ClearOutput()

    self.RunGenomics(['referencesets', 'describe', want_refset.id])
    self.AssertOutputContains(want_refset.id)
    self.AssertOutputContains(want_refset.md5checksum)

  def testListReferenceSetsNoArgs(self):
    results = list(self.RunGenomics(['referencesets', 'list']))
    self.assertTrue(len(results))

if __name__ == '__main__':
  test_case.main()
