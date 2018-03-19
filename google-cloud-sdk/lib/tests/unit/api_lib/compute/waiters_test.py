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

"""Unit tests for the waiters module."""

import collections
import httplib

from googlecloudsdk.api_lib.compute import waiters
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

COMPUTE_V1_MESSAGES = apis.GetMessagesModule('compute', 'v1')
DONE = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.DONE
PENDING = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.PENDING
RUNNING = COMPUTE_V1_MESSAGES.Operation.StatusValueValuesEnum.RUNNING

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
    self.time.side_effect = iter(xrange(0, 1000, 5))

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

  def CreateOperationsData(self, statuses, ids=None, operation_type=None):
    operations = self.CreateOperations(statuses, ids, operation_type)

    operations_data = []
    for operation in operations:
      operations_data.append(
          waiters.OperationData(operation, 'my-project', self.compute.
                                zoneOperations, self.compute.instances))
    return operations_data

  def CreateOperations(self, statuses, ids=None, operation_type=None):
    ids = ids or range(len(statuses))
    assert len(ids) == len(statuses)

    operation_type = operation_type or 'insert'

    operations = []
    for i, status in zip(ids, statuses):
      operations.append(self.messages.Operation(
          name='operation-' + str(i),
          operationType=operation_type,
          selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'zones/us-central1-a/operations/operation-' + str(i)),
          status=status,
          targetLink=(
              'https://www.googleapis.com/compute/v1/projects/my-project'
              '/zones/us-central1-a/instance-' + str(i)),
          zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
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
            operations_data=self.CreateOperationsData([DONE]),
            progress_tracker=mock_progress_tracker,
        ),
        self.CreateInstances([0]))
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
            operations_data=self.CreateOperationsData([DONE, DONE, DONE]),
            progress_tracker=mock_progress_tracker,
        ),
        self.CreateInstances([0, 1, 2]))
    self.AssertSleeps()
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    mock_progress_tracker.Tick.assert_called_once_with()

  def testWithOnePendingInsertOperation(self):
    mock_progress_tracker = mock.MagicMock()
    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0]),
             responses=self.CreateOperations([DONE])),

        Call(requests=self.CreateInstancesGetRequests([0]),
             responses=self.CreateInstances([0])),
    )
    self.assertEqual(
        self.Wait(
            operations_data=self.CreateOperationsData([PENDING]),
            progress_tracker=mock_progress_tracker,
        ),
        self.CreateInstances([0]))
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])
    self.assertEqual(mock_progress_tracker.Tick.call_count, 2)

  def testWithManyPendingInsertOperations(self):
    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([DONE, DONE, DONE])),

        Call(requests=self.CreateInstancesGetRequests([0, 1, 2]),
             responses=self.CreateInstances([0, 1, 2])),
    )
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING])),
        self.CreateInstances([0, 1, 2]))
    self.AssertSleeps(1, 2)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWithManyPendingDeleteOperations(self):
    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING],
                                             operation_type='delete')),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([DONE, DONE, DONE],
                                             operation_type='delete')),

    )
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING], operation_type='delete')), [])
    self.AssertSleeps(1, 2)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWithManyPendingInsertOperationsAndInterleavingDones(self):
    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, DONE, PENDING])),

        Call(requests=(self.CreateInstancesGetRequests([1]) +
                       self.CreateOperationGetRequests([0, 2])),
             responses=(self.CreateOperations([PENDING, DONE], ids=[0, 2]) +
                        self.CreateInstances([1]))),

        Call(requests=(self.CreateInstancesGetRequests([2]) +
                       self.CreateOperationGetRequests([0])),
             responses=(self.CreateOperations([PENDING]) +
                        self.CreateInstances([2]))),

        Call(requests=self.CreateOperationGetRequests([0]),
             responses=self.CreateOperations([PENDING])),

        Call(requests=self.CreateOperationGetRequests([0]),
             responses=self.CreateOperations([PENDING])),

        Call(requests=self.CreateOperationGetRequests([0]),
             responses=self.CreateOperations([DONE])),

        Call(requests=self.CreateInstancesGetRequests([0]),
             responses=self.CreateInstances([0])),

    )

    # Note that instance-0 became ready last, so we expect it to be
    # returned last.
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING])),
        self.CreateInstances([1, 2, 0]))

    self.AssertSleeps(1, 2, 3, 4, 5, 5, 5, 5)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testTimeout(self):
    # The mock clock advances by 5 seconds on every read. Requests are
    # sent before the clock is checked, so with a 59 second timeout,
    # we expect to make 12 calls.
    calls = []
    for _ in xrange(12):
      calls.append(Call(
          requests=self.CreateOperationGetRequests([0, 1, 2]),
          responses=self.CreateOperations([PENDING, PENDING, PENDING])))

    self.RegisterCalls(*calls)

    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING]), timeout=59),
        [])
    self.AssertSleeps(1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5)
    self.assertEqual(
        self.errors,
        [(None, 'Did not create the following resources within 1800s: '
          'https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/us-central1-a/instance-0, '
          'https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/us-central1-a/instance-1, '
          'https://www.googleapis.com/compute/v1/projects/my-project/'
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
    for _ in xrange(12):
      calls.append(Call(
          requests=self.CreateOperationGetRequests([0, 1, 2]),
          responses=self.CreateOperations(
              [PENDING, PENDING, PENDING],
              operation_type='recreateInstancesInstanceGroupManager')))

    self.RegisterCalls(*calls)
    self.Wait(operations_data=self.CreateOperationsData(
        [PENDING, PENDING, PENDING]), timeout=59)
    self.assertIn('Did not recreate the following', self.errors[0][1])

  def testErrorCapturing(self):
    error_ops = self.CreateOperations([DONE, DONE, DONE])
    for i, operation in enumerate(error_ops):
      operation.httpErrorMessage = 'CONFLICT'
      operation.httpErrorStatusCode = httplib.CONFLICT
      operation.error = self.messages.Operation.ErrorValue(
          errors=[self.messages.Operation.ErrorValue.ErrorsValueListEntry(
              message='resource instance-' + str(i) + ' already exists')])
    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=error_ops),

    )
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING])), [])
    self.AssertSleeps(1, 2)
    self.assertEqual(
        self.errors,
        [(httplib.CONFLICT, 'resource instance-0 already exists'),
         (httplib.CONFLICT, 'resource instance-1 already exists'),
         (httplib.CONFLICT, 'resource instance-2 already exists')])
    self.assertEqual(self.warnings, [])

  def testErrorCapturingWithoutHttpErrorStatusCodeBeingSet(self):
    error_ops = self.CreateOperations([DONE, DONE, DONE])
    for i, operation in enumerate(error_ops):
      operation.error = self.messages.Operation.ErrorValue(
          errors=[self.messages.Operation.ErrorValue.ErrorsValueListEntry(
              message='resource instance-' + str(i) + ' already exists')])

    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=error_ops),

    )
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING])), [])
    self.AssertSleeps(1, 2)
    self.assertEqual(
        self.errors,
        [(None, 'resource instance-0 already exists'),
         (None, 'resource instance-1 already exists'),
         (None, 'resource instance-2 already exists')])
    self.assertEqual(self.warnings, [])

  def testWarningCapturing(self):
    warning_ops = self.CreateOperations([DONE, DONE, DONE])
    for operation in warning_ops:
      operation.warnings = [
          self.messages.Operation.WarningsValueListEntry(
              message='us-central1-a is deprecated')]

    self.RegisterCalls(
        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=self.CreateOperations([PENDING, PENDING, PENDING])),

        Call(requests=self.CreateOperationGetRequests([0, 1, 2]),
             responses=warning_ops),

        Call(requests=self.CreateInstancesGetRequests([0, 1, 2]),
             responses=self.CreateInstances([0, 1, 2])),

    )
    self.assertEqual(
        self.Wait(operations_data=self.CreateOperationsData(
            [PENDING, PENDING, PENDING])),
        self.CreateInstances([0, 1, 2]))
    self.AssertSleeps(1, 2)
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
          selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/us-central2/operations/operation-0'),
          status=status,
          targetLink=(
              'https://www.googleapis.com/compute/v1/projects/my-project/'
              'regions/us-central2/address-0'),
          region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central2'))

    self.RegisterCalls(
        Call(
            requests=[(self.compute.regionOperations,
                       'Get',
                       self.messages.ComputeRegionOperationsGetRequest(
                           operation='operation-0',
                           project='my-project',
                           region='us-central2'))],
            responses=[CreateRegionalOperation(DONE)]),

        Call(
            requests=[(self.compute.addresses,
                       'Get',
                       self.messages.ComputeAddressesGetRequest(
                           address='address-0',
                           project='my-project',
                           region='us-central2'))],
            responses=[self.messages.Address(name='address-0')]),
    )
    self.assertEqual(
        self.Wait(operations_data=[
            waiters.OperationData(
                CreateRegionalOperation(PENDING), 'my-project',
                self.compute.regionOperations, self.compute.addresses)
        ]), [self.messages.Address(name='address-0')])
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])

  def testWaitingForNonHomogenousOperations(self):

    def CreateRegionalOperation(status):
      return self.messages.Operation(
          name='operation-0',
          operationType='insert',
          selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/us-central2/operations/operation-0'),
          status=status,
          targetLink=(
              'https://www.googleapis.com/compute/v1/projects/my-project/'
              'regions/us-central2/address-0'),
          region=('https://www.googleapis.com/compute/v1/projects/my-project/'
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
                CreateRegionalOperation(DONE),
                self.CreateOperations([DONE])[0]
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
                CreateRegionalOperation(PENDING), 'my-project',
                self.compute.regionOperations, self.compute.addresses),
            self.CreateOperationsData([PENDING])[0]
        ]), [
            self.messages.Address(name='address-0'),
            self.messages.Instance(name='instance-0')
        ])
    self.AssertSleeps(1)
    self.assertEqual(self.errors, [])
    self.assertEqual(self.warnings, [])


class OperationDataTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.o1 = waiters.OperationData(1, 2, 3, 4)
    self.o2 = waiters.OperationData(1, 2, 3, 4)
    self.o3 = waiters.OperationData(-1, 2, 3, 4)

  def testEq(self):
    self.assertEqual(self.o1, self.o2)

  def testNe(self):
    self.assertNotEqual(self.o1, self.o3)
    self.assertNotEqual(self.o1, None)
    self.assertNotEqual(self.o1, 1)

  def testHash(self):
    self.assertEqual(hash(self.o1), hash(self.o2))


if __name__ == '__main__':
  test_case.main()
