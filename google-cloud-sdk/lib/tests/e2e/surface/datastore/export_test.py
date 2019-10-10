# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Integration tests for `datastore export` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.datastore import e2e_base


class ExportIntegrationTest(e2e_base.DatastoreE2ETestBase):
  """Tests for Export command.

  These tests don't test that exports actually complete because this can take
  a long time.
  """

  def testExport(self):
    operation = self.Run('datastore export --async {}'.format(
        self.GetGcsBucket()))
    self.assertEqual('EXPORT_ENTITIES',
                     self.GetAnyField(operation.metadata,
                                      'common.operationType').string_value)

  def testExportWithLabels(self):
    operation = self.Run(
        'datastore export --async --operation-labels=foo=bar {}'.format(
            self.GetGcsBucket()))
    self.assertEqual('EXPORT_ENTITIES',
                     self.GetAnyField(operation.metadata,
                                      'common.operationType').string_value)

  def testExportWithFilters(self):
    operation = self.Run('datastore export --async '
                         '--kinds=foo,\'kind with space\' '
                         '--namespaces=\'(default)\',bar {}'.format(
                             self.GetGcsBucket()))
    self.assertEqual('EXPORT_ENTITIES',
                     self.GetAnyField(operation.metadata,
                                      'common.operationType').string_value)


if __name__ == '__main__':
  test_case.main()
