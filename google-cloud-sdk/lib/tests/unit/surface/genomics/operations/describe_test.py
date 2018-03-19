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

"""Tests for genomics operations describe command."""

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics operations describe command."""

  def testOperationsDescribe(self):
    op = self.messages.Operation(done=False, name='operations/operation-name')
    self.mocked_client.operations.Get.Expect(
        request=self.messages.GenomicsOperationsGetRequest(
            name='operations/operation-name'),
        response=op)
    self.assertEquals(op, self.RunGenomics(['operations', 'describe',
                                            'operation-name']))

  def testOperationsDescribeWithOpsPrefix(self):
    op = self.messages.Operation(done=False, name='operations/operation-name')
    self.mocked_client.operations.Get.Expect(
        request=self.messages.GenomicsOperationsGetRequest(
            name='operations/operation-name'),
        response=op)
    self.assertEquals(op, self.RunGenomics(['operations', 'describe',
                                            'operations/operation-name']))

  def testOperationsDescribeNotExists(self):
    self.mocked_client.operations.Get.Expect(
        request=self.messages.GenomicsOperationsGetRequest(
            name='operations/operation-name'),
        exception=self.MakeHttpError(404,
                                     'Operation not found: operation-name'))
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 'Operation not found: operation-name'):
      self.RunGenomics(['operations', 'describe', 'operation-name'])


if __name__ == '__main__':
  test_case.main()
