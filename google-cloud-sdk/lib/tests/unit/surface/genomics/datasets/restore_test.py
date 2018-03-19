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

"""Tests for genomics datasets restore command."""

from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class RestoreTest(base.GenomicsUnitTest):
  """Unit tests for genomics datasets restore command."""

  def testDatasetsRestore(self):
    self.WriteInput('y\n')
    self.mocked_client.datasets.Undelete.Expect(
        request=self.messages.GenomicsDatasetsUndeleteRequest(datasetId='1000'),
        response=self.messages.Dataset(id='1000',
                                       name='dataset-name',))
    self.RunGenomics(['datasets', 'restore', '1000'])
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Restoring dataset 1000 will restore all objects in the dataset.

Do you want to continue (Y/n)?  \

Restored dataset [dataset-name, id: 1000].
""")

  def testDatasetsRestoreCancel(self):
    self.WriteInput('n\n')
    with self.assertRaisesRegexp(GenomicsError, 'Restore aborted by user.'):
      self.RunGenomics(['datasets', 'restore', '1000'])
    self.AssertErrContains(
        'Restoring dataset 1000 will restore all objects in the dataset.')

  def testDatasetsRestoreQuiet(self):
    self.mocked_client.datasets.Undelete.Expect(
        request=self.messages.GenomicsDatasetsUndeleteRequest(datasetId='1000'),
        response=self.messages.Dataset(id='1000',
                                       name='dataset-name',))
    self.RunGenomics(['datasets', 'restore', '1000'],
                     ['--quiet'])
    self.AssertOutputEquals('')
    self.AssertErrEquals('Restored dataset [dataset-name, id: 1000].\n')

  def testDatasetsRestoreNotExists(self):
    self.mocked_client.datasets.Undelete.Expect(
        request=self.messages.GenomicsDatasetsUndeleteRequest(datasetId='1000'),
        exception=self.MakeHttpError(404, 'Dataset not found: 1000'))
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 'Dataset not found: 1000'):
      self.RunGenomics(['datasets', 'restore', '1000'],
                       ['--quiet'])

  def testDatasetsRestoreActiveDataset(self):
    self.mocked_client.datasets.Undelete.Expect(
        request=self.messages.GenomicsDatasetsUndeleteRequest(datasetId='1000'),
        exception=self.MakeHttpError(404,
                                     'Cannot undelete active dataset: 1000'))
    with self.assertRaisesRegexp(exceptions.HttpException,
                                 'Cannot undelete active dataset: 1000'):
      self.RunGenomics(['datasets', 'restore', '1000'],
                       ['--quiet'])

if __name__ == '__main__':
  test_case.main()
