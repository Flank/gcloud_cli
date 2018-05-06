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

"""Tests for genomics variant list command."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics variants list command."""

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testVariantsListTest(self):
    req = self.messages.SearchVariantsRequest(variantSetIds=['42'],
                                              callSetIds=['42-1'],
                                              referenceName='MT',
                                              start=15,
                                              end=30,
                                              pageSize=50,
                                              maxCalls=500)
    variants = [self.messages.Variant(variantSetId='42',
                                      id='abc123',
                                      names=['foo'],
                                      created=1000000,
                                      referenceName='MT',
                                      start=10,
                                      end=20,
                                      referenceBases='A',
                                      alternateBases=['T', 'C'],
                                      quality=1.0,
                                      filter=['PASS'],),
                self.messages.Variant(variantSetId='42',
                                      id='abc124',
                                      names=['bar'],
                                      created=1000000,
                                      referenceName='MT',
                                      start=11,
                                      end=21,
                                      referenceBases='T',
                                      alternateBases=['A', 'G'],
                                      quality=1.0,
                                      filter=['PASS'],)]
    resp = self.messages.SearchVariantsResponse(variants=variants)
    self.mocked_client.variants.Search.Expect(request=req, response=resp)

    self.assertEqual(variants,
                      list(self.RunGenomics(
                          ['variants', 'list',
                           '--variant-set-id', '42',
                           '--call-set-ids', '42-1',
                           '--reference-name', 'MT',
                           '--start', '15L',
                           '--end', '30L',
                           '--limit', '50',
                           '--limit-calls', '500'])))

  def testVariantsList_EmptyList(self):
    self.mocked_client.variants.Search.Expect(
        request=self.messages.SearchVariantsRequest(variantSetIds=['42'],
                                                    callSetIds=['42-1'],
                                                    referenceName='empty',
                                                    pageSize=512),
        response=self.messages.SearchVariantsResponse())
    self.assertEqual([],
                     list(self.RunGenomics(['variants', 'list',
                                            '--variant-set-id', '42',
                                            '--call-set-ids', '42-1',
                                            '--reference-name', 'empty'])))

  def testVariantsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['variants', 'list', '--reference-name', 'MT', '--variant-set-id',
           '42', '--limit', '-1'])

  def testVariantsList_LimitCalls_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit-calls: Value must be greater than or equal to 1; '
        'received: -1'):
      self.RunGenomics(
          ['variants', 'list', '--reference-name', 'MT', '--variant-set-id',
           '42', '--limit-calls', '-1'])

  def testInaccessibleVariantSet(self):
    self.mocked_client.variants.Search.Expect(
        request=self.messages.SearchVariantsRequest(callSetIds=[],
                                                    variantSetIds=['42'],
                                                    pageSize=512,
                                                    referenceName='MT'),
        exception=http_error.MakeHttpError(
            403, 'Permission denied; need GET permission'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied; need GET permission'):
      list(self.RunGenomics(['variants', 'list', '--variant-set-id', '42',
                             '--reference-name', 'MT']))

  def testNoVariantSetOrCallSet(self):
    self.mocked_client.variants.Search.Expect(
        request=self.messages.SearchVariantsRequest(referenceName='MT',
                                                    pageSize=512),
        exception=http_error.MakeHttpError(
            400, 'Must specify variantSetIds or callSetIds'))
    with self.AssertRaisesHttpExceptionMatches(
        'Must specify --variant-set-id or --call-set-ids'):
      list(self.RunGenomics(['variants', 'list', '--reference-name', 'MT']))


if __name__ == '__main__':
  test_case.main()
