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
"""Unit tests for deployments cancel preview command."""

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base

DEPLOYMENT_NAME = 'deployment-name'
OPERATION_NAME = 'operation-12345-67890'
FINGERPRINT = '123456'
FINGERPRINT_ENCODED = 'MTIzNDU2'
NEW_FINGERPRINT = '654321'
NEW_FINGERPRINT_ENCODED = 'NjU0MzIx'
INVALID_FINGERPRINT_ERROR = 'fingerprint cannot be decoded.'


class DeploymentsCancelPreviewTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments cancel preview command."""

  def testDeploymentsCancelPreview(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.CancelPreview.Expect(
        request=self.messages.DeploymentmanagerDeploymentsCancelPreviewRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsCancelPreviewRequest=
            self.messages.DeploymentsCancelPreviewRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='cancelPreview',
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
            operationType='cancelPreview',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after cancel preview
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
    self.Run('deployment-manager deployments cancel-preview %s' %
             (DEPLOYMENT_NAME,))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCancelPreview_Async(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.CancelPreview.Expect(
        request=self.messages.DeploymentmanagerDeploymentsCancelPreviewRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsCancelPreviewRequest=
            self.messages.DeploymentsCancelPreviewRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.Run('deployment-manager deployments cancel-preview %s --async'
             %(DEPLOYMENT_NAME,))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputNotContains('completed successfully')
    self.AssertOutputContains('PENDING')

  def testDeploymentsCancelPreview_OperationError(self):
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.CancelPreview.Expect(
        request=self.messages.DeploymentmanagerDeploymentsCancelPreviewRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsCancelPreviewRequest=
            self.messages.DeploymentsCancelPreviewRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='cancelPreview',
              status='PENDING',
          )
      )
    # WaitForOperation throws an error after doing one final poll and seeing
    # errors set in the operation.
    error_string = 'Cancel preview failed - DEPLOYED'
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='DONE',
            error=self.messages.Operation.ErrorValue(
                errors=[
                    self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                        # Error returned when the preview operation to cancel
                        # has already completed.
                        message=error_string,
                        code='CONDITION_NOT_MET',
                    )
                ]
            )
        )
    )
    try:
      self.Run('deployment-manager deployments cancel-preview %s' %
               (DEPLOYMENT_NAME,))
      self.fail('Expected gcloud error for cancel preview operation with error')
    except exceptions.Error as e:
      self.assertTrue(error_string in e.message)
      self.assertTrue(OPERATION_NAME in e.message)
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)

  def testDeploymentsCancelPreview_NoFingerprintFromService(self):
    self.expectBasicDeploymentGet(fingerprint='')
    self.mocked_client.deployments.CancelPreview.Expect(
        request=self.messages.DeploymentmanagerDeploymentsCancelPreviewRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsCancelPreviewRequest=
            self.messages.DeploymentsCancelPreviewRequest(
                fingerprint='',
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='cancelPreview',
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
            operationType='cancelPreview',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after cancel preview
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
    self.Run('deployment-manager deployments cancel-preview %s' %
             (DEPLOYMENT_NAME,))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCancelPreview_WithFingerprint(self):
    self.mocked_client.deployments.CancelPreview.Expect(
        request=self.messages.DeploymentmanagerDeploymentsCancelPreviewRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            deploymentsCancelPreviewRequest=
            self.messages.DeploymentsCancelPreviewRequest(
                fingerprint=FINGERPRINT,
            ),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='cancelPreview',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    for _ in range(2):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='cancelPreview',
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
            operationType='cancelPreview',
            status='DONE',
        )
    )
    # On operation success, list call to display resources after cancel preview
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
    self.Run('deployment-manager deployments cancel-preview %s --fingerprint %s'
             %(DEPLOYMENT_NAME, FINGERPRINT_ENCODED))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCancelPreview_WithInvalidFingerprint(self):
    try:
      self.Run('deployment-manager deployments cancel-preview '
               + DEPLOYMENT_NAME + ' --fingerprint invalid')
      self.fail('Expected invalid fingerprint error')
    except calliope_exceptions.InvalidArgumentException as e:
      self.assertTrue('Invalid value for [--fingerprint]' in e.message)
      self.assertTrue(INVALID_FINGERPRINT_ERROR in e.message)

  def testDeploymentsCancelPreview_ErrorGettingFingerprint(self):
    error_string = 'messed up'
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        exception=http_error.MakeHttpError(500, error_string)
    )
    try:
      self.Run('deployment-manager deployments cancel-preview %s' %
               (DEPLOYMENT_NAME,))
      self.fail('Expected HttpException when deployments get failed.')
    except api_exceptions.HttpException as e:
      self.assertTrue(error_string in e.message)
    self.AssertErrNotContains(NEW_FINGERPRINT_ENCODED)

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
