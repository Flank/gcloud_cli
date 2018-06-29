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

"""Tests for genomics tests readgroupsets update command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class UpdateTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets update command."""

  def testReadgroupsetsUpdateName(self):
    self.mocked_client.readgroupsets.Patch.Expect(
        request=self.messages.GenomicsReadgroupsetsPatchRequest(
            readGroupSet=self.messages.ReadGroupSet(name=
                                                    'readgroupset-name-new',),
            readGroupSetId='1000',
            updateMask='name'),
        response=self.messages.ReadGroupSet(id='1000',
                                            name='readgroupset-name-new',))
    self.RunGenomics(['readgroupsets', 'update', '1000',
                      '--name', 'readgroupset-name-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Updated readgroupset [1000, name: readgroupset-name-new].\n')

  def testReadgroupsetsUpdateReferenceSet(self):
    self.mocked_client.readgroupsets.Patch.Expect(
        request=self.messages.GenomicsReadgroupsetsPatchRequest(
            readGroupSet=self.messages.ReadGroupSet(referenceSetId=
                                                    'referenceSetId-new',),
            readGroupSetId='1000',
            updateMask='referenceSetId'),
        response=self.messages.ReadGroupSet(id='1000',
                                            referenceSetId=
                                            'referenceSetId-new',))
    self.RunGenomics(['readgroupsets', 'update', '1000',
                      '--reference-set-id', 'referenceSetId-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Updated readgroupset [1000, referenceSetId: referenceSetId-new].\n')

  def testReadgroupsetsUpdateNameAndReferenceSet(self):
    self.mocked_client.readgroupsets.Patch.Expect(
        request=self.messages.GenomicsReadgroupsetsPatchRequest(
            readGroupSet=self.messages.ReadGroupSet(
                name='readgroupset-name-new',
                referenceSetId='referenceSetId-new',),
            readGroupSetId='1000',
            updateMask='name,referenceSetId'),
        response=self.messages.ReadGroupSet(id='1000',
                                            name='readgroupset-name-new',
                                            referenceSetId=
                                            'referenceSetId-new',))
    self.RunGenomics(['readgroupsets', 'update', '1000',
                      '--name', 'readgroupset-name-new',
                      '--reference-set-id', 'referenceSetId-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Updated readgroupset [1000, name: readgroupset-name-new, '
        'referenceSetId: referenceSetId-new].\n')

  def testReadgroupsetsUpdateNameWithExistingReferenceSet(self):
    self.mocked_client.readgroupsets.Patch.Expect(
        request=self.messages.GenomicsReadgroupsetsPatchRequest(
            readGroupSet=self.messages.ReadGroupSet(name=
                                                    'readgroupset-name-new',),
            readGroupSetId='1000',
            updateMask='name'),
        response=self.messages.ReadGroupSet(id='1000',
                                            name='readgroupset-name-new',
                                            referenceSetId=
                                            'referenceSetId-new',))
    self.RunGenomics(['readgroupsets', 'update', '1000',
                      '--name', 'readgroupset-name-new'])
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Updated readgroupset [1000, name: readgroupset-name-new, '
        'referenceSetId: referenceSetId-new].\n')

  def testReadgroupsetsUpdateNotExists(self):
    self.mocked_client.readgroupsets.Patch.Expect(
        request=self.messages.GenomicsReadgroupsetsPatchRequest(
            readGroupSet=self.messages.ReadGroupSet(name=
                                                    'readgroupset-name-new',),
            readGroupSetId='1000',
            updateMask='name'),
        exception=self.MakeHttpError(404, 'Readgroupset not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Readgroupset not found: 1000'):
      self.RunGenomics(['readgroupsets', 'update', '1000',
                        '--name', 'readgroupset-name-new'])

  def testReadgroupsetsUpdateFailsWithoutParameters(self):
    with self.assertRaisesRegex(
        GenomicsError,
        'Must specify --name and/or --reference-set-id'):
      self.RunGenomics(['readgroupsets', 'update', '1000'])

if __name__ == '__main__':
  test_case.main()
