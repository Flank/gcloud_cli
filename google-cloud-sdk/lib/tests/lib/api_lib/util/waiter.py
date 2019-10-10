# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Test support for methods which utilizes waiter module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error

from six.moves import range  # pylint: disable=redefined-builtin


class Base(sdk_test_base.WithOutputCapture):
  """Mixin test class to setup mocks and cleanup for tests exercising waiter."""

  def SetUp(self):
    self.curr_time = 0
    self.StartObjectPatch(retry, '_GetCurrentTimeMs',
                          side_effect=lambda: self.curr_time)

    def _SleepMs(miliseconds):
      self.curr_time += int(miliseconds)

    self.StartObjectPatch(retry, '_SleepMs', side_effect=_SleepMs)
    self.StartObjectPatch(progress_tracker, '_SleepSecs')
    self.StartObjectPatch(waiter, '_SleepMs', side_effect=_SleepMs)

  def TearDown(self):
    # Wait for the ProgressTracker ticker thread to end.
    self.JoinAllThreads(timeout=2)


class CloudOperationsBase(Base):

  def ExpectOperation(self, operation_service, operation_name,
                      result_service, result_name, retries=1, error_msg=None):
    request_type = operation_service.GetRequestType('Get')
    response_type = operation_service.GetResponseType('Get')
    response = response_type(
        done=True,
        response=response_type.ResponseValue(
            additionalProperties=[
                response_type.ResponseValue.AdditionalProperty(
                    key='name',
                    value=extra_types.JsonValue(
                        string_value=result_name)),
            ],
        ),
    )
    for _ in range(retries):
      if error_msg:
        response.error = operation_service.client.MESSAGES_MODULE.Status(
            code=1, message=error_msg)
      operation_service.Get.Expect(
          request=request_type(name=operation_name),
          response=response)

    result = None
    if result_service:
      result_request_type = result_service.GetRequestType('Get')
      result_response_type = result_service.GetResponseType('Get')

      result = result_response_type(name=result_name)
      result_service.Get.Expect(
          request=result_request_type(name=result_name),
          response=result,
      )

    return result


class OperationBatchFake(object):
  """Processes batch request simulating configured scenario."""

  def __init__(self, instance_service, instance_collection, operation_service):
    self._instance_service = instance_service
    self._instance_collection = instance_collection
    self._operation_service = operation_service
    messages = operation_service.client.MESSAGES_MODULE
    self.status_enum = messages.Operation.StatusValueValuesEnum
    self._instances = {}  # Instance to operation map.
    self._operation_status = {}
    self._error_instances = []

  def AddInstance(self, instance_ref, operation_ref,
                  number_of_polls_to_done=1,
                  number_of_polls_to_error=None,
                  error_on_instance=False):
    """Declares that instance is created, polled and result retrieved."""
    self._instances[operation_ref.Name()] = instance_ref
    if number_of_polls_to_error is not None:
      http_err = http_error.MakeHttpError(code=444, message='Fake http error',
                                          url=instance_ref.SelfLink())
      self._operation_status[operation_ref.Name()] = iter(
          [self.status_enum.PENDING] * number_of_polls_to_error
          + [api_exceptions.HttpException(http_err)])
    else:
      self._operation_status[operation_ref.Name()] = iter(
          [self.status_enum.PENDING] * number_of_polls_to_done
          + [self.status_enum.DONE])
    if error_on_instance:
      self._error_instances.append(instance_ref)

  def BatchRequests(self, requests, errors_to_collect):
    """Simulates client_adapter.BatchRequestMethod.

    self.batch_fake = OperationBatchFake(...)
    with mock.patch.object(
        client_adapter.ClientAdapter, 'BatchRequests',
        side_effect=self.batch_fake.BatchRequests)
        ...

    Args:
      requests: list(tuple(service, method, payload)).
      errors_to_collect: list, ooutput only, for new errors.

    Returns:
      list of response payloads.
    Raises:
      ValueError: if request is not on initially specified service.
    """
    responses = []
    for r in requests:
      service, method, payload = r
      response_type = service.GetResponseType(method)
      if service == self._instance_service:
        # Create a reference from given Get request.
        payload_data = {field.name: payload.get_assigned_value(field.name)
                        for field in payload.all_fields()}
        instance_ref = resources.REGISTRY.Create(
            self._instance_collection, **payload_data)
        if instance_ref in self._error_instances:
          http_err = http_error.MakeHttpError(code=444,
                                              message='Fake http error',
                                              url=instance_ref.SelfLink())
          errors_to_collect.append(api_exceptions.HttpException(http_err))
        responses.append(
            response_type(name=instance_ref.Name(),
                          selfLink=instance_ref.SelfLink()))
      elif service == self._operation_service:
        instance_ref = self._instances[payload.operation]
        operation_status = next(self._operation_status[payload.operation])
        if isinstance(operation_status, Exception):
          errors_to_collect.append(operation_status)
          responses.append(None)  # Need this entry so that responses can be
                                  # matched with requests.
        else:
          responses.append(
              response_type(name=instance_ref.Name(),
                            status=operation_status,
                            targetLink=instance_ref.SelfLink()))
      else:
        raise ValueError('Unexpected service {0}'.format(service.__class__))

    return responses
