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

"""Tests for genomics variants describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics variants describe command."""

  def testDescribe(self):
    variant_id = 'abc123'
    variant = self.messages.Variant(variantSetId='42',
                                    id=variant_id,
                                    names=['variant_name0', 'variant_name1'],
                                    created=1000000,
                                    referenceName='reference_name0',
                                    start=10,
                                    end=20,
                                    referenceBases='A',
                                    alternateBases=['T', 'C'],
                                    quality=1.0,
                                    filter=['PASS'],)
    self.mocked_client.variants.Get.Expect(
        request=self.messages.GenomicsVariantsGetRequest(variantId=variant_id),
        response=variant)
    self.assertEqual(variant, self.RunGenomics(['variants', 'describe',
                                                variant_id]))

  def testDescribeNotExists(self):
    variant_id = 'abc123'
    self.mocked_client.variants.Get.Expect(
        request=self.messages.GenomicsVariantsGetRequest(variantId=variant_id),
        exception=self.MakeHttpError(404, 'Variant not found: ' + variant_id))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Variant not found: ' + variant_id):
      self.RunGenomics(['variants', 'describe', variant_id])


if __name__ == '__main__':
  test_case.main()
