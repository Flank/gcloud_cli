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
"""Test of the 'operations list' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.datastore import operations
from tests.lib import test_case
from tests.lib.surface.datastore import base


class ListTest(base.DatastoreCommandUnitTest):
  """Tests the datastore operations list command."""

  def testList(self):
    request = self.GetMockListRequest()

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(self.RunDatastoreTest('operations list'))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithLabelGetsTranslated(self):
    expected_filter = 'metadata.common.labels.k=v'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest('operations list --filter=\'label.k:v\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithLabelCorrectUsageGetsTranslated(self):
    expected_filter = 'metadata.common.labels.k=v'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest('operations list --filter=\'labels.k:v\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithNamespaceGetsTranslated(self):
    expected_filter = 'metadata.entity_filter.namespace_id=n'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest('operations list --filter=\'namespace:n\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithDefaultNamespaceIdGetsTranslated(self):
    expected_filter = 'metadata.entity_filter.namespace_id=testnamespace'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest(
            'operations list --filter=\'namespaceId:"testnamespace"\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithDefaultNamespaceGetsTranslated(self):
    expected_filter = 'metadata.entity_filter.namespace_id=""'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest(
            'operations list --filter=\'namespace:"(default)"\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithOperationTypeGetsTranslated(self):
    expected_filter = 'metadata.common.operation_type=IMPORT_ENTITIES'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest(
            'operations list --filter=\'operationType:IMPORT_ENTITIES\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithTypeGetsTranslated(self):
    expected_filter = 'metadata.common.operation_type=IMPORT_ENTITIES'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest(
            'operations list --filter=\'type:IMPORT_ENTITIES\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testListWithKindGetsTranslated(self):
    expected_filter = 'metadata.entity_filter.kind=k'
    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(self.RunDatastoreTest('operations list --filter=\'kind:k\''))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def testMultipleFiltersGetTranslated(self):
    expected_filter = ('metadata.common.operation_type=IMPORT_ENTITIES '
                       'AND (metadata.entity_filter.namespace_id=n '
                       'AND (metadata.common.labels.k=v '
                       'AND (metadata.common.labels.k2=v2 '
                       'AND metadata.entity_filter.kind=k)))')

    request = self.GetMockListRequest(operation_filter=expected_filter)

    operation_name = 'export operation name'

    operation_list = [
        operations.GetMessages().GoogleLongrunningOperation(
            done=False, name=operation_name)
    ]

    response = operations.GetMessages().GoogleLongrunningListOperationsResponse(
        operations=operation_list)

    self.mock_datastore_v1.projects_operations.List.Expect(
        request, response=response)

    actual = list(
        self.RunDatastoreTest('operations list --filter=\'%s\'' % (
            'type:IMPORT_ENTITIES AND namespace:n AND '
            'label.k:v AND label.k2:v2 AND kind:k')))
    self.assertEqual(1, len(actual))
    self.assertEqual(operation_name, actual[0].name)

  def GetMockListRequest(self,
                         operation_filter=None,
                         page_size=operations.DEFAULT_PAGE_SIZE,
                         page_token=None):
    return operations.GetMessages().DatastoreProjectsOperationsListRequest(
        filter=operation_filter,
        name='projects/%s' % (self.Project()),
        pageSize=page_size,
        pageToken=page_token)


if __name__ == '__main__':
  test_case.main()
