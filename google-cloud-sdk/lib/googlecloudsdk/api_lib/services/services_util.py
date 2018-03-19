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

"""Common helper methods for Services commands."""

from apitools.base.py import encoding

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry


OP_BASE_CMD = 'gcloud services operations '
OP_DESCRIBE_CMD = OP_BASE_CMD + 'describe {0}'
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
SERVICES_COLLECTION = 'servicemanagement.services'


def GetMessagesModule():
  # pylint:disable=protected-access
  return apis_internal._GetMessagesModule('servicemanagement', 'v1')


def GetClientInstance():
  # pylint:disable=protected-access
  return apis_internal._GetClientInstance('servicemanagement', 'v1')


def GetEndpointsServiceName():
  return 'endpoints.googleapis.com'


def GetServiceManagementServiceName():
  return 'servicemanagement.googleapis.com'


def GetValidatedProject(project_id):
  """Validate the project ID, if supplied, otherwise return the default project.

  Args:
    project_id: The ID of the project to validate. If None, gcloud's default
                project's ID will be returned.

  Returns:
    The validated project ID.
  """
  if project_id:
    properties.VALUES.core.project.Validate(project_id)
  else:
    project_id = properties.VALUES.core.project.Get(required=True)
  return project_id


def GetEnabledListRequest(project_id):
  return GetMessagesModule().ServicemanagementServicesListRequest(
      consumerId='project:' + project_id
  )


def GetAvailableListRequest():
  return GetMessagesModule().ServicemanagementServicesListRequest()


def ProcessOperationResult(result, async=False):
  """Validate and process Operation outcome for user display.

  Args:
    result: The message to process (expected to be of type Operation)'
    async: If False, the method will block until the operation completes.

  Returns:
    The processed Operation message in Python dict form
  """
  op = GetProcessedOperationResult(result, async)
  if async:
    cmd = OP_WAIT_CMD.format(op.get('name'))
    log.status.Print('Asynchronous operation is in progress... '
                     'Use the following command to wait for its '
                     'completion:\n {0}'.format(cmd))
  else:
    cmd = OP_DESCRIBE_CMD.format(op.get('name'))
    log.status.Print('Operation finished successfully. '
                     'The following command can describe '
                     'the Operation details:\n {0}'.format(cmd))
  return op


def GetProcessedOperationResult(result, async=False):
  """Validate and process Operation result message for user display.

  This method checks to make sure the result is of type Operation and
  converts the StartTime field from a UTC timestamp to a local datetime
  string.

  Args:
    result: The message to process (expected to be of type Operation)'
    async: If False, the method will block until the operation completes.

  Returns:
    The processed message in Python dict form
  """
  if not result:
    return

  messages = GetMessagesModule()

  RaiseIfResultNotTypeOf(result, messages.Operation)

  result_dict = encoding.MessageToDict(result)

  if not async:
    op_name = result_dict['name']
    op_ref = resources.REGISTRY.Parse(
        op_name,
        collection='servicemanagement.operations')
    log.status.Print(
        'Waiting for async operation {0} to complete...'.format(op_name))
    result_dict = encoding.MessageToDict(WaitForOperation(
        op_ref, GetClientInstance()))

  return result_dict


def RaiseIfResultNotTypeOf(test_object, expected_type, nonetype_ok=False):
  if nonetype_ok and test_object is None:
    return
  if not isinstance(test_object, expected_type):
    raise TypeError('result must be of type %s' % expected_type)


def WaitForOperation(operation_ref, client):
  """Waits for an operation to complete.

  Args:
    operation_ref: A reference to the operation on which to wait.
    client: The client object that contains the GetOperation request object.

  Raises:
    TimeoutError: if the operation does not complete in time.
    OperationErrorException: if the operation fails.

  Returns:
    The Operation object, if successful. Raises an exception on failure.
  """
  WaitForOperation.operation_response = None
  messages = GetMessagesModule()
  operation_id = operation_ref.operationsId

  def _CheckOperation(operation_id):  # pylint: disable=missing-docstring
    request = messages.ServicemanagementOperationsGetRequest(
        operationsId=operation_id,
    )

    result = client.operations.Get(request)

    if result.done:
      WaitForOperation.operation_response = result
      return True
    else:
      return False

  # Wait for no more than 30 minutes while retrying the Operation retrieval
  try:
    retry.Retryer(exponential_sleep_multiplier=1.1, wait_ceiling_ms=10000,
                  max_wait_ms=30*60*1000).RetryOnResult(
                      _CheckOperation, [operation_id], should_retry_if=False,
                      sleep_ms=1500)
  except retry.MaxRetrialsException:
    raise exceptions.TimeoutError('Timed out while waiting for '
                                  'operation {0}. Note that the operation '
                                  'is still pending.'.format(operation_id))

  # Check to see if the operation resulted in an error
  if WaitForOperation.operation_response.error is not None:  # pytype: disable=none-attr
    raise exceptions.OperationErrorException(
        'The operation with ID {0} resulted in a failure.'.format(operation_id))

  # If we've gotten this far, the operation completed successfully,
  # so return the Operation object
  return WaitForOperation.operation_response
