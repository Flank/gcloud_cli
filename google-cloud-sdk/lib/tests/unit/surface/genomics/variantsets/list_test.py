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

"""Tests for genomics variantsets list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics variantsets list command."""

  def testVariantSetsList(self):
    self.mocked_client.variantsets.Search.Expect(
        request=self.messages.SearchVariantSetsRequest(datasetIds=['123'],),
        response=self.messages.SearchVariantSetsResponse(variantSets=[
            self.messages.VariantSet(datasetId='123',
                                     id='1000',
                                     name='1000name',
                                     description='1000description'),
            self.messages.VariantSet(datasetId='123',
                                     id='1001',
                                     name='1001name',
                                     description='1001description'),
        ]))
    self.RunGenomics(
        ['variantsets', 'list', '123'])
    self.AssertOutputEquals(
        textwrap.dedent("""\
      ID NAME DESCRIPTION
      1000 1000name 1000description
      1001 1001name 1001description
      """),
        normalize_space=True)

  def testVariantSetsList_EmptyList(self):
    self.mocked_client.variantsets.Search.Expect(
        request=self.messages.SearchVariantSetsRequest(datasetIds=['123'],),
        response=self.messages.SearchVariantSetsResponse())
    self.RunGenomics(
        ['variantsets', 'list', '123'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testVariantSetsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['variantsets', 'list', '123', '--limit', '-1'])

  def testVariantSetsList_Limit(self):
    self.mocked_client.variantsets.Search.Expect(
        request=self.messages.SearchVariantSetsRequest(datasetIds=['123'],
                                                       pageSize=3,),
        response=self.messages.SearchVariantSetsResponse(variantSets=[
            self.messages.VariantSet(datasetId='123',
                                     id='1000',
                                     name='1000name',
                                     description='1000description'),
            self.messages.VariantSet(datasetId='123',
                                     id='1001',
                                     name='1001name',
                                     description='1001description'),
            self.messages.VariantSet(datasetId='123',
                                     id='1002',
                                     name='1002name',
                                     description='1002description'),
            self.messages.VariantSet(datasetId='123',
                                     id='1003',
                                     name='1003name',
                                     description='1003description'),
        ]))

    self.RunGenomics(
        ['variantsets', 'list', '123',
         '--limit', '3'])
    self.AssertOutputEquals(
        textwrap.dedent("""\
      ID NAME DESCRIPTION
      1000 1000name 1000description
      1001 1001name 1001description
      1002 1002name 1002description
      """),
        normalize_space=True)

  def testNonexistentDataset(self):
    self.mocked_client.variantsets.Search.Expect(
        request=self.messages.SearchVariantSetsRequest(datasetIds=['123'],),
        exception=http_error.MakeHttpError(404, 'Dataset not found: "123"'))

    with self.AssertRaisesHttpExceptionMatches('Dataset not found: "123"'):
      self.RunGenomics(['variantsets', 'list', '123'])

if __name__ == '__main__':
  test_case.main()
