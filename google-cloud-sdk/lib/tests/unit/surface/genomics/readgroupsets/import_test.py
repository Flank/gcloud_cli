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

"""Tests for genomics readgroupsets import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ImportTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets import command."""

  def testImport(self):
    operation = self.messages.Operation(done=False, name='importing123')
    self.mocked_client.readgroupsets.Import.Expect(
        request=self.messages.ImportReadGroupSetsRequest(
            datasetId='1000',
            sourceUris=[
                'gs://mybucket/reads1.bam', 'gs://mybucket/reads2*.bam'
            ]),
        response=operation)
    self.assertEqual(operation, self.RunGenomics(
        ['readgroupsets', 'import', '--dataset-id', '1000', '--source-uris',
         'gs://mybucket/reads1.bam,gs://mybucket/reads2*.bam']))
    self.AssertOutputContains(operation.name)

  def testImportWithPartitionStrategy(self):
    operation = self.messages.Operation(done=False, name='importing123')
    self.mocked_client.readgroupsets.Import.Expect(
        request=self.messages.ImportReadGroupSetsRequest(
            datasetId='1000',
            partitionStrategy=
            (self.messages.ImportReadGroupSetsRequest.
             PartitionStrategyValueValuesEnum.
             MERGE_ALL),
            sourceUris=['gs://mybucket/????.bam']),
        response=operation)
    self.assertEqual(operation, self.RunGenomics(
        ['readgroupsets', 'import', '--dataset-id', '1000', '--source-uris',
         'gs://mybucket/????.bam', '--partition-strategy', 'MERGE_ALL']))
    self.AssertOutputContains(operation.name)

  def testImportWithEverything(self):
    operation = self.messages.Operation(done=False, name='importing123')
    self.mocked_client.readgroupsets.Import.Expect(
        request=self.messages.ImportReadGroupSetsRequest(
            datasetId='1000',
            partitionStrategy=
            (self.messages.ImportReadGroupSetsRequest.
             PartitionStrategyValueValuesEnum.
             PER_FILE_PER_SAMPLE),
            referenceSetId='123',
            sourceUris=['gs://mybucket/*.bam']),
        response=operation)
    self.assertEqual(operation, self.RunGenomics(
        ['readgroupsets', 'import', '--dataset-id', '1000', '--source-uris',
         'gs://mybucket/*.bam', '--reference-set-id', '123',
         '--partition-strategy', 'PER_FILE_PER_SAMPLE']))
    self.AssertOutputContains(operation.name)

  def testImportEmptyRequest(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --dataset-id --source-uris: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'import'])

  def testImportNoSourceUris(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-uris: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'import',
                        '--dataset-id', '1000'])

  def testImportNoDatasetId(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --dataset-id: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'import',
                        '--source-uris', 'gs://bucket/reads.bam'])

  def testImportDatasetDoesNotExist(self):
    self.mocked_client.readgroupsets.Import.Expect(
        request=self.messages.ImportReadGroupSetsRequest(
            datasetId='1000',
            sourceUris=['gs://mybucket/reads.bam']),
        exception=self.MakeHttpError(404, 'Dataset not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Dataset not found: 1000'):
      self.RunGenomics(['readgroupsets', 'import',
                        '--dataset-id', '1000',
                        '--source-uris', 'gs://mybucket/reads.bam'])

  def testImportWithInvalidPartitionStrategy(self):
    with self.assertRaises(GenomicsError):
      self.RunGenomics(['readgroupsets', 'import',
                        '--dataset-id', '1000',
                        '--source-uris', 'gs://mybucket/reads.bam',
                        '--partition-strategy', 'FOO'])

  def testImportWithInvalidFileTypeFromServer(self):
    self.mocked_client.readgroupsets.Import.Expect(
        request=self.messages.ImportReadGroupSetsRequest(
            datasetId='1000',
            sourceUris=['gs://mybucket/variants.vcf'],),
        exception=self.MakeHttpError(
            400, '"sourceUris": element 0: unsupported file type'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                '"--source-uris": element 0: unsupported file'
                                ' type'):
      self.RunGenomics(['readgroupsets', 'import',
                        '--dataset-id', '1000',
                        '--source-uris', 'gs://mybucket/variants.vcf'])


if __name__ == '__main__':
  test_case.main()
