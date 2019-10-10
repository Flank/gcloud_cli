# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the waiters module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.compute import waiters
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error

import mock
from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin
import six.moves.http_client


COMPUTE_V1_MESSAGES = apis.GetMessagesModule('compute', 'v1')
DONE_V1 = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.DONE
PENDING_V1 = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.PENDING
RUNNING_V1 = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.RUNNING

Call = collections.namedtuple('Call', ['requests', 'responses'])


class WaitForOperationsTest(sdk_test_base.SdkBase):

  def SetUp(self):
    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    sleep_patcher = mock.patch('time.sleep')
    self.addCleanup(sleep_patcher.stop)
    self.sleep = sleep_patcher.start()

    time_patcher = mock.patch(
        'googlecloudsdk.command_lib.util.time_util.CurrentTimeSec',
        autospec=True)
    self.addCleanup(time_patcher.stop)
    self.time = time_patcher.start()
    self.time.side_effect = iter(range(0, 1000, 5))

    sleep_patcher = mock.patch(
        'googlecloudsdk.command_lib.util.time_util.Sleep',
        autospec=True)
    self.addCleanup(sleep_patcher.stop)
    self.sleep = sleep_patcher.start()

    self.mock_http = mock.MagicMock()
    self.batch_url = 'https://www.googleapis.com/batch/compute'

    self.compute = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    self.warnings = []
    self.errors = []

    self.batch_requests = []

  def TearDown(self):
    self.assertEqual(self.make_requests.call_args_list,
                     self.batch_requests)

  def Wait(self, **kwargs):
    args = dict(
        warnings=self.warnings,
        errors=self.errors,
        http=self.mock_http,
        batch_url=self.batch_url,
        progress_tracker=None,
    )
    args.update(kwargs)
    return list(waiters.WaitForOperations(**args))

  def CreateOperationsData(self, statuses, ids=None, operation_type=None,
                           followup_overrides=None):
    operations = self.CreateOperations(statuses, ids, operation_type)

    if not followup_overrides:
      followup_overrides = [None for _ in statuses]

    operations_data = []
    for operation, followup_override in zip(operations, followup_overrides):
      operations_data.append(
          waiters.OperationData(
              operation,
              self.compute.zoneOperations,
              self.compute.instances,
              project='my-project',
              followup_override=followup_override))
    return operations_data

  def CreateOperations(self, statuses, ids=None, operation_type=None):
    ids = ids or list(range(len(statuses)))
    assert len(ids) == len(statuses)

    operation_type = operation_type or 'insert'

    operations = []
    for i, status in zip(ids, statuses):
      operations.append(self.messages.Operation(
          name='operation-' + str(i),
          operationType=operation_type,
          selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'zones/us-central1-a/operations/operation-' + str(i)),
          status=status,
          targetLink=(
              'https://compute.googleapis.com/compute/v1/projects/my-project'
              '/zones/us-central1-a/instance-' + str(i)),
          zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'zones/us-central2-a')))
    return operations

  def CreateOperationGetRequests(self, ids):
    res = []
    for i in ids:
      res.append((self.compute.zoneOperations, 'Get',
                  self.messages.ComputeZoneOperationsGetRequest(
                      operation='operation-' + str(i),
                      project='my-project',
                      zone='us-central2-a')))
    return res

  def CreateInstances(self, ids):
    res = []
    for i in ids:
      res.append(self.messages.Instance(
          name='instance-' + str(i),
          zone='us-central2-a'))
    return res

  def CreateInstancesGetRequests(self, ids):
    res = []
    for i in ids:
      res.append((self.compute.instances, 'Get',
                  self.messages.ComputeInstancesGetRequest(
                      instance='instance-' + str(i),
                      project='my-project',
                      zone='us-central2-a')))
    return res

  def CreateInstancesCustomGetRequests(self, instance_names):
    res = []
    for instance_name in instance_names:
      res.append((self.compute.instances, 'Get',
                  self.messages.ComputeInstancesGetRequest(
                      instance=instance_name,
                      project='my-project',
                      zone='us-central2-a')))
    return res

  def RegisterCalls(self, *calls):
    return_values = []

    for call in calls:
      self.batch_requests.append(mock.call(
          requests=call.requests,
          http=self.mock_http,
          batch_url=self.batch_url))

      batch_response = []
      for obj in call.responses:
        batch_response.append(obj)
      return_values.append((batch_response, []))
    self.make_requests.side_effect = iter(return_values)

  def AssertSleeps(self, *sleeps):
    calls = []
    for sleep in sleeps:
      calls.append(mock.call(sleep))
    self.assertEqual(self.sleep.call_args_list, calls)

  def testWithNoOperations(self):
    self.RegisterCalls()
    self.assertEqual(self.Wait(operations_data=[]), [])
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWithOneDoneInsertOperation(self):
    mock_progress_tracker = mock.MagicMock()
    self.RegisterCalls(
        Call(
            requests=self.CreateInstancesGetRequests([0]),
            responses=self.CreateInstances([0])),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData([DONE_V1]),
            progress_tracker=mock_progress_tracker,
        ), self.CreateInstances([0]))
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    mock_progress_tracker.Tick.assert_called_once_with()

  def testWithOneDoneOverrideOperation(self):
    mock_progress_tracker = mock.MagicMock()
    self.RegisterCalls(
        Call(
            requests=self.CreateInstancesCustomGetRequests(['overridden-name']),
            responses=self.CreateInstances([0])),)
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [DONE_V1], followup_overrides=['overridden-name']),
            progress_tracker=mock_progress_tracker), self.CreateInstances([0]))
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    mock_progress_tracker.Tick.assert_called_once_with()

  def testWithManyDoneInsertOperations(self):
    mock_progress_tracker = mock.MagicMock()
    self.RegisterCalls(
        Call(requests=self.CreateInstancesGetRequests([0, 1, 2]),
             responses=self.CreateInstances([0, 1, 2])),
    )

    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [DONE_V1, DONE_V1, DONE_V1]),
            progress_tracker=mock_progress_tracker,
        ), self.CreateInstances([0, 1, 2]))
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    mock_progress_tracker.Tick.assert_called_once_with()

  def testWithOnePendingInsertOperation(self):
    mock_progress_tracker = mock.MagicMock()
    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0]),
            responses=self.CreateOperations([DONE_V1])),
        Call(
            requests=self.CreateInstancesGetRequests([0]),
            responses=self.CreateInstances([0])),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData([PENDING_V1]),
            progress_tracker=mock_progress_tracker,
        ), self.CreateInstances([0]))
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    self.assertEqual(mock_progress_tracker.Tick.call_count, 2)

  def testWithManyPendingInsertOperations(self):
    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations([DONE_V1, DONE_V1, DONE_V1])),
        Call(
            requests=self.CreateInstancesGetRequests([0, 1, 2]),
            responses=self.CreateInstances([0, 1, 2])),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        self.CreateInstances([0, 1, 2]))
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWithManyPendingDeleteOperations(self):
    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1], operation_type='delete')),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations([DONE_V1, DONE_V1, DONE_V1],
                                            operation_type='delete')),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1], operation_type='delete')),
        [])
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWithManyPendingInsertOperationsAndInterleavingDones(self):
    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations([PENDING_V1, DONE_V1, PENDING_V1])),
        Call(
            requests=(self.CreateInstancesGetRequests([1]) +
                      self.CreateOperationGetRequests([0, 2])),
            responses=(
                self.CreateOperations([PENDING_V1, DONE_V1], ids=[0, 2]) +
                self.CreateInstances([1]))),
        Call(
            requests=(self.CreateInstancesGetRequests([2]) +
                      self.CreateOperationGetRequests([0])),
            responses=(self.CreateOperations([PENDING_V1]) +
                       self.CreateInstances([2]))),
        Call(
            requests=self.CreateOperationGetRequests([0]),
            responses=self.CreateOperations([PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0]),
            responses=self.CreateOperations([PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0]),
            responses=self.CreateOperations([DONE_V1])),
        Call(
            requests=self.CreateInstancesGetRequests([0]),
            responses=self.CreateInstances([0])),
    )

    # Note that instance-0 became ready last, so we expect it to be
    # returned last.
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        self.CreateInstances([1, 2, 0]))

    self.AssertSleeps(1, 2, 3, 4, 5, 5, 5)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testTimeout(self):
    # The mock clock advances by 5 seconds on every read. Requests are
    # sent before the clock is checked, so with a 59 second timeout,
    # we expect to make 12 calls.
    calls = []
    for _ in range(12):
      calls.append(
          Call(
              requests=self.CreateOperationGetRequests([0, 1, 2]),
              responses=self.CreateOperations(
                  [PENDING_V1, PENDING_V1, PENDING_V1])))

    self.RegisterCalls(*calls)

    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1]),
            timeout=59), [])
    self.AssertSleeps(1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5)
    self.assertEqual(
        self.errors,
        [(None, 'Did not create the following resources within 1800s: '
          'https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/us-central1-a/instance-0, '
          'https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/us-central1-a/instance-1, '
          'https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/us-central1-a/instance-2. '
          'These operations may still be '
          'underway remotely and may still succeed; use gcloud list and '
          'describe commands or https://console.developers.google.com/ to '
          'check resource state')])
    self.assertEqual(self.warnings, [])

  def testTimeoutMessageRecreateInstancesIGM(self):
    # The mock clock advances by 5 seconds on every read. Requests are
    # sent before the clock is checked, so with a 59 second timeout,
    # we expect to make 12 calls.
    calls = []
    for _ in range(12):
      calls.append(
          Call(
              requests=self.CreateOperationGetRequests([0, 1, 2]),
              responses=self.CreateOperations(
                  [PENDING_V1, PENDING_V1, PENDING_V1],
                  operation_type='recreateInstancesInstanceGroupManager')))

    self.RegisterCalls(*calls)
    self.Wait(
        operations_data=self.CreateOperationsData(
            [PENDING_V1, PENDING_V1, PENDING_V1]),
        timeout=59)
    self.assertIn('Did not recreate the following', self.errors[0][1])

  def testErrorCapturing(self):
    error_ops = self.CreateOperations([DONE_V1, DONE_V1, DONE_V1])
    for i, operation in enumerate(error_ops):
      operation.httpErrorMessage = 'CONFLICT'
      operation.httpErrorStatusCode = six.moves.http_client.CONFLICT
      operation.error = self.messages.Operation.ErrorValue(
          errors=[self.messages.Operation.ErrorValue.ErrorsValueListEntry(
              message='resource instance-' + str(i) + ' already exists')])
    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=error_ops),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1])), [])
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [
        (six.moves.http_client.CONFLICT, 'resource instance-0 already exists'),
        (six.moves.http_client.CONFLICT, 'resource instance-1 already exists'),
        (six.moves.http_client.CONFLICT, 'resource instance-2 already exists')
    ])
    self.assertEqual(self.warnings, [])

  def testErrorCapturingWithoutHttpErrorStatusCodeBeingSet(self):
    error_ops = self.CreateOperations([DONE_V1, DONE_V1, DONE_V1])
    for i, operation in enumerate(error_ops):
      operation.error = self.messages.Operation.ErrorValue(
          errors=[self.messages.Operation.ErrorValue.ErrorsValueListEntry(
              message='resource instance-' + str(i) + ' already exists')])

    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=error_ops),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1])), [])
    self.AssertSleeps(1)
    self.assertEqual(
        self.errors,
        [(None, 'resource instance-0 already exists'),
         (None, 'resource instance-1 already exists'),
         (None, 'resource instance-2 already exists')])
    self.assertEqual(self.warnings, [])

  def testWarningCapturing(self):
    warning_ops = self.CreateOperations([DONE_V1, DONE_V1, DONE_V1])
    for operation in warning_ops:
      operation.warnings = [
          self.messages.Operation.WarningsValueListEntry(
              message='us-central1-a is deprecated')]

    self.RegisterCalls(
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=self.CreateOperations(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        Call(
            requests=self.CreateOperationGetRequests([0, 1, 2]),
            responses=warning_ops),
        Call(
            requests=self.CreateInstancesGetRequests([0, 1, 2]),
            responses=self.CreateInstances([0, 1, 2])),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData(
                [PENDING_V1, PENDING_V1, PENDING_V1])),
        self.CreateInstances([0, 1, 2]))
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(
        self.warnings,
        ['us-central1-a is deprecated',
         'us-central1-a is deprecated',
         'us-central1-a is deprecated'])

  def testWaitingForRegionalOperation(self):

    def CreateRegionalOperation(status):
      return self.messages.Operation(
          name='operation-0',
          operationType='insert',
          selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'regions/us-central2/operations/operation-0'),
          status=status,
          targetLink=(
              'https://compute.googleapis.com/compute/v1/projects/my-project/'
              'regions/us-central2/address-0'),
          region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central2'))

    self.RegisterCalls(
        Call(
            requests=[(self.compute.regionOperations, 'Get',
                       self.messages.ComputeRegionOperationsGetRequest(
                           operation='operation-0',
                           project='my-project',
                           region='us-central2'))],
            responses=[CreateRegionalOperation(DONE_V1)]),
        Call(
            requests=[(self.compute.addresses, 'Get',
                       self.messages.ComputeAddressesGetRequest(
                           address='address-0',
                           project='my-project',
                           region='us-central2'))],
            responses=[self.messages.Address(name='address-0')]),
    )
    self.assertEqual(
        self.Wait(operations_data=[
            waiters.OperationData(
                CreateRegionalOperation(PENDING_V1),
                self.compute.regionOperations,
                self.compute.addresses,
                project='my-project')
        ]), [self.messages.Address(name='address-0')])
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWaitingForNonHomogenousOperations(self):

    def CreateRegionalOperation(status):
      return self.messages.Operation(
          name='operation-0',
          operationType='insert',
          selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'regions/us-central2/operations/operation-0'),
          status=status,
          targetLink=(
              'https://compute.googleapis.com/compute/v1/projects/my-project/'
              'regions/us-central2/address-0'),
          region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central2'))

    self.RegisterCalls(
        Call(
            requests=[(self.compute.regionOperations, 'Get',
                       self.messages.ComputeRegionOperationsGetRequest(
                           operation='operation-0',
                           project='my-project',
                           region='us-central2')),
                      (self.compute.zoneOperations, 'Get',
                       self.messages.ComputeZoneOperationsGetRequest(
                           operation='operation-0',
                           project='my-project',
                           zone='us-central2-a'))],
            responses=[
                CreateRegionalOperation(DONE_V1),
                self.CreateOperations([DONE_V1])[0]
            ]),
        Call(
            requests=[(self.compute.addresses, 'Get',
                       self.messages.ComputeAddressesGetRequest(
                           address='address-0',
                           project='my-project',
                           region='us-central2')),
                      (self.compute.instances, 'Get',
                       self.messages.ComputeInstancesGetRequest(
                           instance='instance-0',
                           project='my-project',
                           zone='us-central2-a'))],
            responses=[
                self.messages.Address(name='address-0'),
                self.messages.Instance(name='instance-0')
            ]))

    self.assertEqual(
        self.Wait(operations_data=[
            waiters.OperationData(
                CreateRegionalOperation(PENDING_V1),
                self.compute.regionOperations,
                self.compute.addresses,
                project='my-project'),
            self.CreateOperationsData([PENDING_V1])[0]
        ]), [
            self.messages.Address(name='address-0'),
            self.messages.Instance(name='instance-0')
        ])
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])


