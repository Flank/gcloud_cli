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

"""Unit tests for api_lib.util.waiter module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os
import signal

from apitools.base.py import encoding
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class OperationException(Exception):
  pass


class Cheese(object):

  def __init__(self, name):
    self.name = name

  def __str__(self):
    return self.name


class MakeCheeseOperation(object):

  def __init__(self, name, done):
    self.name = name
    self.done = done

  def __str__(self):
    return '{0} {1}'.format(self.name, 'done' if self.done else 'not done')


class OperationPoller(waiter.OperationPoller):

  def __init__(self, retries=1, exception_on=None, ctrl_c_on=None):
    self.retries = retries
    self.count = 0
    self.exception_on = exception_on
    self.ctrl_c_on = ctrl_c_on

  def IsDone(self, operation):
    return operation.done

  def Poll(self, operation_ref):
    self.count += 1
    if self.exception_on == self.count:
      raise OperationException(
          'Operation failed on {0} retry'.format(self.count))
    if self.ctrl_c_on == self.count:
      os.kill(os.getpid(), signal.SIGINT)

    return MakeCheeseOperation(
        done=self.count >= self.retries,
        name='{0}-{1}'.format(operation_ref, self.count))

  def GetResult(self, operation):
    return Cheese(name='Super Cheese made by ' + operation.name)


class WaiterTest(waiter_test_base.Base):

  def testSuccessfulCase(self):
    result = waiter.WaitFor(poller=OperationPoller(10),
                            operation_ref='operation-X',
                            message='Making Cheese')
    self.assertEqual('Super Cheese made by operation-X-10', result.name)
    # With 0 jitter this should be at least that much for default retry params.
    self.assertLess(98300, self.curr_time)

    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testPollUntilDone(self):
    waiter.PollUntilDone(poller=OperationPoller(10),
                         operation_ref='operation-X')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testNoWaitCase(self):
    poller = OperationPoller(0)
    result = waiter.WaitFor(poller=poller,
                            operation_ref='operation-X',
                            message='Making Cheese')
    self.assertEqual('Super Cheese made by operation-X-1', result.name)
    self.assertLessEqual(1000, self.curr_time)

    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testException(self):
    with self.assertRaises(OperationException):
      waiter.WaitFor(poller=OperationPoller(10, exception_on=4),
                     operation_ref='operation-X',
                     message='Making Cheese')
    self.assertLess(8718, self.curr_time)

    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testTimeout_WaitLimit(self):
    with self.assertRaisesRegex(
        waiter.TimeoutError,
        r'Operation operation-X has not finished in 1800 seconds. '
        r'The operations may still be underway remotely and may still succeed; '
        r'use gcloud list and describe commands or '
        r'https://console.developers.google.com/ to check resource state.'):
      waiter.WaitFor(poller=OperationPoller(1000),
                     operation_ref='operation-X',
                     message='Making Cheese')

    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testTimeout_MaxRetries(self):
    with self.assertRaisesRegex(waiter.TimeoutError,
                                r'Operation operation-X has not finished in 4 '
                                r'seconds after max 2 retrials'):
      waiter.WaitFor(poller=OperationPoller(1000),
                     operation_ref='operation-X',
                     message='Making Cheese',
                     max_retrials=2,
                     jitter_ms=0)

    self.AssertOutputEquals('')
    self.AssertErrContains('Making Cheese')

  def testCtrlC(self):
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                r'Aborting wait for operation operation-X.'):
      waiter.WaitFor(poller=OperationPoller(1000, ctrl_c_on=3),
                     operation_ref='operation-X',
                     message='Making Cheese')

    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
{"ux": "PROGRESS_TRACKER", "message": "Making Cheese", "status": "INTERRUPTED"}
""")


class CloudOperationTest(waiter_test_base.CloudOperationsBase):
  # One of many apis supporting standard operations.
  API_NAME = 'bigtableadmin'
  API_VERSION = 'v2'
  RESULT_SERVICE = 'projects_instances'
  OPERATIONS_COLLECTION = API_NAME + '.operations'

  def SetUp(self):
    self.client_class = core_apis.GetClientClass(
        self.API_NAME, self.API_VERSION)

  def testSuccessfulCase(self):
    with api_mock.Client(self.client_class) as client:
      result_service = getattr(client, self.RESULT_SERVICE)
      operation_service = client.operations

      operation_ref = resources.REGISTRY.Create(
          self.OPERATIONS_COLLECTION, operationsId='operationX')

      self.ExpectOperation(operation_service, 'operations/operationX',
                           result_service, 'theinstance')

      poller = waiter.CloudOperationPoller(result_service, operation_service)
      result = waiter.WaitFor(poller=poller,
                              operation_ref=operation_ref,
                              message='Making it')
      self.assertEqual('theinstance', result.name)
      self.assertLessEqual(1000, self.curr_time)

      self.AssertOutputEquals('')
      self.AssertErrContains('Making it')

  def testOperationError(self):
    with api_mock.Client(self.client_class) as client:
      result_service = getattr(client, self.RESULT_SERVICE)
      operation_service = client.operations

      operation_ref = resources.REGISTRY.Create(
          self.OPERATIONS_COLLECTION, operationsId='operationX')

      self.ExpectOperation(operation_service, 'operations/operationX',
                           result_service=None, result_name='theinstance',
                           error_msg='Something happened')

      poller = waiter.CloudOperationPoller(result_service, operation_service)

      with self.assertRaisesRegex(waiter.OperationError,
                                  r'Something happened'):
        waiter.WaitFor(poller=poller,
                       operation_ref=operation_ref,
                       message='Making it')


class CloudOperationNoResourcesTest(waiter_test_base.CloudOperationsBase):
  # One of the ML APIs that supports non-resource-creating operations.
  API_NAME = 'speech'
  API_VERSION = 'v1'
  OPERATIONS_COLLECTION = API_NAME + '.operations'

  def SetUp(self):
    self.client_class = core_apis.GetClientClass(
        self.API_NAME, self.API_VERSION)

  def testSuccessfulCase(self):
    with api_mock.Client(self.client_class) as client:
      operation_service = client.operations

      operation_ref = resources.REGISTRY.Create(
          self.OPERATIONS_COLLECTION, operationsId='operationX')

      self.ExpectOperation(operation_service, 'operationX',
                           None, 'resultX')

      poller = waiter.CloudOperationPollerNoResources(
          operation_service,
          get_name_func=lambda x: x.operationsId)
      result = waiter.WaitFor(poller=poller,
                              operation_ref=operation_ref,
                              message='Making it')
      self.assertEqual({'name': 'resultX'}, encoding.MessageToPyValue(result))
      self.assertLessEqual(1000, self.curr_time)

      self.AssertOutputEquals('')
      self.AssertErrContains('Making it')

  def testOperationError(self):
    with api_mock.Client(self.client_class) as client:
      operation_service = client.operations

      operation_ref = resources.REGISTRY.Create(
          self.OPERATIONS_COLLECTION, operationsId='operationX')

      self.ExpectOperation(operation_service, 'operationX',
                           result_service=None, result_name='resultX',
                           error_msg='Something happened')

      poller = waiter.CloudOperationPollerNoResources(
          operation_service,
          get_name_func=lambda x: x.operationsId)

      with self.assertRaisesRegex(waiter.OperationError,
                                  r'Something happened'):
        waiter.WaitFor(poller=poller,
                       operation_ref=operation_ref,
                       message='Making it')

if __name__ == '__main__':
  test_case.main()
