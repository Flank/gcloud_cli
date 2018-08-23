# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for api_lib.compute.operations.poller module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.compute.operations import poller as compute_poller
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base

import mock
from six.moves import range

_GLOBAL_OPERATIONS_COLLECTION = 'compute.globalOperations'
_REGION_OPERATIONS_COLLECTION = 'compute.regionOperations'
_ZONE_OPERATIONS_COLLECTION = 'compute.zoneOperations'


class PollerTest(waiter_test_base.Base):

  def SetUp(self):
    self.client_class = core_apis.GetClientClass('compute', 'v1')
    self.messages = self.client_class.MESSAGES_MODULE
    status_enum = self.messages.Operation.StatusValueValuesEnum
    self.status_done = status_enum.DONE
    self.status_pending = status_enum.PENDING
    self.error_entry = self.messages.Operation.ErrorValue.ErrorsValueListEntry

  def ExpectOperation(self, operation_service, operation_ref,
                      result_service, result_ref, retries=1, error_msg=None):
    request_type = operation_service.GetRequestType('Get')
    response_type = operation_service.GetResponseType('Get')
    response = response_type()
    for i in range(retries):
      if error_msg:
        response.error = self.messages.Operation.ErrorValue(
            errors=[self.error_entry(code='BAD', message=error_msg)])
      else:
        response.status = (self.status_pending
                           if i < retries-1 else self.status_done)
      response.targetLink = result_ref.SelfLink()
      operation_service.Get.Expect(
          request=request_type(**operation_ref.AsDict()),
          response=response)

    result = None
    if not error_msg and result_service:
      result_request_type = result_service.GetRequestType('Get')
      result_response_type = result_service.GetResponseType('Get')

      result = result_response_type(name=result_ref.Name())
      result_service.Get.Expect(
          request=result_request_type(**result_ref.AsDict()),
          response=result)

    return result

  def testGlobalOperation(self):
    with api_mock.Client(self.client_class) as client:
      poller = compute_poller.Poller(client.instances)
      operation_ref = resources.REGISTRY.Create(
          _GLOBAL_OPERATIONS_COLLECTION,
          project='mickey',
          operation='operationX')
      instance_ref = resources.REGISTRY.Create(
          'compute.instances',
          project='mickey',
          zone='disney',
          instance='Super-Cheese')

      self.ExpectOperation(
          client.globalOperations, operation_ref,
          client.instances, instance_ref)
      result = waiter.WaitFor(poller=poller,
                              operation_ref=operation_ref,
                              message='Making Cheese')
    self.assertEqual('Super-Cheese', result.name)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testRegionOperation(self):
    with api_mock.Client(self.client_class) as client:
      poller = compute_poller.Poller(client.instances)
      operation_ref = resources.REGISTRY.Create(
          _REGION_OPERATIONS_COLLECTION,
          project='mickey',
          region='florida',
          operation='operationX')
      instance_ref = resources.REGISTRY.Create(
          'compute.instances',
          project='mickey',
          zone='disney',
          instance='Super-Cheese')

      self.ExpectOperation(
          client.regionOperations, operation_ref,
          client.instances, instance_ref)
      result = waiter.WaitFor(poller=poller,
                              operation_ref=operation_ref,
                              message='Making Cheese')
    self.assertEqual('Super-Cheese', result.name)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testZoneOperation(self):
    with api_mock.Client(self.client_class) as client:
      poller = compute_poller.Poller(client.instances)
      operation_ref = resources.REGISTRY.Create(
          _ZONE_OPERATIONS_COLLECTION,
          project='mickey',
          zone='disney',
          operation='operationX')
      instance_ref = resources.REGISTRY.Create(
          'compute.instances',
          project='mickey',
          zone='disney',
          instance='Super-Cheese')

      self.ExpectOperation(
          client.zoneOperations, operation_ref,
          client.instances, instance_ref)
      result = waiter.WaitFor(poller=poller,
                              operation_ref=operation_ref,
                              message='Making Cheese')
    self.assertEqual('Super-Cheese', result.name)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testError(self):
    with api_mock.Client(self.client_class) as client:
      poller = compute_poller.Poller(client.instances)
      operation_ref = resources.REGISTRY.Create(
          _GLOBAL_OPERATIONS_COLLECTION,
          project='mickey',
          operation='operationX')
      instance_ref = resources.REGISTRY.Create(
          'compute.instances',
          project='mickey',
          zone='disney',
          instance='Super-Cheese')

      self.ExpectOperation(
          client.globalOperations, operation_ref,
          client.instances, instance_ref, error_msg='Something happened')
      with self.assertRaisesRegex(compute_poller.OperationErrors,
                                  r'Something happened'):
        waiter.WaitFor(poller=poller,
                       operation_ref=operation_ref,
                       message='Making Cheese')
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')