def _GetOperationStatusEnum(messages, status):
  enum_type = messages.Operation.StatusValueValuesEnum
  return getattr(enum_type, status)


def _CreateOperation(messages, status, operation_id=None, operation_type=None):
  operation_id = operation_id or 0

  operation_type = operation_type or 'insert'
  operation = messages.Operation(
      name='operation-' + str(operation_id),
      operationType=operation_type,
      selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'zones/us-central2-a/operations/operation-' +
                str(operation_id)),
      status=_GetOperationStatusEnum(messages, status),
      targetLink=('https://www.googleapis.com/compute/v1/projects/my-project'
                  '/zones/us-central2-a/instance-' + str(operation_id)),
      zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
            'zones/us-central2-a'))
  return operation


def _CreateOperationData(compute,
                         messages,
                         status,
                         operation_id=None,
                         operation_type=None):
  operation = _CreateOperation(messages, status, operation_id, operation_type)

  operation_data = waiters.OperationData(
      operation,
      compute.zoneOperations,
      compute.instances,
      project='my-project')
  return operation_data


def _InsertErrorsToOperations(messages,
                              operation,
                              status_code=404,
                              errors=(('error-code-1', 'error-location1',
                                       'error-message-1'),
                                      ('error-code-2', 'error-location-2',
                                       'error-message-2'))):
  operation.error = messages.Operation.ErrorValue(errors=[])
  for code, location, message in errors:
    operation.error.errors.append(
        messages.Operation.ErrorValue.ErrorsValueListEntry(
            code=code, location=location, message=message))
  operation.httpErrorStatusCode = status_code
  return operation


