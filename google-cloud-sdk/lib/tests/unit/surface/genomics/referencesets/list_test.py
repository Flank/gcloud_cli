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

"""Tests for genomics referencesets list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics referencesets list command."""

  def testReferenceSetsListByAssembly(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(assemblyId='asm1',),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
            self.messages.ReferenceSet(id='1001',
                                       referenceIds=['rset1'],
                                       md5checksum=
                                       '43569a28e2c4af7f3320161c15cf2298',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
        ]))
    self.RunGenomics(
        ['referencesets', 'list', '--assembly-id', 'asm1'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      1001 asm1 acc1,acc2
      """), normalize_space=True)

  def testReferenceSetsListByAccessions(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(accessions=['acc1'],),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
            self.messages.ReferenceSet(id='1001',
                                       referenceIds=['rset1'],
                                       md5checksum=
                                       '43569a28e2c4af7f3320161c15cf2298',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
        ]))
    self.RunGenomics(
        ['referencesets', 'list', '--accessions', 'acc1'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      1001 asm1 acc1,acc2
      """), normalize_space=True)

  def testReferenceSetsListByChecksum(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(
            md5checksums=['274961313498db4141f4387558dae16a'],),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
        ]))
    self.RunGenomics(
        ['referencesets', 'list', '--md5checksums',
         '274961313498db4141f4387558dae16a'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      """), normalize_space=True)

  def testReferenceSetsListByAll(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(
            md5checksums=['274961313498db4141f4387558dae16a'],
            accessions=['acc1'],
            assemblyId='asm1',),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
        ]))
    self.RunGenomics(
        ['referencesets', 'list', '--md5checksums',
         '274961313498db4141f4387558dae16a', '--assembly-id',
         'asm1', '--accessions', 'acc1'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      """), normalize_space=True)

  def testReferenceSetsList_NoArgs(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
        ]))
    self.RunGenomics(
        ['referencesets', 'list'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      """), normalize_space=True)

  def testReferenceSetsList_EmptyList(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(assemblyId='asm99',),
        response=self.messages.SearchReferenceSetsResponse())
    self.RunGenomics(
        ['referencesets', 'list', '--assembly-id', 'asm99'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testReferenceSetsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['referencesets', 'list', '--limit', '-1'])

  def testReferenceSetsList_Limit(self):
    self.mocked_client.referencesets.Search.Expect(
        request=self.messages.SearchReferenceSetsRequest(assemblyId='asm1',
                                                         pageSize=3,),
        response=self.messages.SearchReferenceSetsResponse(referenceSets=[
            self.messages.ReferenceSet(id='1000',
                                       referenceIds=['rset0'],
                                       md5checksum=
                                       '274961313498db4141f4387558dae16a',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
            self.messages.ReferenceSet(id='1001',
                                       referenceIds=['rset1'],
                                       md5checksum=
                                       '43569a28e2c4af7f3320161c15cf2298',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc1', 'acc2']),
            self.messages.ReferenceSet(id='1002',
                                       referenceIds=['rset2'],
                                       md5checksum=
                                       '5ffa92391ccca8f3890144d86aae2b34',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc3']),
            self.messages.ReferenceSet(id='1003',
                                       referenceIds=['rset3'],
                                       md5checksum=
                                       '8e40e028b520127fc9861219f32f44b1',
                                       assemblyId='asm1',
                                       sourceAccessions=['acc4']),
        ]))

    self.RunGenomics(
        ['referencesets', 'list', '--assembly-id', 'asm1', '--limit', '3'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID ASSEMBLY_ID SOURCE_ACCESSIONS
      1000 asm1 acc1,acc2
      1001 asm1 acc1,acc2
      1002 asm1 acc3
      """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