class BatchPollerTest(waiter_test_base.Base):

  def SetUp(self):
    self.api_version = 'v1'
    self.client_class = core_apis.GetClientClass('compute', self.api_version)
    self.messages = self.client_class.MESSAGES_MODULE
    status_enum = self.messages.Operation.StatusValueValuesEnum
    self.status_done = status_enum.DONE
    self.status_pending = status_enum.PENDING
    self.error_entry = self.messages.Operation.ErrorValue.ErrorsValueListEntry

    self.operation_x_ref = resources.REGISTRY.Create(
        _GLOBAL_OPERATIONS_COLLECTION, project='mickey', operation='operationX')

    self.operation_y_ref = resources.REGISTRY.Create(
        _GLOBAL_OPERATIONS_COLLECTION, project='mickey', operation='operationY')

    self.instance_x_ref = resources.REGISTRY.Create(
        'compute.instances',
        project='mickey', zone='disney', instance='Super-Cheese-X')

    self.instance_y_ref = resources.REGISTRY.Create(
        'compute.instances',
        project='mickey', zone='disney', instance='Super-Cheese-Y')

    self.adapter = client_adapter.ClientAdapter(self.api_version, no_http=True)
    self.batch_fake = waiter_test_base.OperationBatchFake(
        self.adapter.apitools_client.instances,
        'compute.instances',
        self.adapter.apitools_client.globalOperations)

  def testNoOperations(self):
    with mock.patch.object(
        client_adapter.ClientAdapter, 'BatchRequests',
        side_effect=self.batch_fake.BatchRequests) as batch_requests:

      poller = compute_poller.BatchPoller(
          self.adapter, self.adapter.apitools_client.instances)
      results = waiter.WaitFor(
          poller=poller,
          operation_ref=compute_poller.OperationBatch([]),
          message='Making Cheese')
    # Expecting a call from Poll and then GetResult
    self.assertEqual(2, batch_requests.call_count)
    self.assertEqual(0, len(results))
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testTwoOperations_FirstFinish(self):
    self.batch_fake.AddInstance(
        self.instance_x_ref, self.operation_x_ref, number_of_polls_to_done=1)
    self.batch_fake.AddInstance(
        self.instance_y_ref, self.operation_y_ref, number_of_polls_to_done=2)

    with mock.patch.object(
        client_adapter.ClientAdapter, 'BatchRequests',
        side_effect=self.batch_fake.BatchRequests) as batch_requests:

      poller = compute_poller.BatchPoller(
          self.adapter, self.adapter.apitools_client.instances)
      results = waiter.WaitFor(
          poller=poller,
          operation_ref=compute_poller.OperationBatch(
              [self.operation_x_ref, self.operation_y_ref]),
          message='Making Cheese')
    # Expected calls with following responses:
    #  1. X pending, Y Pending
    #  2. X done, Y pending
    #  3. X done, Y done
    #  4. Get X, Get Y
    self.assertEqual(4, batch_requests.call_count)
    self.assertEqual('Super-Cheese-X', results[0].name)
    self.assertEqual('Super-Cheese-Y', results[1].name)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testTwoOperations_OneWithErrorInPoll(self):
    self.batch_fake.AddInstance(
        self.instance_x_ref, self.operation_x_ref, number_of_polls_to_error=0)
    self.batch_fake.AddInstance(
        self.instance_y_ref, self.operation_y_ref, number_of_polls_to_done=2)

    with mock.patch.object(
        client_adapter.ClientAdapter, 'BatchRequests',
        side_effect=self.batch_fake.BatchRequests) as batch_requests:

      poller = compute_poller.BatchPoller(
          self.adapter, self.adapter.apitools_client.instances)
      with self.assertRaisesRegex(core_exceptions.MultiError,
                                  'HTTPError 444: Fake http error'):
        waiter.WaitFor(
            poller=poller,
            operation_ref=compute_poller.OperationBatch(
                [self.operation_x_ref, self.operation_y_ref]),
            message='Making Cheese')
    # Expecting single call as error occurs on first try.
    self.assertEqual(1, batch_requests.call_count)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testTwoOperations_OneWithErrorInGetResult(self):
    self.batch_fake.AddInstance(
        self.instance_x_ref, self.operation_x_ref,
        number_of_polls_to_done=0)
    self.batch_fake.AddInstance(
        self.instance_y_ref, self.operation_y_ref,
        number_of_polls_to_done=0, error_on_instance=True)

    with mock.patch.object(
        client_adapter.ClientAdapter, 'BatchRequests',
        side_effect=self.batch_fake.BatchRequests) as batch_requests:

      poller = compute_poller.BatchPoller(
          self.adapter, self.adapter.apitools_client.instances)
      with self.assertRaisesRegex(core_exceptions.MultiError,
                                  'HTTPError 444: Fake http error'):
        waiter.WaitFor(
            poller=poller,
            operation_ref=compute_poller.OperationBatch(
                [self.operation_x_ref, self.operation_y_ref]),
            message='Making Cheese')
    # Expecting twoo calls: poll and get result.
    self.assertEqual(2, batch_requests.call_count)
    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

if __name__ == '__main__':
  test_case.main()
