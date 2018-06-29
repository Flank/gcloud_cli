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

"""Tests for genomics tests datasets update command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class UpdateTest(base.GenomicsUnitTest):
  """Unit tests for genomics datasets update command."""

  def testDatasetsUpdate(self):
    self.mocked_client.datasets.Patch.Expect(
        request=self.messages.GenomicsDatasetsPatchRequest(
            dataset=self.messages.Dataset(name='dataset-name-new',),
            datasetId='1000',),
        response=self.messages.Dataset(id='1000',
                                       name='dataset-name-new',))
    self.RunGenomics(['datasets', 'update', '1000',
                      '--name', 'dataset-name-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals('Updated dataset [dataset-name-new, id: 1000].\n')

  def testDatasetsUpdateNotExists(self):
    self.mocked_client.datasets.Patch.Expect(
        request=self.messages.GenomicsDatasetsPatchRequest(
            dataset=self.messages.Dataset(name='dataset-name-new',),
            datasetId='1000',),
        exception=self.MakeHttpError(404, 'Dataset not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Dataset not found: 1000'):
      self.RunGenomics(['datasets', 'update', '1000',
                        '--name', 'dataset-name-new'])

if __name__ == '__main__':
  test_case.main()
