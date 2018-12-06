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

"""Tests for genomics variants import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.genomics import base


class ImportTest(base.GenomicsUnitTest):
  """Unit tests for genomics variants import command."""

  def testVariantsImportTest(self):
    format_enum = self.messages.ImportVariantsRequest.FormatValueValuesEnum
    req = self.messages.ImportVariantsRequest(
        variantSetId='123',
        sourceUris=['gs://uri0/foo'],
        format=format_enum.FORMAT_COMPLETE_GENOMICS,
        normalizeReferenceNames=False)
    resp = self.messages.Operation(name='myop')
    self.mocked_client.variants.Import.Expect(request=req, response=resp)
    self.assertEqual(resp, self.RunGenomics(['variants',
                                              'import',
                                              '--variantset-id',
                                              '123',
                                              '--source-uris',
                                              'gs://uri0/foo',
                                              '--file-format',
                                              'COMPLETE_GENOMICS',]))

  def testVariantsImportTest_NormalizeReferenceNames(self):
    format_enum = self.messages.ImportVariantsRequest.FormatValueValuesEnum
    req = self.messages.ImportVariantsRequest(
        variantSetId='123',
        sourceUris=['gs://uri0/foo'],
        format=format_enum.FORMAT_COMPLETE_GENOMICS,
        normalizeReferenceNames=True)
    resp = self.messages.Operation(name='myop')
    self.mocked_client.variants.Import.Expect(request=req, response=resp)
    self.assertEqual(resp, self.RunGenomics(['variants',
                                              'import',
                                              '--variantset-id',
                                              '123',
                                              '--source-uris',
                                              'gs://uri0/foo',
                                              '--file-format',
                                              'COMPLETE_GENOMICS',
                                              '--normalize-reference-names']))

  def testVariantsImportTest_InfoMergeConfig(self):
    format_enum = self.messages.ImportVariantsRequest.FormatValueValuesEnum
    imc = self.messages.ImportVariantsRequest.InfoMergeConfigValue
    ops_enum = imc.AdditionalProperty.ValueValueValuesEnum
    additional_properties = [
        imc.AdditionalProperty(key='BAR',
                               value=ops_enum.MOVE_TO_CALLS),
        imc.AdditionalProperty(key='BAZ',
                               value=ops_enum.INFO_MERGE_OPERATION_UNSPECIFIED),
        imc.AdditionalProperty(key='FOO',
                               value=ops_enum.IGNORE_NEW)
    ]
    req = self.messages.ImportVariantsRequest(
        variantSetId='123',
        sourceUris=['gs://uri0/foo'],
        format=format_enum.FORMAT_COMPLETE_GENOMICS,
        normalizeReferenceNames=False,
        infoMergeConfig=imc(additionalProperties=additional_properties))
    resp = self.messages.Operation(name='myop')
    self.mocked_client.variants.Import.Expect(request=req, response=resp)
    self.assertEqual(
        resp,
        self.RunGenomics(['variants', 'import', '--variantset-id', '123',
                          '--source-uris', 'gs://uri0/foo', '--file-format',
                          'COMPLETE_GENOMICS', '--info-merge-config',
                          'FOO=IGNORE_NEW,BAR=MOVE_TO_CALLS,BAZ=GORILLA']))

if __name__ == '__main__':
  test_case.main()
