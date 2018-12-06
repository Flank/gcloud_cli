# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for genomics operations wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.genomics import base


class WaitTest(base.GenomicsUnitTest):
  """Unit tests for genomics operations wait command."""

  def testOperationsWait(self):
    name = 'projects/fake-project/operations/12345678'
    op = self.messages_v2.Operation(done=True, name=name)
    self.mocked_client_v2.projects_operations.Get.Expect(
        request=self.messages_v2.GenomicsProjectsOperationsGetRequest(
            name=name),
        response=op)
    self.assertEqual(None, self.RunGenomics(['operations', 'wait', name]))

  def testOperationsWaitV1(self):
    name = 'operations/abcdef'
    op = self.messages.Operation(done=True, name=name)
    self.mocked_client.operations.Get.Expect(
        request=self.messages.GenomicsOperationsGetRequest(name=name),
        response=op)
    self.assertEqual(None, self.RunGenomics(['operations', 'wait', name]))

  def testOperationsWaitError(self):
    name = 'projects/fake-project/operations/12345678'
    message = 'fake error'
    op = self.messages_v2.Operation(
        done=True,
        name=name,
        error=self.messages_v2.Status(code=1, message=message))
    self.mocked_client_v2.projects_operations.Get.Expect(
        request=self.messages_v2.GenomicsProjectsOperationsGetRequest(
            name=name),
        response=op)
    with self.assertRaisesRegex(Exception, message):
      self.RunGenomics(['operations', 'wait', name])


if __name__ == '__main__':
  test_case.main()
