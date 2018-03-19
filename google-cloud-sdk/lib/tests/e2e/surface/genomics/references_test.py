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

"""Integration test for 'genomics references' commands."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base

# ReferenceSet Id for GRCh38
GRCH38_REFERENCE_SET_ID = 'EMud_c37lKPXTQ'


class ReferencesIntegrationTest(base.GenomicsIntegrationTest):
  """Integration test for genomics references.

  """

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListAndDescribeReferences(self):
    results = list(self.RunGenomics(['references', 'list', '--reference-set-id',
                                     GRCH38_REFERENCE_SET_ID]))
    self.assertTrue(len(results))
    want_ref = results[0]

    got_ref = self.RunGenomics(['references', 'describe', want_ref.id])
    self.assertEqual(want_ref, got_ref)

    # Check the console output.
    properties.VALUES.core.user_output_enabled.Set(True)

    self.RunGenomics(['references', 'list', '--md5checksums',
                      want_ref.md5checksum])
    self.AssertOutputContains(want_ref.id)
    self.ClearOutput()

    self.RunGenomics(['references', 'describe', want_ref.id])
    self.AssertOutputContains(want_ref.id)
    self.AssertOutputContains(want_ref.md5checksum)

  def testListReferences_NoArgs(self):
    results = list(self.RunGenomics(['references', 'list']))
    self.assertTrue(len(results))


if __name__ == '__main__':
  test_case.main()
