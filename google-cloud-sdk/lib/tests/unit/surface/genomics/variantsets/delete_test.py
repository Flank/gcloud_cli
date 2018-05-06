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

"""Tests for genomics variantsets delete command."""

import textwrap
from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DeleteTest(base.GenomicsUnitTest):
  """Unit tests for genomics variantsets delete command."""

  def testVariantSetsDelete(self):
    self.WriteInput('y\n')
    self.mocked_client.variantsets.Get.Expect(
        request=self.messages.GenomicsVariantsetsGetRequest(variantSetId='500'),
        response=self.messages.VariantSet(id='5000', name='foo'))
    self.mocked_client.variantsets.Delete.Expect(
        request=self.messages.GenomicsVariantsetsDeleteRequest(variantSetId=
                                                               '500'),
        response={})
    self.RunGenomics(['variantsets', 'delete', '500'])
    self.AssertErrContains(textwrap.dedent("""\
      Deleted [500: "foo"].
      """))

  def testVariantSetsDeleteCancel(self):
    self.mocked_client.variantsets.Get.Expect(
        request=self.messages.GenomicsVariantsetsGetRequest(variantSetId='500'),
        response=self.messages.VariantSet(id='5000', name='foo'))
    self.WriteInput('n\n')
    with self.assertRaisesRegex(GenomicsError, 'Deletion aborted by user.'):
      self.RunGenomics(['variantsets', 'delete', '500'])
    self.AssertErrContains(
        'Deleting variant set 500: "foo" will also delete all')

  def testDatasetsDeleteQuiet(self):
    self.mocked_client.variantsets.Get.Expect(
        request=self.messages.GenomicsVariantsetsGetRequest(variantSetId='500'),
        response=self.messages.VariantSet(id='5000', name='foo'))
    self.mocked_client.variantsets.Delete.Expect(
        request=self.messages.GenomicsVariantsetsDeleteRequest(variantSetId=
                                                               '500'),
        response={})
    self.RunGenomics(['variantsets', 'delete', '500'],
                     ['--quiet'])
    self.AssertErrEquals(textwrap.dedent("""\
      Deleted [500: "foo"].
      """))

  def testDatasetsDeleteNotExists(self):
    self.mocked_client.variantsets.Get.Expect(
        request=self.messages.GenomicsVariantsetsGetRequest(variantSetId='500'),
        exception=self.MakeHttpError(404, 'VariantSet not found: 500'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'VariantSet not found: 500'):
      self.RunGenomics(['variantsets', 'delete', '500'],
                       ['--quiet'])

if __name__ == '__main__':
  test_case.main()
