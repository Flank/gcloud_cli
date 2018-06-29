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

"""Tests for genomics variants update command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class UpdateTest(base.GenomicsUnitTest):
  """Unit tests for genomics variants update command."""

  def testUpdate(self):
    variant_id = 'abc123'
    variant = self.messages.Variant(names=['foo', 'bar'])
    self.mocked_client.variants.Patch.Expect(
        request=self.messages.GenomicsVariantsPatchRequest(updateMask='names',
                                                           variant=variant,
                                                           variantId=
                                                           variant_id),
        response=variant)
    self.assertEqual(variant, self.RunGenomics(['variants', 'update',
                                                variant_id,
                                                '--names',
                                                'foo,bar']))

  def testUpdateNotExists(self):
    variant_id = 'abc123'
    self.mocked_client.variants.Patch.Expect(
        request=self.messages.GenomicsVariantsPatchRequest(
            updateMask='names',
            variant=self.messages.Variant(names=['foo', 'bar']),
            variantId=variant_id),
        exception=self.MakeHttpError(404, 'Variant not found: ' + variant_id))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Variant not found: ' + variant_id):
      self.RunGenomics(['variants', 'update', variant_id, '--names', 'foo,bar'])


if __name__ == '__main__':
  test_case.main()
