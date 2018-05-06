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

"""Tests for genomics readgroupsets export command."""

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class ExportTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets export command."""

  def _MakeExportRequest(self, rgset_id, export_uri, reference_names=None,
                         project_id=None):
    if not reference_names:
      reference_names = []
    if not project_id:
      project_id = self.Project()
    return self.messages.GenomicsReadgroupsetsExportRequest(
        readGroupSetId=rgset_id,
        exportReadGroupSetRequest=self.messages.ExportReadGroupSetRequest(
            exportUri=export_uri,
            referenceNames=reference_names,
            projectId=project_id))

  def testExport(self):
    operation = self.messages.Operation(done=False, name='exporting123')
    self.mocked_client.readgroupsets.Export.Expect(
        request=self._MakeExportRequest('1000', 'gs://mybucket/foo.bam'),
        response=operation)
    self.assertEqual(
        operation, self.RunGenomics(['readgroupsets', 'export', '1000',
                                     '--export-uri', 'gs://mybucket/foo.bam']))
    self.AssertOutputContains(operation.name)

  def testExportWithReferenceNames(self):
    operation = self.messages.Operation(done=False, name='exporting123')
    self.mocked_client.readgroupsets.Export.Expect(
        request=self._MakeExportRequest('1000',
                                        'gs://mybucket/foo.bam',
                                        reference_names=['*', '1', '2']),
        response=operation)
    self.assertEqual(operation, self.RunGenomics(
        ['readgroupsets', 'export', '1000', '--export-uri',
         'gs://mybucket/foo.bam', '--reference-names', '*,1,2']))
    self.AssertOutputContains(operation.name)

  def testExportEmptyRequest(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument READ_GROUP_SET_ID --export-uri: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'export'])

  def testExportNoReadGroupSetId(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument READ_GROUP_SET_ID: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'export',
                        '--export-uri', 'gs://bucket/reads.bam'])

  def testExportNoExportUri(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --export-uri: Must be specified.'):
      self.RunGenomics(['readgroupsets', 'export', '123'])

  def testExportReadGroupSetDoesNotExist(self):
    self.mocked_client.readgroupsets.Export.Expect(
        self._MakeExportRequest('1000', 'gs://mybucket/reads.bam'),
        exception=self.MakeHttpError(
            404, 'Read group set not found: 1000')
    )
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Read group set not found: 1000'):
      self.RunGenomics(['readgroupsets', 'export', '1000',
                        '--export-uri', 'gs://mybucket/reads.bam'])


if __name__ == '__main__':
  test_case.main()