def _InsertWarningsToOperation(messages,
                               operation,
                               warnings=('warning-message-1',
                                         'warning-message-2')):
  operation.warnings = []
  for warning in warnings:
    operation.warnings.append(
        messages.Operation.WarningsValueListEntry(message=warning))
  return operation


class OperationDataTest(sdk_test_base.SdkBase):

  def SetUp(self):

    self.mock_client = apitools_mock.Client(
        client_class=apis.GetClientClass('compute', 'alpha'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = apis.GetMessagesModule('compute', 'alpha')
    self.compute = apis.GetClientInstance('compute', 'alpha', no_http=True)
    self.pending_operation_data = _CreateOperationData(self.compute,
                                                       self.messages, 'PENDING')

    self.pending_delete_operation_data = _CreateOperationData(
        self.compute, self.messages, 'PENDING', operation_type='delete')

    self.done_operation_data = _CreateOperationData(self.compute, self.messages,
                                                    'DONE')

  def testPollUntilDone(self):

    self.mock_client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), _CreateOperation(self.messages, 'DONE'))

    self.pending_operation_data.PollUntilDone()
    self.assertEqual(self.pending_operation_data.operation.status,
                     _GetOperationStatusEnum(self.messages, 'DONE'))
    self.assertEqual(self.pending_operation_data.errors, [])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testPollUntilDone_FinishedWithErrorsAndWarnings(self):

    done_operation = _CreateOperation(self.messages, 'DONE')
    _InsertErrorsToOperations(self.messages, done_operation)
    _InsertWarningsToOperation(self.messages, done_operation)

    self.mock_client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), done_operation)

    self.pending_operation_data.PollUntilDone()

    self.assertEqual(self.pending_operation_data.operation.status,
                     _GetOperationStatusEnum(self.messages, 'DONE'))
    self.assertEqual(self.pending_operation_data.errors,
                     [(404, 'error-message-1'), (404, 'error-message-2')])
    self.assertEqual(self.pending_operation_data.warnings,
                     ['warning-message-1', 'warning-message-2'])

  def testPollUntilDone_TimedOut(self):
    self.pending_operation_data.PollUntilDone(timeout_sec=-1)

    self.assertEqual(self.pending_operation_data.errors,
                     [(None, 'operation operation-0 timed out')])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testPollUntilDone_HttpRequestCrash(self):
    self.mock_client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'),
        exception=http_error.MakeHttpError(404, 'not found'))
    self.pending_operation_data.PollUntilDone()

    self.assertEqual(self.pending_operation_data.errors,
                     [(404, 'Resource not found API reason: not found')])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testGetResult(self):
    self.mock_client.ZoneOperationsService.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), _CreateOperation(self.messages, 'DONE'))

    self.mock_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='instance-0', project='my-project', zone='us-central2-a'),
        self.messages.Instance(zone='us-central2-a', name='instance-0'))

    instance = self.pending_operation_data.GetResult()
    self.assertEqual(instance.zone, 'us-central2-a')
    self.assertEqual(instance.name, 'instance-0')
    self.assertEqual(self.pending_operation_data.errors, [])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testGetResult_ResourceFetchingError(self):
    self.mock_client.ZoneOperationsService.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), _CreateOperation(self.messages, 'DONE'))

    self.mock_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='instance-0', project='my-project', zone='us-central2-a'),
        response=None,
        exception=http_error.MakeHttpError(404, 'not found'))

    self.pending_operation_data.GetResult()
    self.assertEqual(self.pending_operation_data.errors,
                     [(404, 'Resource not found API reason: not found')])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testGetResult_DeleteOperation(self):

    self.mock_client.ZoneOperationsService.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'),
        _CreateOperation(self.messages, 'DONE', operation_type='delete'))

    self.pending_delete_operation_data.GetResult()
    self.assertEqual(self.pending_operation_data.errors, [])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testGetResult_OperationFinishedWithError(self):
    done_operation = _CreateOperation(self.messages, 'DONE')
    _InsertErrorsToOperations(self.messages, done_operation)

    self.mock_client.ZoneOperationsService.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), done_operation)

    self.pending_operation_data.GetResult()
    self.assertEqual(self.pending_operation_data.errors,
                     [(404, 'error-message-1'), (404, 'error-message-2')])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testIsDone(self):
    self.assertFalse(self.pending_operation_data.IsDone())
    self.assertTrue(self.done_operation_data.IsDone())

  def testOperationGetRequest(self):
    request = self.pending_operation_data.OperationGetRequest()
    expected_request = self.messages.ComputeZoneOperationsGetRequest(
        project='my-project', zone='us-central2-a', operation='operation-0')
    self.assertEqual(request, expected_request)

  def testOperationWaitRequest(self):
    request = self.pending_operation_data.OperationWaitRequest()
    expected_request = self.messages.ComputeZoneOperationsWaitRequest(
        project='my-project', zone='us-central2-a', operation='operation-0')
    self.assertEqual(request, expected_request)

  def testResourceGetRequest(self):
    request = self.pending_operation_data.ResourceGetRequest()
    expected_request = self.messages.ComputeInstancesGetRequest(
        instance='instance-0', project='my-project', zone='us-central2-a')
    self.assertEqual(request, expected_request)

  def testEqual(self):
    operation_data1 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='insert')
    operation_data2 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='insert')
    self.assertEqual(operation_data1, operation_data2)

  def testNotEqual(self):
    operation_data1 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='insert')
    operation_data2 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='delete')
    self.assertNotEqual(operation_data1, operation_data2)

  def testHash(self):
    operation_data1 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='insert')
    operation_data2 = _CreateOperationData(
        self.compute, self.messages, 'DONE', operation_type='insert')
    self.assertEqual(hash(operation_data1), hash(operation_data2))


