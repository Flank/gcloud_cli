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
"""Test of the 'operations delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import operations
from tests.lib import test_case
from tests.lib.surface.firestore import base


class DeleteTest(base.FirestoreCommandUnitTest):
  """Tests the firestore operations delete command."""

  def testDeleteRelativePath(self):
    operation_name_relative = 'doomed'
    operation_name_full =\
      'projects/my-test-project/databases/(default)/operations/doomed'
    request = self._GetMockDeleteRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_firestore_v1.projects_databases_operations.Delete.Expect(
        request, response=response)

    self.RunFirestoreTest(
        'operations delete {}'.format(operation_name_relative))

  def testDeleteAbsolutePath(self):
    operation_name_full =\
      'projects/my-test-project/databases/(default)/operations/doomed'
    request = self._GetMockDeleteRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_firestore_v1.projects_databases_operations.Delete.Expect(
        request, response=response)

    self.RunFirestoreTest('operations delete {}'.format(operation_name_full))

  def _GetMockDeleteRequest(self, name):
    messages = operations.GetMessages()
    request = messages.FirestoreProjectsDatabasesOperationsDeleteRequest()
    request.name = name
    return request


if __name__ == '__main__':
  test_case.main()
