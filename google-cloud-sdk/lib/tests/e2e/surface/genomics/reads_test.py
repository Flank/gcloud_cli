# -*- coding: utf-8 -*- #
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

"""Integration test for 'genomics reads' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base

# 1000 genomes read group set ID for individual 'HG02166'.
RGSET_ID_1KG = 'CMvnhpKTFhDt6uGJ6YSOLQ'


class ReadsIntegrationTest(base.GenomicsIntegrationTest):
  """Integration test for genomics reads.

  This test is currently limited to read-only methods against known existing
  datasets. As of 10/13/15, creating a new read group set would require
  waiting for a long asynchoronous operation to complete.
  """

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListReads(self):
    reads = list(self.RunGenomics(['reads', 'list', RGSET_ID_1KG,
                                   '--limit', '3']))
    self.assertEqual(3, len(reads))
    for read in reads:
      self.assertTrue(read.alignedSequence)

  def testListUnmappedReads(self):
    reads = list(self.RunGenomics(['reads', 'list', RGSET_ID_1KG,
                                   '--reference-name', '*', '--limit', '2']))
    self.assertEqual(2, len(reads))
    for read in reads:
      self.assertIsNone(read.alignment)

  def testListReadsByReference(self):
    reads = list(self.RunGenomics(['reads', 'list', RGSET_ID_1KG,
                                   '--reference-name', 'X', '--limit', '4']))
    self.assertEqual(4, len(reads))
    for read in reads:
      self.assertIsNotNone(read.alignment)
      self.assertIsNotNone(read.alignment.position)
      self.assertEqual('X', read.alignment.position.referenceName)

  def testListReadsByRange(self):
    target = 20000
    reads = list(self.RunGenomics(['reads', 'list', RGSET_ID_1KG,
                                   '--reference-name', '1',
                                   '--start', str(target),
                                   '--end', str(target + 1),
                                   # Use JSON formatting to ensure we fetch all
                                   # fields. By default we use a field mask.
                                   '--format', 'json'
                                  ]))

    for read in reads:
      self.assertEqual(RGSET_ID_1KG, read.readGroupSetId)
      self.assertIsNotNone(read.alignment)
      self.assertIsNotNone(read.alignment.position)
      self.assertEqual('1', read.alignment.position.referenceName)

      # For ease of test maintenance, we're just making a conservative (erring
      # on the side of 'too large') approximation of the alignment length. Some
      # of these cigar operations will not actually contribute to the alignment.
      got_start = read.alignment.position.position
      approx_len = 0
      for op in read.alignment.cigar:
        approx_len += op.operationLength
      # We do some rough assertions that the start position is where we expect,
      # to avoid hardcoding more data in this test than necessary.
      self.assertTrue(got_start <= target)
      self.assertTrue(target - approx_len < got_start)

if __name__ == '__main__':
  test_case.main()
