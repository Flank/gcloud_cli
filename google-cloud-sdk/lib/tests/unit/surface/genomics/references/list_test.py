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

"""Tests for genomics references list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics references list command."""

  def testReferencesList(self):
    self.mocked_client.references.Search.Expect(
        request=self.messages.SearchReferencesRequest(referenceSetId='GRCh38',),
        response=self.messages.SearchReferencesResponse(references=[
            self.messages.Reference(id='1000',
                                    name='ref0',
                                    length=2000,
                                    sourceUri='uri0',
                                    sourceAccessions=['acc0', 'acc1']),
            self.messages.Reference(id='1001',
                                    name='ref1',
                                    length=2000,
                                    sourceUri='uri1',
                                    sourceAccessions=[]),
        ]))
    self.RunGenomics(
        ['references', 'list', '--reference-set-id', 'GRCh38'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID NAME LENGTH SOURCE_URI ACCESSIONS
      1000 ref0 2000 uri0 acc0,acc1
      1001 ref1 2000 uri1
      """), normalize_space=True)

  def testReferencesList_NoArgs(self):
    self.mocked_client.references.Search.Expect(
        request=self.messages.SearchReferencesRequest(),
        response=self.messages.SearchReferencesResponse(references=[
            self.messages.Reference(id='1000',
                                    name='ref0',
                                    length=2000,
                                    sourceUri='uri0',
                                    sourceAccessions=[]),
            self.messages.Reference(id='1001',
                                    name='ref1',
                                    length=2000,
                                    sourceUri='uri1',
                                    sourceAccessions=[]),
        ]))
    self.RunGenomics(
        ['references', 'list'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID NAME LENGTH SOURCE_URI ACCESSIONS
      1000 ref0 2000 uri0
      1001 ref1 2000 uri1
      """), normalize_space=True)

  def testReferencesList_EmptyList(self):
    self.mocked_client.references.Search.Expect(
        request=self.messages.SearchReferencesRequest(referenceSetId='GRCh39',),
        response=self.messages.SearchReferencesResponse())
    self.RunGenomics(
        ['references', 'list', '--reference-set-id', 'GRCh39'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testReferencesList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['references', 'list', '--limit', '-1'])

  def testReferencesList_Limit(self):
    self.mocked_client.references.Search.Expect(
        request=self.messages.SearchReferencesRequest(referenceSetId='GRCh38',
                                                      pageSize=3,),
        response=self.messages.SearchReferencesResponse(references=[
            self.messages.Reference(id='1000',
                                    name='ref0',
                                    length=2000,
                                    sourceUri='uri0',
                                    sourceAccessions=[]),
            self.messages.Reference(id='1001',
                                    name='ref1',
                                    length=2000,
                                    sourceUri='uri1',
                                    sourceAccessions=[]),
            self.messages.Reference(id='1002',
                                    name='ref2',
                                    length=2000,
                                    sourceUri='uri2',
                                    sourceAccessions=[]),
            self.messages.Reference(id='1003',
                                    name='ref3',
                                    length=2000,
                                    sourceUri='uri3',
                                    sourceAccessions=[]),
        ]))

    self.RunGenomics(
        ['references', 'list', '--reference-set-id', 'GRCh38',
         '--limit', '3'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID NAME LENGTH SOURCE_URI ACCESSIONS
      1000 ref0 2000 uri0
      1001 ref1 2000 uri1
      1002 ref2 2000 uri2
      """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
