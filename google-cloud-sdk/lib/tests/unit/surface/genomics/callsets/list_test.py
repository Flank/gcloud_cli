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

"""Tests for genomics callsets list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base
from six.moves import range


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics callsets list command."""

  def testCallsetsList(self):
    num_callsets = 10
    self.mocked_client.callsets.Search.Expect(
        request=self.messages.SearchCallSetsRequest(name='callset-name',
                                                    variantSetIds=['123'],),
        response=self.messages.SearchCallSetsResponse(
            callSets=[self.messages.CallSet(id=str(1000 + i),
                                            name='callset-name' + str(i),
                                            variantSetIds=['123'])
                      for i in range(num_callsets)]))
    self.RunGenomics(
        ['callsets', 'list', '123', '--name', 'callset-name'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID NAME VARIANT_SET_IDS
      1000 callset-name0 123
      1001 callset-name1 123
      1002 callset-name2 123
      1003 callset-name3 123
      1004 callset-name4 123
      1005 callset-name5 123
      1006 callset-name6 123
      1007 callset-name7 123
      1008 callset-name8 123
      1009 callset-name9 123
      """), normalize_space=True)

  def testCallsetsList_EmptyList(self):
    self.mocked_client.callsets.Search.Expect(
        request=self.messages.SearchCallSetsRequest(name='callset-name',
                                                    variantSetIds=['123'],),
        response=self.messages.SearchCallSetsResponse())
    self.RunGenomics(
        ['callsets', 'list', '123', '--name', 'callset-name'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testCallsetsList_Limit_InvalidLow(self):
    limit = -1
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['callsets', 'list', '123', '--limit', str(limit)])

  def testCallsetsList_Limit(self):
    num_callsets = 10
    limit = 5
    self.mocked_client.callsets.Search.Expect(
        request=self.messages.SearchCallSetsRequest(name='callset-name',
                                                    variantSetIds=['123'],
                                                    pageSize=limit,),
        response=self.messages.SearchCallSetsResponse(
            callSets=[self.messages.CallSet(id=str(1000 + i),
                                            name='callset-name' + str(i),
                                            variantSetIds=['123'])
                      for i in range(num_callsets)]))

    self.RunGenomics(
        ['callsets', 'list', '123', '--name', 'callset-name',
         '--limit', str(limit)])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID NAME VARIANT_SET_IDS
      1000 callset-name0 123
      1001 callset-name1 123
      1002 callset-name2 123
      1003 callset-name3 123
      1004 callset-name4 123
      """), normalize_space=True)

  def testInaccessibleVariantSet(self):
    self.mocked_client.callsets.Search.Expect(
        request=self.messages.SearchCallSetsRequest(variantSetIds=['42']),
        exception=self.MakeHttpError(403,
                                     'Permission denied; need GET permission'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Permission denied; need GET permission'):
      self.RunGenomics(['callsets', 'list', '42'])

if __name__ == '__main__':
  test_case.main()
