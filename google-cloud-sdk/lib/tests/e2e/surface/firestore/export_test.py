# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for `firestore export` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import re
from tests.lib import test_case
from tests.lib.surface.firestore import e2e_base


class ExportIntegrationTest(e2e_base.FirestoreE2ETestBase):
  """Tests for Export command.

  These tests don't test that exports actually complete because this can take
  a long time.
  """

  def _verifyType(self, operation):
    self.assertRegexpMatches(
        self.GetAnyField(operation.metadata, '@type').string_value,
        re.compile(
            r'^type\.googleapis\.com/google\.firestore'
            r'\.admin\.[^.]+\.ExportDocumentsMetadata$'
        ),
        msg='Incorrect type')

  def testExport(self):
    operation = self.Run('alpha firestore export --async {}'.format(
        self.GetGcsBucket()))
    self._verifyType(operation)

  def testExportWithCollectionIds(self):
    operation = self.Run('alpha firestore export --async '
                         '--collection-ids=foo,\'id with space\' '
                         '{}'.format(self.GetGcsBucket()))
    self._verifyType(operation)
    expected_collection_ids = set(['foo', 'id with space'])
    actual_collection_ids = set(
        [e.string_value for e in self.GetAnyField(
            operation.metadata, 'collectionIds').array_value.entries])
    self.assertSetEqual(expected_collection_ids, actual_collection_ids)


if __name__ == '__main__':
  test_case.main()
