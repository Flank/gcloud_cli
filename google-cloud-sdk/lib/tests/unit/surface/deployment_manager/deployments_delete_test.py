# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Unit tests for deployments delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin

DEPLOYMENT_NAME = 'deployment-name'


class DeploymentsDeleteTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments delete command."""

  # TODO(b/36053577): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def testDeploymentsDelete(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deletePolicy=(self.messages
                          .DeploymentmanagerDeploymentsDeleteRequest
                          .DeletePolicyValueValuesEnum('ABANDON')),
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='delete',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='PENDING',
          )
      )
    for _ in range(2):
      # Operation complete: one 'DONE' response to end poll, one for delete
      # command error checking.
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='DONE',
          )
      )
    self.WriteInput('y\n')
    self.Run('deployment-manager deployments delete ' + DEPLOYMENT_NAME
             +  ' --delete-policy ABANDON')
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Delete operation operation-12345-67890 completed successfully.')

  def testDeploymentsDelete_WithWarning(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deletePolicy=(
                self.messages.DeploymentmanagerDeploymentsDeleteRequest.
                DeletePolicyValueValuesEnum('ABANDON')),
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='delete',
            status='PENDING',
        ))
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='PENDING',
          ))
    for _ in range(2):
      # Operation complete: one 'DONE' response to end poll, one for delete
      # command error checking.
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='DONE',
              warnings=[
                  self.messages.Operation.WarningsValueListEntry(
                      message='warning')
              ]))
    self.WriteInput('y\n')
    self.Run('deployment-manager deployments delete ' + DEPLOYMENT_NAME +
             ' --delete-policy ABANDON')
    self.AssertOutputEquals('')
    self.AssertErrContains('WARNING: Delete operation operation-12345-67890 '
                           'completed with warnings:')
    self.AssertErrContains('message: warning')

  def testDeploymentsDelete_Async(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='delete',
            status='PENDING',
        )
    )
    self.WriteInput('y\n')
    self.Run('deployment-manager deployments delete ' + DEPLOYMENT_NAME
             + ' --async')
    self.AssertOutputEquals('')
    self.AssertErrContains('deployment-name')

  def testDeploymentsDelete_Multiple(self):
    deployment_names = [DEPLOYMENT_NAME + '-' + str(i) for i in range(3)]
    operation_prefix = 'operation-'

    for deployment_name in deployment_names:
      operation_name = operation_prefix + deployment_name
      self.mocked_client.deployments.Delete.Expect(
          request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
              project=self.Project(),
              deployment=deployment_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='PENDING',
          )
      )
      for _ in range(2):
        # Operation is pending for a while
        self.mocked_client.operations.Get.Expect(
            request=self.messages.DeploymentmanagerOperationsGetRequest(
                project=self.Project(),
                operation=operation_name,
            ),
            response=self.messages.Operation(
                name=operation_name,
                operationType='delete',
                status='PENDING',
            )
        )
      for _ in range(2):
        # Operation complete: one 'DONE' respone to end poll, one for delete
        # command error checking.
        self.mocked_client.operations.Get.Expect(
            request=self.messages.DeploymentmanagerOperationsGetRequest(
                project=self.Project(),
                operation=operation_name,
            ),
            response=self.messages.Operation(
                name=operation_name,
                operationType='delete',
                status='DONE',
            )
        )
    self.WriteInput('y\n')
    self.Run('deployment-manager deployments delete '
             + ' '.join(deployment_names))
    for deployment_name in deployment_names:
      self.AssertErrContains(operation_prefix + deployment_name)
    self.AssertOutputEquals('')

  def testDeploymentsDelete_WithError(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='delete',
            status='PENDING',
        )
    )
    error_string = 'baderrormessage'
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='PENDING',
          )
      )
    for _ in range(2):
      # Operation complete: one 'DONE' respone to end poll, one for delete
      # command error checking.
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='DONE',
              error=self.messages.Operation.ErrorValue(
                  errors=[
                      self.messages.Operation.ErrorValue
                      .ErrorsValueListEntry(message=error_string)
                  ]
              )
          )
      )
    self.WriteInput('y\n')
    try:
      self.Run('deployment-manager deployments delete ' + DEPLOYMENT_NAME)
      self.fail('Expected gcloud error for delete operation with error.')
    except core_exceptions.MultiError:
      self.AssertErrContains('Delete operation ' + operation_name + ' failed.')
      self.AssertOutputEquals('')

  def testDeploymentsDelete_PromptNo(self):
    self.WriteInput('n\n')
    with self.assertRaisesRegex(exceptions.OperationError,
                                'Deletion aborted by user.'):
      self.Run('deployment-manager deployments delete ' + DEPLOYMENT_NAME)
    self.AssertErrContains(DEPLOYMENT_NAME)
    self.AssertErrContains('The following deployments will be deleted')

  def testDeploymentsDelete_PromptQuiet(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='delete',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='PENDING',
          )
      )
    for _ in range(2):
      # Operation complete: one 'DONE' respone to end poll, one for delete
      # command error checking.
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType='delete',
              status='DONE',
          )
      )
    self.Run('deployment-manager deployments delete -q ' + DEPLOYMENT_NAME)
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for delete [operation-12345-67890]')
    self.AssertErrContains(
        'Delete operation operation-12345-67890 completed successfully.')

if __name__ == '__main__':
  test_case.main()