class OperationDataTestOperationGet(sdk_test_base.SdkBase):

  def SetUp(self):

    self.mock_client = apitools_mock.Client(
        client_class=apis.GetClientClass('compute', 'alpha'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    time_patcher = self.StartPatch(
        'googlecloudsdk.command_lib.util.time_util.CurrentTimeSec',
        auto_spec=True)
    time_patcher.side_effect = iter(range(0, 1000, 5))

    self.sleep_patcher = self.StartPatch(
        'googlecloudsdk.command_lib.util.time_util.Sleep', auto_spec=True)

    self.messages = apis.GetMessagesModule('compute', 'alpha')
    self.compute = apis.GetClientInstance('compute', 'alpha', no_http=True)

    self.StartObjectPatch(
        waiters.OperationData, '_SupportOperationWait', return_value=False)
    self.pending_operation_data = _CreateOperationData(self.compute,
                                                       self.messages, 'PENDING')

  def AssertSleep(self, *args):
    sleep_args = []
    for sleep_time in args:
      sleep_args.append(mock.call(sleep_time))

    self.assertEqual(self.sleep_patcher.call_args_list, sleep_args)

  def _RegisterOperationGet(self, counts):
    for _ in range(counts):
      self.mock_client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-0',
              project='my-project',
              zone='us-central2-a'), _CreateOperation(self.messages, 'PENDING'))

  def testPollUntilDone(self):

    self.mock_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), _CreateOperation(self.messages, 'DONE'))

    self.pending_operation_data.PollUntilDone()
    self.assertEqual(self.pending_operation_data.operation.status,
                     _GetOperationStatusEnum(self.messages, 'DONE'))
    self.assertEqual(self.pending_operation_data.errors, [])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testPollUntilDone_PollIntervalLimit(self):
    self._RegisterOperationGet(10)
    self.mock_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'), _CreateOperation(self.messages, 'DONE'))

    self.pending_operation_data.PollUntilDone()
    self.assertEqual(self.pending_operation_data.operation.status,
                     _GetOperationStatusEnum(self.messages, 'DONE'))
    self.assertEqual(self.pending_operation_data.errors, [])
    self.assertEqual(self.pending_operation_data.warnings, [])
    self.AssertSleep(1, 2, 3, 4, 5, 5, 5, 5, 5, 5)

  def testPollUntilDone_Timeout(self):
    self._RegisterOperationGet(1)

    self.pending_operation_data.PollUntilDone(9)
    self.assertEqual(self.pending_operation_data.errors,
                     [(None, 'operation operation-0 timed out')])
    self.assertEqual(self.pending_operation_data.warnings, [])

  def testPollUntilDone_HttpRequestCrash(self):
    self.mock_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-0', project='my-project',
            zone='us-central2-a'),
        exception=http_error.MakeHttpError(404, 'not found'))
    self.pending_operation_data.PollUntilDone()

    self.assertEqual(self.pending_operation_data.errors,
                     [(404, 'Resource not found API reason: not found')])
    self.assertEqual(self.pending_operation_data.warnings, [])


if __name__ == '__main__':
  test_case.main()
