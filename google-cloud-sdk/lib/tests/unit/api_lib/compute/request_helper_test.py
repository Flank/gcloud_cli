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
"""Unit tests for the request_helper module."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import waiters
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
import mock

COMPUTE_V1_MESSAGES = apis.GetMessagesModule('compute', 'v1')
_KV = COMPUTE_V1_MESSAGES.InstanceAggregatedList.ItemsValue.AdditionalProperty


class MakeRequestsTest(test_case.TestCase):

  def SetUp(self):
    batch_helper_patcher = (
        mock.patch(
            'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
            autospec=True))
    self.addCleanup(batch_helper_patcher.stop)
    self.batch_helper = batch_helper_patcher.start()

    wait_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.waiters.WaitForOperations')
    self.addCleanup(wait_patcher.stop)
    self.wait_for_operations = wait_patcher.start()
    self.wait_for_operations.return_value = iter([])

    self.compute_v1 = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    http_patcher = mock.patch('googlecloudsdk.core.credentials.http.Http',
                              autospec=True)
    self.addCleanup(http_patcher.stop)
    self.mock_http = http_patcher.start()

  def testWithSynchronousRequestsOnly(self):
    expected_responses = [
        self.messages.Instance(name='my-instance'),
        self.messages.Zone(name='my-zone'),
    ]

    self.batch_helper.side_effect = iter([
        (expected_responses, []),
    ])

    requests = [
        (self.compute_v1.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(
             instance='my-instance',
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.zones,
         'Get',
         self.messages.ComputeZonesGetRequest(
             zone='my-zone',
             project='my-project')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(responses), expected_responses)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    self.assertFalse(self.wait_for_operations.called)

  def testWithAsynchronousRequestsOnly(self):
    operations = [
        self.messages.Operation(targetLink='my-instance-1', zone='my-zone'),
        self.messages.Operation(targetLink='my-instance-2', zone='my-zone'),
    ]
    wait_response = [
        self.messages.Instance(name='my-instance-1'),
        self.messages.Instance(name='my-instance-2'),
    ]

    self.batch_helper.side_effect = iter([
        (operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        wait_response,
    ])

    requests = [
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance-3'),
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance-4'),
             project='my-project',
             zone='my-zone')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(responses), wait_response)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                zoneOperations, self.compute_v1.instances))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=None,
        warnings=[],
        errors=[])

  def testWithAsynchronousAndSynchronousRequests(self):
    operations = [
        self.messages.Operation(targetLink='my-instance-3', zone='my-zone'),
        self.messages.Operation(targetLink='my-instance-4', zone='my-zone'),
    ]
    batch_helper_sync_response = [
        self.messages.Instance(name='my-instance-1'),
        self.messages.Instance(name='my-instance-2'),
    ]
    wait_response = [
        self.messages.Instance(name='my-instance-3'),
        self.messages.Instance(name='my-instance-4'),
    ]

    self.batch_helper.side_effect = iter([
        (batch_helper_sync_response + operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        wait_response,
    ])

    requests = [
        (self.compute_v1.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(
             instance='my-instance-1',
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance-3'),
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(
             instance='my-instance-2',
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance-4'),
             project='my-project',
             zone='my-zone')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(
        list(responses), batch_helper_sync_response + wait_response)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                zoneOperations, self.compute_v1.instances))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=None,
        warnings=[],
        errors=[])

  def testWithSingleZoneMutation(self):
    operations = [self.messages.Operation(targetLink='my-instance',
                                          zone='my-zone')]
    resources = [self.messages.Instance(name='my-instance')]

    self.batch_helper.side_effect = iter([
        (operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        resources,
    ])

    requests = [
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance'),
             project='my-project',
             zone='my-zone')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(responses), resources)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                zoneOperations, self.compute_v1.instances))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=None,
        warnings=[],
        errors=[])

  def testWithProgressTracker(self):
    operations = [self.messages.Operation(targetLink='my-instance',
                                          zone='my-zone')]
    resources = [self.messages.Instance(name='my-instance')]

    self.batch_helper.side_effect = iter([
        (operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        resources,
    ])

    requests = [
        (self.compute_v1.instances,
         'Insert',
         self.messages.ComputeInstancesInsertRequest(
             instance=self.messages.Instance(name='my-instance'),
             project='my-project',
             zone='my-zone')),
    ]

    errors = []
    mock_progress_tracker = mock.MagicMock()
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors,
        progress_tracker=mock_progress_tracker
    )

    self.assertEqual(list(responses), resources)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                zoneOperations, self.compute_v1.instances))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=mock_progress_tracker,
        warnings=[],
        errors=[])

  def testWithSingleRegionMutation(self):
    operations = [
        self.messages.Operation(targetLink='my-address', region='my-region'),
    ]
    resources = [self.messages.Address(name='my-address')]

    self.batch_helper.side_effect = iter([
        (operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        resources,
    ])

    requests = [
        (self.compute_v1.addresses,
         'Insert',
         self.messages.ComputeAddressesInsertRequest(
             address=self.messages.Address(name='my-address'),
             project='my-project',
             region='my-region')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(responses), resources)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                regionOperations, self.compute_v1.addresses))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=None,
        warnings=[],
        errors=[])

  def testWithSingleGlobalMutation(self):
    operations = [
        self.messages.Operation(targetLink='my-network'),
    ]
    resources = [self.messages.Network(name='my-network')]

    self.batch_helper.side_effect = iter([
        (operations, []),
    ])
    self.wait_for_operations.side_effect = iter([
        resources,
    ])

    requests = [
        (self.compute_v1.networks,
         'Insert',
         self.messages.ComputeNetworksInsertRequest(
             network=self.messages.Network(name='my-network'),
             project='my-project')),
    ]

    errors = []
    responses = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(responses), resources)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute_v1.
                                globalOperations, self.compute_v1.networks))
    self.wait_for_operations.assert_called_once_with(
        operations_data=operations_data,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        progress_tracker=None,
        warnings=[],
        errors=[])

  def testThatListRequestsCannotBeMixedWithNonListRequests(self):
    requests = [
        (self.compute_v1.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(
             instance='my-instance',
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.instances,
         'List',
         self.messages.ComputeInstancesListRequest(
             project='my-project',
             zone='my-zone')),
        (self.compute_v1.zones,
         'Get',
         self.messages.ComputeZonesGetRequest(
             zone='my-zone',
             project='my-project')),
    ]

    errors = []
    with self.assertRaises(ValueError):
      list(request_helper.MakeRequests(
          requests=requests,
          http=self.mock_http,
          batch_url='https://www.googleapis.com/batch/compute',
          errors=errors))

    self.assertFalse(errors)
    self.assertFalse(self.batch_helper.called)
    self.assertFalse(self.wait_for_operations.called)

  def testListingWithSingleRequestAndNoPaging(self):
    items = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
        self.messages.Operation(name='operation-3'),
    ]

    self.batch_helper.side_effect = iter([
        [[self.messages.OperationList(items=items)], []],
    ])

    requests = [
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]
    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), items)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')
    self.assertFalse(self.wait_for_operations.called)

  def testListingWithSingleListRequestAndPaging(self):
    page_1 = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
        self.messages.Operation(name='operation-3'),
    ]
    page_2 = [
        self.messages.Operation(name='operation-4'),
        self.messages.Operation(name='operation-5'),
        self.messages.Operation(name='operation-6'),
    ]
    page_3 = [
        self.messages.Operation(name='operation-7'),
        self.messages.Operation(name='operation-8'),
        self.messages.Operation(name='operation-9'),
    ]

    self.batch_helper.side_effect = iter([
        [[self.messages.OperationList(
            items=page_1,
            nextPageToken='page-2')],
         []],
        [[self.messages.OperationList(
            items=page_2,
            nextPageToken='page-3')],
         []],
        [[self.messages.OperationList(items=page_3)], []],
    ])

    requests = [
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), page_1 + page_2 + page_3)
    self.assertFalse(errors)
    self.assertEqual(
        self.batch_helper.call_args_list,
        [
            mock.call(
                requests=[
                    (self.compute_v1.globalOperations,
                     'List',
                     self.messages.ComputeGlobalOperationsListRequest(
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),

            mock.call(
                requests=[
                    (self.compute_v1.globalOperations,
                     'List',
                     self.messages.ComputeGlobalOperationsListRequest(
                         pageToken='page-2',
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),

            mock.call(
                requests=[
                    (self.compute_v1.globalOperations,
                     'List',
                     self.messages.ComputeGlobalOperationsListRequest(
                         pageToken='page-3',
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),
        ])

  def testWithManyListRequestsAndPaging(self):
    zonal_page_1 = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
    ]
    zonal_page_2 = [
        self.messages.Operation(name='operation-3'),
        self.messages.Operation(name='operation-4'),
        self.messages.Operation(name='operation-5'),
    ]
    global_page_1 = [
        self.messages.Operation(name='operation-6'),
        self.messages.Operation(name='operation-7'),
    ]
    global_page_2 = [
        self.messages.Operation(name='operation-8'),
        self.messages.Operation(name='operation-9'),
    ]

    self.batch_helper.side_effect = iter([
        [
            [
                self.messages.OperationList(
                    items=zonal_page_1,
                    nextPageToken='page-2-a'),

                self.messages.OperationList(
                    items=global_page_1,
                    nextPageToken='page-2-b')
            ],
            []
        ],

        [
            [
                self.messages.OperationList(items=zonal_page_2),
                self.messages.OperationList(items=global_page_2),
            ],
            []
        ],
    ])

    requests = [
        (self.compute_v1.zoneOperations,
         'List',
         self.messages.ComputeZoneOperationsListRequest(
             zone='zone-1',
             project='my-project')),
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    # Protocol messages in protorpc are mutable, so they cannot be
    # hashed which means they cannot be stored in a set. To get around
    # this, we create sets using just the name attribute of the
    # protocol buffers before doing the equality comparison.
    self.assertEqual(
        set(operation.name for operation in res),
        set(operation.name for operation in
            zonal_page_1 + zonal_page_2 + global_page_1 + global_page_2))

    self.assertFalse(errors)
    self.assertEqual(
        self.batch_helper.call_args_list,
        [
            mock.call(
                requests=[
                    (self.compute_v1.zoneOperations,
                     'List',
                     self.messages.ComputeZoneOperationsListRequest(
                         zone='zone-1',
                         project='my-project')),
                    (self.compute_v1.globalOperations,
                     'List',
                     self.messages.ComputeGlobalOperationsListRequest(
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),

            mock.call(
                requests=[
                    (self.compute_v1.zoneOperations,
                     'List',
                     self.messages.ComputeZoneOperationsListRequest(
                         zone='zone-1',
                         pageToken='page-2-a',
                         project='my-project')),
                    (self.compute_v1.globalOperations,
                     'List',
                     self.messages.ComputeGlobalOperationsListRequest(
                         pageToken='page-2-b',
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),
        ])

  def testWithAggregatedListRequestAndNoPaging(self):
    items = [
        self.messages.Instance(name='instance-1'),
        self.messages.Instance(name='instance-2'),
        self.messages.Instance(name='instance-3'),
    ]

    self.batch_helper.side_effect = iter([
        [[self.messages.InstanceAggregatedList(
            items=self.messages.InstanceAggregatedList.ItemsValue(
                additionalProperties=[
                    _KV(key='zones/zone-1',
                        value=self.messages.InstancesScopedList(
                            instances=[
                                self.messages.Instance(name='instance-1'),
                                self.messages.Instance(name='instance-2'),
                            ])),
                    _KV(key='zones/zone-2',
                        value=self.messages.InstancesScopedList(
                            instances=[
                                self.messages.Instance(name='instance-3'),
                            ])),
                ])

        )], []],
    ])

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), items)
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=[
            (self.compute_v1.instances,
             'AggregatedList',
             self.messages.ComputeInstancesAggregatedListRequest(
                 project='my-project'))],
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')

  def testWithAggregatedListRequestWithUnreachableScope(self):
    items = [
        self.messages.Instance(name='instance-3'),
    ]

    warning = self.messages.InstancesScopedList.WarningValue(
        code=(self.messages.InstancesScopedList.WarningValue
              .CodeValueValuesEnum.UNREACHABLE),
        message='Scope [zones/zone-1] is unreachable.',
    )
    self.batch_helper.side_effect = iter([
        [[self.messages.InstanceAggregatedList(
            items=self.messages.InstanceAggregatedList.ItemsValue(
                additionalProperties=[
                    _KV(key='zones/zone-1',
                        value=self.messages.InstancesScopedList(
                            warning=warning)),
                    _KV(key='zones/zone-2',
                        value=self.messages.InstancesScopedList(
                            instances=[
                                self.messages.Instance(name='instance-3'),
                            ])),
                ])

        )], []],
    ])

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), items)
    self.assertEqual(errors, [(None, 'Scope [zones/zone-1] is unreachable.')])
    self.batch_helper.assert_called_once_with(
        requests=[
            (self.compute_v1.instances,
             'AggregatedList',
             self.messages.ComputeInstancesAggregatedListRequest(
                 project='my-project'))],
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')

  def testWithAggregatedListRequestAndPaging(self):
    page_1 = [
        self.messages.Instance(name='instance-1'),
        self.messages.Instance(name='instance-2'),
        self.messages.Instance(name='instance-3'),
    ]
    page_2 = [
        self.messages.Instance(name='instance-4'),
        self.messages.Instance(name='instance-5'),
        self.messages.Instance(name='instance-6'),
    ]

    self.batch_helper.side_effect = iter([
        [[self.messages.InstanceAggregatedList(
            nextPageToken='page-2',
            items=self.messages.InstanceAggregatedList.ItemsValue(
                additionalProperties=[
                    _KV(key='zones/zone-1',
                        value=self.messages.InstancesScopedList(
                            instances=page_1,
                        )),
                ])

        )], []],

        [[self.messages.InstanceAggregatedList(
            items=self.messages.InstanceAggregatedList.ItemsValue(
                additionalProperties=[
                    _KV(key='zones/zone-1',
                        value=self.messages.InstancesScopedList(
                            instances=page_2,
                        )),
                ])

        )], []],
    ])

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.MakeRequests(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), page_1 + page_2)
    self.assertFalse(errors)
    self.assertEqual(
        self.batch_helper.call_args_list,
        [
            mock.call(
                requests=[
                    (self.compute_v1.instances,
                     'AggregatedList',
                     self.messages.ComputeInstancesAggregatedListRequest(
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),

            mock.call(
                requests=[
                    (self.compute_v1.instances,
                     'AggregatedList',
                     self.messages.ComputeInstancesAggregatedListRequest(
                         pageToken='page-2',
                         project='my-project'))],
                http=self.mock_http,
                batch_url='https://www.googleapis.com/batch/compute'),
        ])


class ListJsonTests(test_case.TestCase):

  def SetUp(self):
    batch_helper_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
        autospec=True)
    self.addCleanup(batch_helper_patcher.stop)
    self.batch_helper = batch_helper_patcher.start()

    self.compute_v1 = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    http_patcher = mock.patch('googlecloudsdk.core.credentials.http.Http',
                              autospec=True)
    self.addCleanup(http_patcher.stop)
    self.mock_http = http_patcher.start()

  def testListingWithSingleRequestAndNoPaging(self):
    items = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
        self.messages.Operation(name='operation-3'),
    ]

    self.batch_helper.side_effect = [
        [[encoding.MessageToJson(self.messages.OperationList(items=items))],
         []],
    ]

    requests = [
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]
    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), resource_projector.MakeSerializable(items))
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')

  def testListingWithSingleListRequestAndPaging(self):
    page_1 = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
        self.messages.Operation(name='operation-3'),
    ]
    page_2 = [
        self.messages.Operation(name='operation-4'),
        self.messages.Operation(name='operation-5'),
        self.messages.Operation(name='operation-6'),
    ]
    page_3 = [
        self.messages.Operation(name='operation-7'),
        self.messages.Operation(name='operation-8'),
        self.messages.Operation(name='operation-9'),
    ]

    self.batch_helper.side_effect = [
        [[
            encoding.MessageToJson(
                self.messages.OperationList(
                    items=page_1, nextPageToken='page-2'))
        ], []],
        [[
            encoding.MessageToJson(
                self.messages.OperationList(
                    items=page_2, nextPageToken='page-3'))
        ], []],
        [[encoding.MessageToJson(self.messages.OperationList(items=page_3))],
         []],
    ]

    requests = [
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(
        list(res),
        resource_projector.MakeSerializable(page_1 + page_2 + page_3))
    self.assertFalse(errors)
    self.assertEqual(self.batch_helper.call_args_list, [
        mock.call(
            requests=[(self.compute_v1.globalOperations,
                       'List',
                       self.messages.ComputeGlobalOperationsListRequest(
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
        mock.call(
            requests=[(self.compute_v1.globalOperations,
                       'List',
                       self.messages.ComputeGlobalOperationsListRequest(
                           pageToken='page-2',
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
        mock.call(
            requests=[(self.compute_v1.globalOperations,
                       'List',
                       self.messages.ComputeGlobalOperationsListRequest(
                           pageToken='page-3',
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
    ])

  def testWithManyListRequestsAndPaging(self):
    zonal_page_1 = [
        self.messages.Operation(name='operation-1'),
        self.messages.Operation(name='operation-2'),
    ]
    zonal_page_2 = [
        self.messages.Operation(name='operation-3'),
        self.messages.Operation(name='operation-4'),
        self.messages.Operation(name='operation-5'),
    ]
    global_page_1 = [
        self.messages.Operation(name='operation-6'),
        self.messages.Operation(name='operation-7'),
    ]
    global_page_2 = [
        self.messages.Operation(name='operation-8'),
        self.messages.Operation(name='operation-9'),
    ]

    self.batch_helper.side_effect = [
        [[
            encoding.MessageToJson(
                self.messages.OperationList(
                    items=zonal_page_1, nextPageToken='page-2-a')),
            encoding.MessageToJson(
                self.messages.OperationList(
                    items=global_page_1, nextPageToken='page-2-b'))
        ], []],
        [[
            encoding.MessageToJson(
                self.messages.OperationList(items=zonal_page_2)),
            encoding.MessageToJson(
                self.messages.OperationList(items=global_page_2)),
        ], []],
    ]

    requests = [
        (self.compute_v1.zoneOperations,
         'List',
         self.messages.ComputeZoneOperationsListRequest(
             zone='zone-1',
             project='my-project')),
        (self.compute_v1.globalOperations,
         'List',
         self.messages.ComputeGlobalOperationsListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    # Protocol messages in protorpc are mutable, so they cannot be
    # hashed which means they cannot be stored in a set. To get around
    # this, we create sets using just the name attribute of the
    # protocol buffers before doing the equality comparison.
    self.assertEqual(
        set(operation['name'] for operation in res),
        set(operation.name for operation in
            zonal_page_1 + zonal_page_2 + global_page_1 + global_page_2))

    self.assertFalse(errors)
    self.assertEqual(self.batch_helper.call_args_list, [
        mock.call(
            requests=[(self.compute_v1.zoneOperations,
                       'List',
                       self.messages.ComputeZoneOperationsListRequest(
                           zone='zone-1',
                           project='my-project')),
                      (self.compute_v1.globalOperations,
                       'List',
                       self.messages.ComputeGlobalOperationsListRequest(
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
        mock.call(
            requests=[(self.compute_v1.zoneOperations,
                       'List',
                       self.messages.ComputeZoneOperationsListRequest(
                           zone='zone-1',
                           pageToken='page-2-a',
                           project='my-project')),
                      (self.compute_v1.globalOperations,
                       'List',
                       self.messages.ComputeGlobalOperationsListRequest(
                           pageToken='page-2-b',
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
    ])

  def testWithAggregatedListRequestAndNoPaging(self):
    items = [
        self.messages.Instance(name='instance-1'),
        self.messages.Instance(name='instance-2'),
        self.messages.Instance(name='instance-3'),
    ]

    self.batch_helper.side_effect = [
        [[
            encoding.MessageToJson(
                self.messages.InstanceAggregatedList(
                    items=self.messages.InstanceAggregatedList.ItemsValue(
                        additionalProperties=[
                            _KV(key='zones/zone-1',
                                value=self.messages.
                                InstancesScopedList(instances=[
                                    self.messages.Instance(name='instance-1'),
                                    self.messages.Instance(name='instance-2'),
                                ])),
                            _KV(key='zones/zone-2',
                                value=self.messages.
                                InstancesScopedList(instances=[
                                    self.messages.Instance(name='instance-3'),
                                ])),
                        ])))
        ], []],
    ]

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(
        set(instance['name'] for instance in res),
        set(instance.name for instance in items))
    self.assertFalse(errors)
    self.batch_helper.assert_called_once_with(
        requests=[(self.compute_v1.instances,
                   'AggregatedList',
                   self.messages.ComputeInstancesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')

  def testWithAggregatedListRequestWithUnreachableScope(self):
    items = [
        self.messages.Instance(name='instance-3'),
    ]

    warning = self.messages.InstancesScopedList.WarningValue(
        code=(self.messages.InstancesScopedList.WarningValue
              .CodeValueValuesEnum.UNREACHABLE),
        message='Scope [zones/zone-1] is unreachable.',
    )
    self.batch_helper.side_effect = [
        [[
            encoding.MessageToJson(
                self.messages.InstanceAggregatedList(
                    items=self.messages.InstanceAggregatedList.ItemsValue(
                        additionalProperties=[
                            _KV(key='zones/zone-1',
                                value=self.messages.InstancesScopedList(
                                    warning=warning)),
                            _KV(key='zones/zone-2',
                                value=self.messages.
                                InstancesScopedList(instances=[
                                    self.messages.Instance(name='instance-3'),
                                ])),
                        ])))
        ], []],
    ]

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(list(res), resource_projector.MakeSerializable(items))
    self.assertEqual(errors, [(None, 'Scope [zones/zone-1] is unreachable.')])
    self.batch_helper.assert_called_once_with(
        requests=[(self.compute_v1.instances,
                   'AggregatedList',
                   self.messages.ComputeInstancesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute')

  def testWithAggregatedListRequestAndPaging(self):
    page_1 = [
        self.messages.Instance(name='instance-1'),
        self.messages.Instance(name='instance-2'),
        self.messages.Instance(name='instance-3'),
    ]
    page_2 = [
        self.messages.Instance(name='instance-4'),
        self.messages.Instance(name='instance-5'),
        self.messages.Instance(name='instance-6'),
    ]

    self.batch_helper.side_effect = [
        [[
            encoding.MessageToJson(
                self.messages.InstanceAggregatedList(
                    nextPageToken='page-2',
                    items=self.messages.InstanceAggregatedList.ItemsValue(
                        additionalProperties=[
                            _KV(key='zones/zone-1',
                                value=self.messages.InstancesScopedList(
                                    instances=page_1,)),
                        ])))
        ], []],
        [[
            encoding.MessageToJson(
                self.messages.InstanceAggregatedList(
                    items=self.messages.InstanceAggregatedList.ItemsValue(
                        additionalProperties=[
                            _KV(key='zones/zone-1',
                                value=self.messages.InstancesScopedList(
                                    instances=page_2,)),
                        ])))
        ], []],
    ]

    requests = [
        (self.compute_v1.instances,
         'AggregatedList',
         self.messages.ComputeInstancesAggregatedListRequest(
             project='my-project')),
    ]

    errors = []
    res = request_helper.ListJson(
        requests=requests,
        http=self.mock_http,
        batch_url='https://www.googleapis.com/batch/compute',
        errors=errors)

    self.assertEqual(
        list(res), resource_projector.MakeSerializable(page_1 + page_2))
    self.assertFalse(errors)
    self.assertEqual(self.batch_helper.call_args_list, [
        mock.call(
            requests=[(self.compute_v1.instances,
                       'AggregatedList',
                       self.messages.ComputeInstancesAggregatedListRequest(
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
        mock.call(
            requests=[(self.compute_v1.instances,
                       'AggregatedList',
                       self.messages.ComputeInstancesAggregatedListRequest(
                           pageToken='page-2',
                           project='my-project'))],
            http=self.mock_http,
            batch_url='https://www.googleapis.com/batch/compute'),
    ])


if __name__ == '__main__':
  test_case.main()
