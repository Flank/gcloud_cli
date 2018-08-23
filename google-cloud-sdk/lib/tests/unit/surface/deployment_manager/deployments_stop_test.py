# -*- coding: utf-8 -*- #
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
"""Unit tests for deployments stop command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin

DEPLOYMENT_NAME = 'deployment-name'
OPERATION_NAME = 'operation-12345-67890'
FINGERPRINT = b'123456'
FINGERPRINT_ENCODED = 'MTIzNDU2'
INVALID_FINGERPRINT_ERROR = 'fingerprint cannot be decoded.'


class DeploymentsStopTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments stop command."""

  def testDeploymentsStop(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='stop',
              status='PENDING',
          )
      )
    # Operation complete: one 'DONE' response to end poll
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after stop
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[
                self.messages.Resource(
                    name='resource-' + str(i),
                    id=i,
                ) for i in range(4)]
        )
    )
    self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsStop_WithWarning(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=FINGERPRINT,),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        ))
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='stop',
              status='PENDING',
          ))
    # Operation complete: one 'DONE' response to end poll
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='DONE',
            warnings=[
                self.messages.Operation.WarningsValueListEntry(
                    message='warning')
            ]))
    # On operation success, list call to display resources after stop
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(resources=[
            self.messages.Resource(
                name='resource-' + str(i),
                id=i,
            ) for i in range(4)
        ]))
    self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('WARNING: Stop operation operation-12345-67890 '
                           'completed with warnings:')
    self.AssertErrContains('message: warning')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsStop_WithFingerprint(self):
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='stop',
              status='PENDING',
          )
      )
    # Operation complete: one 'DONE' response to end poll
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after stop
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[
                self.messages.Resource(
                    name='resource-' + str(i),
                    id=i,
                ) for i in range(4)]
        )
    )
    self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME
             + ' --fingerprint ' + FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsStop_WithInvalidFingerprint(self):
    try:
      self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME
               + ' --fingerprint invalid')
      self.fail('Expected invalid fingerprint error')
    except calliope_exceptions.InvalidArgumentException as e:
      self.assertTrue('Invalid value for [--fingerprint]' in str(e))
      self.assertTrue(INVALID_FINGERPRINT_ERROR in str(e))

  def testDeploymentsStop_Async(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        )
    )
    self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME
             + ' --async')
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputNotContains('completed successfully')
    self.AssertOutputContains('PENDING')

  def testDeploymentsStop_OperationError(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='stop',
              status='PENDING',
          )
      )
    # WaitForOperation throws an error after doing one final poll and seeing
    # errors set in the operation.
    error_string = 'Stop request failed - DEPLOYED'
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='DONE',
            error=self.messages.Operation.ErrorValue(
                errors=[
                    self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                        # Error returned when the operation to stop has
                        # already completed.
                        message=error_string,
                        code='CONDITION_NOT_MET',
                    )
                ]
            )
        )
    )
    try:
      self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME)
      self.fail('Expected gcloud error for stop operation with error.')
    except exceptions.Error as e:
      self.assertTrue(error_string in str(e))
      self.assertTrue(OPERATION_NAME in str(e))

  def testDeploymentsStop_NoFingerprintFromService(self):
    self.expectBasicDeploymentGet(fingerprint=b'')
    self.mocked_client.deployments.Stop.Expect(
        request=self.messages.DeploymentmanagerDeploymentsStopRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsStopRequest=self.messages.DeploymentsStopRequest(
                fingerprint=b'',
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='PENDING',
        )
    )
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='stop',
              status='PENDING',
          )
      )
    # Operation complete: one 'DONE' response to end poll
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='stop',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after stop
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[
                self.messages.Resource(
                    name='resource-' + str(i),
                    id=i,
                ) for i in range(4)]
        )
    )
    self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsStop_ErrorGettingFingerprint(self):
    error_string = 'messed up'
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        exception=http_error.MakeHttpError(500, error_string)
    )
    try:
      self.Run('deployment-manager deployments stop ' + DEPLOYMENT_NAME)
      self.fail('Expected HttpException when deployments get failed.')
    except api_exceptions.HttpException as e:
      self.assertTrue(error_string in e.message)

  def expectBasicDeploymentGet(self, fingerprint=FINGERPRINT):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            fingerprint=fingerprint,
        )
    )

if __name__ == '__main__':
  test_case.main()
