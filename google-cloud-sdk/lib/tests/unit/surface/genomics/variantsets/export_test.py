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

"""Tests for genomics variantsets export command."""

from tests.lib import test_case
from tests.lib.surface.genomics import base


class ExportTest(base.GenomicsUnitTest):
  """Unit tests for genomics variants export command."""

  def testVariantSetsExportTest(self):
    enum = self.messages.ExportVariantSetRequest.FormatValueValuesEnum
    req = self.messages.GenomicsVariantsetsExportRequest(
        variantSetId='123',
        exportVariantSetRequest=self.messages.ExportVariantSetRequest(
            callSetIds=['123-1', '123-2'],
            projectId='42',
            format=enum.FORMAT_BIGQUERY,
            bigqueryDataset='bqdataset',
            bigqueryTable='bqtable'))
    resp = self.messages.Operation(done=True)
    self.mocked_client.variantsets.Export.Expect(request=req, response=resp)
    self.assertEquals(resp, self.RunGenomics(['variantsets',
                                              'export',
                                              '123',
                                              'bqtable',
                                              '--call-set-ids',
                                              '123-1,123-2',
                                              '--bigquery-project',
                                              '42',
                                              '--bigquery-dataset',
                                              'bqdataset',]))

  def testVariantSetsExportTestDefaultProjectId(self):
    enum = self.messages.ExportVariantSetRequest.FormatValueValuesEnum
    req = self.messages.GenomicsVariantsetsExportRequest(
        variantSetId='123',
        exportVariantSetRequest=self.messages.ExportVariantSetRequest(
            callSetIds=['123-1', '123-2'],
            projectId='fake-project',
            format=enum.FORMAT_BIGQUERY,
            bigqueryDataset='bqdataset',
            bigqueryTable='bqtable'))
    resp = self.messages.Operation(done=True)
    self.mocked_client.variantsets.Export.Expect(request=req, response=resp)
    self.assertEquals(resp, self.RunGenomics(['variantsets',
                                              'export',
                                              '123',
                                              'bqtable',
                                              '--call-set-ids',
                                              '123-1,123-2',
                                              '--bigquery-dataset',
                                              'bqdataset',]))

  def testVariantSetsExportTestNoCallSetIds(self):
    enum = self.messages.ExportVariantSetRequest.FormatValueValuesEnum
    req = self.messages.GenomicsVariantsetsExportRequest(
        variantSetId='123',
        exportVariantSetRequest=self.messages.ExportVariantSetRequest(
            projectId='fake-project',
            format=enum.FORMAT_BIGQUERY,
            bigqueryDataset='bqdataset',
            bigqueryTable='bqtable'))
    resp = self.messages.Operation(done=True)
    self.mocked_client.variantsets.Export.Expect(request=req, response=resp)
    self.assertEquals(resp, self.RunGenomics(['variantsets',
                                              'export',
                                              '123',
                                              'bqtable',
                                              '--bigquery-dataset',
                                              'bqdataset']))

if __name__ == '__main__':
  test_case.main()
