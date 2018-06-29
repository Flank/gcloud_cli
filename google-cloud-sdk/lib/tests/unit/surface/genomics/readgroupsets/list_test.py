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

"""Tests for genomics readgroupsets list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets list command."""

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testReadGroupSetsList(self):
    read_group_sets = [
        self.messages.ReadGroupSet(id='1000',
                                   name='rgset0',
                                   referenceSetId='abc'),
        self.messages.ReadGroupSet(id='1001',
                                   name='rgset1',
                                   referenceSetId='def'),
    ]
    self.mocked_client.readgroupsets.Search.Expect(
        request=self.messages.SearchReadGroupSetsRequest(name='rgset',
                                                         datasetIds=['123'],
                                                         pageSize=128,),
        response=self.messages.SearchReadGroupSetsResponse(readGroupSets=
                                                           read_group_sets))
    self.assertEqual(read_group_sets, list(self.RunGenomics(
        ['readgroupsets', 'list', '123', '--name', 'rgset'])))

  def testReadGroupSetsList_EmptyList(self):
    self.mocked_client.readgroupsets.Search.Expect(
        request=self.messages.SearchReadGroupSetsRequest(name='nonexistent',
                                                         datasetIds=['123',
                                                                     '456'],
                                                         pageSize=128,),
        response=self.messages.SearchReadGroupSetsResponse())
    self.assertEqual([], list(self.RunGenomics(
        ['readgroupsets', 'list', '123', '456', '--name', 'nonexistent'])))

  def testReadGroupSetsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['readgroupsets', 'list', '123', '--limit', '-1'])

  def testReadGroupSetsList_Limit(self):
    read_group_sets = [
        self.messages.ReadGroupSet(id='1000',
                                   name='foo0',
                                   referenceSetId='abc'),
        self.messages.ReadGroupSet(id='1001',
                                   name='foo1',
                                   referenceSetId='def'),
        self.messages.ReadGroupSet(id='1002',
                                   name='foo2',
                                   referenceSetId='def'),
        self.messages.ReadGroupSet(id='1003',
                                   name='foo3',
                                   referenceSetId='abc'),
    ]
    self.mocked_client.readgroupsets.Search.Expect(
        request=self.messages.SearchReadGroupSetsRequest(name='foo',
                                                         datasetIds=['123'],
                                                         pageSize=3,),
        response=self.messages.SearchReadGroupSetsResponse(readGroupSets=
                                                           read_group_sets))

    self.assertEqual(read_group_sets[:3], list(self.RunGenomics(
        ['readgroupsets', 'list', '123', '--name', 'foo', '--limit', '3'])))

  def testInaccessibleDataset(self):
    self.mocked_client.readgroupsets.Search.Expect(
        request=self.messages.SearchReadGroupSetsRequest(datasetIds=['123'],
                                                         pageSize=128,),
        exception=self.MakeHttpError(403,
                                     'Permission denied; need GET permission'))

    with self.assertRaisesRegex(exceptions.HttpException,
                                'Permission denied; need GET permission'):
      list(self.RunGenomics(['readgroupsets', 'list', '123']))

if __name__ == '__main__':
  test_case.main()
