# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `firestore operations` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.firestore import e2e_base


class OperationsIntegrationTest(e2e_base.FirestoreE2ETestBase):
  """Integration test for all operations commands.

  This test does not mutate project state, and makes no assumptions about the
  contents of the project besides that operations are not commonly deleted.
  """

  def testOperationsList(self):
    self.Run('alpha firestore operations list --page-size=10 --limit=20')

  def testOperationsDescribe(self):
    operations = list(self.Run('alpha firestore operations list'))
    if not operations:
      self.skipTest('No operations to describe')
    operation_id = operations[0].name
    operation = self.Run(
        'alpha firestore operations describe {0}'.format(operation_id))
    # TODO(b/36049789): Uncomment after fixing AssertMessagesEqual to handle
    # JsonValue field sorting.
    # self.AssertMessagesEqual(operations[0], operation)
    self.assertEqual(operation_id, operation.name)


if __name__ == '__main__':
  test_case.main()
