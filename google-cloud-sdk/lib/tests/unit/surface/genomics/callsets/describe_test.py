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

"""Tests for genomics callsets describe command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics callsets list command."""

  def testCallsetsDescribe(self):
    callset = self.messages.CallSet(created=10000,
                                    id='1000',
                                    name='callset-name',
                                    variantSetIds=['vs1'])
    self.mocked_client.callsets.Get.Expect(
        request=self.messages.GenomicsCallsetsGetRequest(callSetId=callset.id),
        response=callset,)
    self.assertEqual(callset,
                     self.RunGenomics(['callsets', 'describe', callset.id]))
    self.AssertOutputContains(callset.name)

  def testCallsetsDescribeNotExists(self):
    callset = self.messages.CallSet(created=10000,
                                    id='1000',
                                    name='callset-name',
                                    variantSetIds=['vs1'])
    self.mocked_client.callsets.Get.Expect(
        request=self.messages.GenomicsCallsetsGetRequest(callSetId=callset.id),
        exception=self.MakeHttpError(404, 'Callset not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Callset not found: 1000'):
      self.RunGenomics(['callsets', 'describe', callset.id])

if __name__ == '__main__':
  test_case.main()
