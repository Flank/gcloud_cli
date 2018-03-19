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
"""Tests for genomics tests variantsets update command."""

import textwrap
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class UpdateTest(base.GenomicsUnitTest):
  """Unit tests for genomics variantsets update command."""

  def testVariantsetsUpdate(self):
    self.mocked_client.variantsets.Patch.Expect(
        request=self.messages.GenomicsVariantsetsPatchRequest(
            updateMask='name,description',
            variantSet=self.messages.VariantSet(name='name-new',
                                                description='desc-new'),
            variantSetId='1000',),
        response=self.messages.VariantSet(id='1000',
                                          name='name-new',
                                          description='desc-new'))
    self.RunGenomics(['variantsets', 'update', '1000', '--name', 'name-new',
                      '--description', 'desc-new'])
    self.AssertErrEquals(textwrap.dedent("""\
      Updated variant set 1000, name: name-new, description: desc-new
      """))

  def testVariantsetsUpdateNotExists(self):
    self.mocked_client.variantsets.Patch.Expect(
        request=self.messages.GenomicsVariantsetsPatchRequest(
            updateMask='name',
            variantSet=self.messages.VariantSet(name='name-new'),
            variantSetId='1000',),
        exception=self.MakeHttpError(404, 'Variant set not found: 1000'))
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 'Variant set not found: 1000'):
      self.RunGenomics(['variantsets', 'update', '1000', '--name', 'name-new'])


if __name__ == '__main__':
  test_case.main()
