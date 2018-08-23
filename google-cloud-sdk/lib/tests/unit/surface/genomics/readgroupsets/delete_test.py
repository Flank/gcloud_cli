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

"""Tests for genomics readgroupsets delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class DeleteTest(base.GenomicsUnitTest):
  """Unit tests for genomics readgroupsets delete command."""

  def expectGetRequest(self):
    self.mocked_client.readgroupsets.Get.Expect(
        request=self.messages.GenomicsReadgroupsetsGetRequest(readGroupSetId=
                                                              '1000'),
        response=self.messages.ReadGroupSet(id='1000',
                                            name='rgset-name',))

  def testReadGroupSetsDelete(self):
    self.WriteInput('y\n')
    self.expectGetRequest()
    self.mocked_client.readgroupsets.Delete.Expect(
        request=self.messages.GenomicsReadgroupsetsDeleteRequest(readGroupSetId=
                                                                 '1000'),
        response={})
    self.RunGenomics(['readgroupsets', 'delete', '1000'])
    self.AssertErrContains(textwrap.dedent("""\
      Deleted [1000 (rgset-name)].
      """))

  def testReadGroupSetsDeleteCancel(self):
    self.WriteInput('n\n')
    self.expectGetRequest()
    with self.assertRaisesRegex(GenomicsError, 'Deletion aborted by user.'):
      self.RunGenomics(['readgroupsets', 'delete', '1000'])
    self.AssertErrContains(
        'Deleting read group set 1000 (rgset-name) will delete all objects')

  def testReadGroupSetsDeleteQuiet(self):
    self.expectGetRequest()
    self.mocked_client.readgroupsets.Delete.Expect(
        request=self.messages.GenomicsReadgroupsetsDeleteRequest(readGroupSetId=
                                                                 '1000'),
        response={})
    self.RunGenomics(['readgroupsets', 'delete', '1000'],
                     ['--quiet'])
    self.AssertErrEquals(textwrap.dedent("""\
      Deleted [1000 (rgset-name)].
      """))

  def testReadGroupSetsDeleteNotExists(self):
    self.expectGetRequest()
    self.mocked_client.readgroupsets.Delete.Expect(
        request=self.messages.GenomicsReadgroupsetsDeleteRequest(readGroupSetId=
                                                                 '1000'),
        exception=self.MakeHttpError(404, 'Read group set not found: 1000'))
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Read group set not found: 1000'):
      self.RunGenomics(['readgroupsets', 'delete', '1000'],
                       ['--quiet'])

if __name__ == '__main__':
  test_case.main()
