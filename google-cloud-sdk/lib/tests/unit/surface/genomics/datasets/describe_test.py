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

"""Tests for genomics datasets describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DescribeTest(base.GenomicsUnitTest):
  """Unit tests for genomics datasets list command."""

  def testDescribe(self):
    dataset = self.messages.Dataset(createTime='2015-07-08T21:26:16Z',
                                    id='1000',
                                    name='dataset-name')
    self.mocked_client.datasets.Get.Expect(
        request=self.messages.GenomicsDatasetsGetRequest(datasetId=dataset.id),
        response=dataset,)
    self.assertEqual(dataset,
                     self.RunGenomics(['datasets', 'describe', dataset.id]))
    self.AssertOutputContains(dataset.id)
    self.AssertOutputContains(dataset.name)
    self.AssertOutputContains(dataset.createTime)

  def testDescribeNotExists(self):
    self.mocked_client.datasets.Get.Expect(
        request=self.messages.GenomicsDatasetsGetRequest(datasetId='1000'),
        exception=self.MakeHttpError(404, 'Dataset not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Dataset not found: 1000'):
      self.RunGenomics(['datasets', 'describe', '1000'])

if __name__ == '__main__':
  test_case.main()
