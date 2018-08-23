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

"""Tests for genomics variantsets create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class CreateTest(base.GenomicsUnitTest):
  """Unit tests for genomics datasets create command."""

  def testVariantSetsCreateBadDSID(self):
    self.mocked_client.variantsets.Create.Expect(
        request=self.messages.VariantSet(datasetId='42',
                                         name='foo'),
        exception=self.MakeHttpError(404, 'Dataset 42 not found'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Dataset 42 not found'):
      self.RunGenomics(['variantsets', 'create',
                        '--name', 'foo', '--dataset-id', '42'])

  def testVariantSetsCreate(self):
    self.mocked_client.variantsets.Create.Expect(
        request=self.messages.VariantSet(datasetId='1000',
                                         name='foo',
                                         description='bar'),
        response=self.messages.VariantSet(datasetId='1000',
                                          id='10',
                                          name='foo',
                                          description='bar'))
    self.RunGenomics(['variantsets', 'create',
                      '--name', 'foo', '--description', 'bar',
                      '--dataset-id', '1000'])
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created variant set [foo, id: 10] belonging to dataset [id: 1000].
""")

  def testVariantSetsCreateWithReferenceSet(self):
    self.mocked_client.variantsets.Create.Expect(
        request=self.messages.VariantSet(datasetId='1000',
                                         name='foo',
                                         description='bar',
                                         referenceSetId='abc',),
        response=self.messages.VariantSet(datasetId='1000',
                                          name='foo',
                                          description='bar',
                                          referenceSetId='abc',
                                          id='10',))
    self.RunGenomics(['variantsets', 'create',
                      '--name', 'foo', '--dataset-id', '1000',
                      '--description', 'bar', '--reference-set-id', 'abc'])
    self.AssertOutputEquals('')
    self.AssertErrEquals('Created variant set [foo, id: 10] belonging to '
                         'dataset [id: 1000].\n')

if __name__ == '__main__':
  test_case.main()
