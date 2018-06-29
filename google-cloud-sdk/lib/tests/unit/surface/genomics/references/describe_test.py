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

"""Tests for genomics references describe command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics references describe command."""

  def testDescribe(self):
    ref = self.messages.Reference(
        id='abcdefg',
        length=1000000,
        md5checksum='996cbd07017ad2481cb4a593a8b0a0d2',
        name='chr1',
        ncbiTaxonId=123,
        sourceAccessions=['acc1', 'acc2'],
        sourceUri='uri1')
    self.mocked_client.references.Get.Expect(
        request=self.messages.GenomicsReferencesGetRequest(referenceId=ref.id),
        response=ref)
    self.assertEqual(ref, self.RunGenomics(['references', 'describe', ref.id]))

    self.AssertOutputContains(ref.id)
    self.AssertOutputContains(str(ref.length))
    self.AssertOutputContains(ref.md5checksum)
    self.AssertOutputContains(ref.name)
    self.AssertOutputContains(str(ref.ncbiTaxonId))
    self.AssertOutputContains(ref.sourceAccessions[0])
    self.AssertOutputContains(ref.sourceAccessions[1])
    self.AssertOutputContains(ref.sourceUri)

  def testDescribeNotExists(self):
    self.mocked_client.references.Get.Expect(
        request=self.messages.GenomicsReferencesGetRequest(referenceId='1000',),
        exception=self.MakeHttpError(404, 'Reference not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Reference not found: 1000'):
      self.RunGenomics(['references', 'describe', '1000'])

if __name__ == '__main__':
  test_case.main()
