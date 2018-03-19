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

"""Tests for genomics reads list command."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics reads list command."""

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeMappedRead(self, ref, pos, fragment, seq, reverse=False):
    return self.messages.Read(
        fragmentName=fragment,
        alignedSequence=seq,
        alignment=self.messages.LinearAlignment(position=self.messages.Position(
            referenceName=ref,
            position=pos, reverseStrand=reverse)))

  def testReadsList(self):
    alignments = [
        self.messages.Read(fragmentName='a',
                           alignedSequence='ACTG'),
        self.messages.Read(fragmentName='b',
                           alignedSequence='TT'),
        self._MakeMappedRead('chr1', 1000, 'q', 'GATTACA')
    ]
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 pageSize=512,),
        response=self.messages.SearchReadsResponse(alignments=alignments),)
    self.assertEquals(alignments,
                      list(self.RunGenomics(['reads', 'list', '123'])))

  def testReadsListReferenceOnly(self):
    alignments = [
        self._MakeMappedRead('X', 1, 'q', 'ACTG', reverse=True)
    ]
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 referenceName='X',
                                                 pageSize=512,),
        response=self.messages.SearchReadsResponse(alignments=alignments),)
    self.assertEquals(alignments,
                      list(self.RunGenomics(['reads', 'list', '123',
                                             '--reference-name', 'X'])))

  def testReadsListRange(self):
    alignments = [self._MakeMappedRead('17', 7, 'q', 'ACTG')]
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 referenceName='17',
                                                 pageSize=512,
                                                 start=1,
                                                 end=10,),
        response=self.messages.SearchReadsResponse(alignments=alignments))
    self.assertEquals(alignments,
                      list(self.RunGenomics(['reads', 'list', '123',
                                             '--reference-name', '17',
                                             '--start', '1', '--end', '10'])))

  def testReadsList_EmptyList(self):
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 referenceName='empty',
                                                 pageSize=512,),
        response=self.messages.SearchReadsResponse())
    self.assertEquals([],
                      list(self.RunGenomics(['reads', 'list', '123',
                                             '--reference-name', 'empty'])))

  def testReadsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['reads', 'list', '123', '--limit', '-1'])

  def testReadsList_Limit(self):
    alignments = [
        self.messages.Read(fragmentName='a',
                           alignedSequence='AA'),
        self.messages.Read(fragmentName='b',
                           alignedSequence='CC'),
        self.messages.Read(fragmentName='c',
                           alignedSequence='TT'),
        self.messages.Read(fragmentName='d',
                           alignedSequence='GG'),
    ]
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 referenceName='*',
                                                 pageSize=3,),
        response=self.messages.SearchReadsResponse(alignments=alignments))

    self.assertEquals(alignments[0:3],
                      list(self.RunGenomics(['reads', 'list', '123',
                                             '--reference-name', '*',
                                             '--limit', '3'])))

  def testInaccessibleReadGroupSet(self):
    self.mocked_client.reads.Search.Expect(
        request=self.messages.SearchReadsRequest(readGroupSetIds=['123'],
                                                 pageSize=512,),
        exception=self.MakeHttpError(403,
                                     'Permission denied; need GET permission'))

    with self.assertRaisesRegexp(
        exceptions.HttpException,
        'Permission denied; need GET permission'):
      list(self.RunGenomics(['reads', 'list', '123']))

if __name__ == '__main__':
  test_case.main()
