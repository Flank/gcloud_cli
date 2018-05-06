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

"""Tests for genomics readgroupsets describe command."""

from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets describe command."""

  def testDescribe(self):
    rgset = self.messages.ReadGroupSet(
        datasetId='12345678',
        id='CJ_ppJ-WCxDxrtDr5fGIhBA',
        name='my-rgset',
        info=self.messages.ReadGroupSet.InfoValue(additionalProperties=[
            self.messages.ReadGroupSet.InfoValue.AdditionalProperty(
                key='k',
                value=genomics_util.InfoValuesToAPI(['v1', 'v2']))
        ]),
        readGroups=[self.messages.ReadGroup(
            id='456',
            info=self.messages.ReadGroup.InfoValue(additionalProperties=[
                self.messages.ReadGroup.InfoValue.AdditionalProperty(
                    key='k2',
                    value=genomics_util.InfoValuesToAPI(['v']))
            ]),
            name='rg001',
            sampleId='sample001',)],
        referenceSetId='123')

    self.mocked_client.readgroupsets.Get.Expect(
        request=self.messages.GenomicsReadgroupsetsGetRequest(readGroupSetId=
                                                              rgset.id),
        response=rgset)
    self.assertEqual(rgset,
                     self.RunGenomics(['readgroupsets', 'describe', rgset.id]))
    self.AssertOutputContains(rgset.name)

  def testDescribeNotExists(self):
    self.mocked_client.readgroupsets.Get.Expect(
        request=self.messages.GenomicsReadgroupsetsGetRequest(readGroupSetId=
                                                              '1000',),
        exception=self.MakeHttpError(404, 'Read group set not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Read group set not found: 1000'):
      self.RunGenomics(['readgroupsets', 'describe', '1000'])

if __name__ == '__main__':
  test_case.main()
