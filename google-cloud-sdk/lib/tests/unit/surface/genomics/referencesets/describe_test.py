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

"""Tests for genomics referencesets describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics referencesets describe command."""

  def testDescribe(self):
    refset = self.messages.ReferenceSet(
        assemblyId='GRCh99',
        description='Some description',
        id='abcdefg',
        md5checksum='996cbd07017ad2481cb4a593a8b0a0d2',
        ncbiTaxonId=123,
        referenceIds=['ref1', 'ref2'],
        sourceAccessions=['acc1', 'acc2'],
        sourceUri='uri1')
    self.mocked_client.referencesets.Get.Expect(
        request=self.messages.GenomicsReferencesetsGetRequest(referenceSetId=
                                                              refset.id),
        response=refset)
    self.assertEqual(
        refset, self.RunGenomics(['referencesets', 'describe', refset.id]))
    self.AssertOutputContains(refset.assemblyId)
    self.AssertOutputContains(refset.description)
    self.AssertOutputContains(refset.id)
    self.AssertOutputContains(refset.md5checksum)
    self.AssertOutputContains(str(refset.ncbiTaxonId))
    self.AssertOutputContains(refset.referenceIds[0])
    self.AssertOutputContains(refset.referenceIds[1])
    self.AssertOutputContains(refset.sourceAccessions[0])
    self.AssertOutputContains(refset.sourceAccessions[1])
    self.AssertOutputContains(refset.sourceUri)

  def testDescribeNotExists(self):
    self.mocked_client.referencesets.Get.Expect(
        request=self.messages.GenomicsReferencesetsGetRequest(referenceSetId=
                                                              '1000',),
        exception=self.MakeHttpError(404, 'Reference set not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Reference set not found: 1000'):
      self.RunGenomics(['referencesets', 'describe', '1000'])

if __name__ == '__main__':
  test_case.main()
