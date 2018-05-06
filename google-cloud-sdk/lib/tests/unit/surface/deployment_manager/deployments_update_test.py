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

"""Unit tests for deployments update command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base
import six
from six.moves import range  # pylint: disable=redefined-builtin


DEPLOYMENT_NAME = 'deployment-name'
DESCRIPTION = 'deployment-description'
UPDATE_DESCRIPTION = 'update-description'
MANIFEST_NAME = 'manifest-name'
MANIFEST_URL = 'google.com/' + MANIFEST_NAME
FINGERPRINT = b'123456'
FINGERPRINT_ENCODED = 'MTIzNDU2'
NEW_FINGERPRINT = b'654321'
NEW_FINGERPRINT_ENCODED = 'NjU0MzIx'
INVALID_FINGERPRINT_ERROR = 'fingerprint cannot be decoded.'

OPERATION_NAME = 'operation-12345-67890'
CURRENT_LABELS = {'key1': 'val2', 'key2': 'val2', 'key3': 'val4'}
UPDATE_LABELS = 'key1=val1,key4=val4'
REMOVE_LABELS = 'key3,key4'
NEW_LABELS = {'key1': 'val1', 'key2': 'val2'}


class DeploymentsUpdateTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments update command."""

  def testDeploymentsUpdate_DefaultArgs(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')

    self.AssertErrNotContains('Note: maximum of %s resources are shown, please '
                              'use list command to show all of the resources.'
                              % dm_api_util.MAX_RESOURCE_TO_DISPLAY)
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))
    if self.track is base.ReleaseTrack.ALPHA:
      for i in range(4):
        self.AssertOutputContains('action_name-' + str(i))
      self.AssertOutputContains('RUNTIME_POLICIES')
      self.AssertOutputContains('UPDATE_ON_CHANGE')
      self.AssertOutputContains('DELETE, CREATE')
      self.AssertOutputContains('UPDATE_ALWAYS')
      self.AssertOutputContains('N/A')
    else:
      self.AssertOutputContains('INTENT')

    self.AssertOutputNotContains('description')

  def testDeploymentsUpdate_TruncatedResources(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    resource_count = dm_api_util.MAX_RESOURCE_TO_DISPLAY + 1
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources(resource_count=resource_count)
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
    self.AssertErrContains('Note: maximum of %s resources are shown, please '
                           'use describe command to show all of the resources.'
                           % dm_api_util.MAX_RESOURCE_TO_DISPLAY)
    self.AssertBasicOutputs()
    for i in range(dm_api_util.MAX_RESOURCE_TO_DISPLAY):
      self.AssertOutputContains('resource-{}'.format(i))
    self.AssertOutputNotContains('resource-{}'.format(resource_count))
    self.AssertOutputNotContains('description')

  def testDeploymentsUpdate_WithDescription(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml(
        description=DESCRIPTION)
    self.expectBasicDeploymentGet(description=DESCRIPTION)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_UpdateDescription(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml(
        description=UPDATE_DESCRIPTION)
    self.expectBasicDeploymentGet(description=DESCRIPTION)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --description ' + UPDATE_DESCRIPTION)
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_UpdateEmptyDescription(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet(description=DESCRIPTION)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --description \'\'')
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsLabelsUpdate_DefaultArgs(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml(labels=NEW_LABELS)
    self.expectBasicDeploymentGet(labels=CURRENT_LABELS)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments update %s --config %s '
             '--update-labels %s --remove-labels %s' %
             (DEPLOYMENT_NAME, self.getSimpleYamlConfigFilePath(),
              UPDATE_LABELS, REMOVE_LABELS))
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsLabelsUpdate_NoConfig(self):
    # Update deployment labels without providing config files or manifest
    deployment = self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        fingerprint=FINGERPRINT,
        labels=self.buildLabelEntry(NEW_LABELS),
    )
    self.expectBasicDeploymentGet(labels=CURRENT_LABELS)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(
        fingerprint=NEW_FINGERPRINT, labels=NEW_LABELS)
    self.Run('deployment-manager deployments update %s --update-labels %s '
             '--remove-labels %s' % (DEPLOYMENT_NAME, UPDATE_LABELS,
                                     REMOVE_LABELS))
    self.AssertErrContains('Update deployment metadata completed successfully.')
    self.AssertOutputContains(NEW_FINGERPRINT_ENCODED)
    self.AssertOutputContains('- key: key1\n  value: val1\n- key: key2\n  '
                              'value: val2\n')
    self.AssertOutputNotContains('PENDING')

  def testDeploymentsUpdate_NoManifest(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Deployment(
        )
    )

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsUpdate_NoOutputs(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.messages.Manifest(
            layout='',
        )
    )

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsUpdate_Async(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '" --async')
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputNotContains('completed successfully')
    self.AssertOutputNotContains('INTENT')
    self.AssertOutputContains('PENDING')

  def testDeploymentsUpdate_Policies(self):
    create_policy = 'ACQUIRE'
    delete_policy = 'ABANDON'
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.mocked_client.deployments.Update.Expect(
        request=self.messages.DeploymentmanagerDeploymentsUpdateRequest(
            project=self.Project(),
            deploymentResource=deployment,
            deployment=DEPLOYMENT_NAME,
            preview=False,
            createPolicy=(
                self.messages.DeploymentmanagerDeploymentsUpdateRequest.
                CreatePolicyValueValuesEnum(create_policy)),
            deletePolicy=(
                self.messages.DeploymentmanagerDeploymentsUpdateRequest.
                DeletePolicyValueValuesEnum(delete_policy)),
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='update',
            status='PENDING',
        )
    )
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update %s --config "%s" '
             '--create-policy %s --delete-policy %s'
             % (DEPLOYMENT_NAME, self.getSimpleYamlConfigFilePath(),
                create_policy, delete_policy))
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_InvalidPolicies(self):
    invalid_policy_name = 'INVALID_POLICY_NAME'
    for policy in ['--create-policy', '--delete-policy']:
      with self.AssertRaisesArgumentErrorRegexp(
          'argument {0}: Invalid choice: \'invalid-policy-name\''
          .format(policy)):
        self.Run('deployment-manager deployments update %s --config "%s" '
                 '%s %s' % (DEPLOYMENT_NAME, self.getSimpleYamlConfigFilePath(),
                            policy, invalid_policy_name))
    self.AssertErrNotContains(NEW_FINGERPRINT_ENCODED)

  def testDeploymentsUpdate_NoConfig(self):
    # Apply an already-previewed update.
    deployment = self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        fingerprint=FINGERPRINT,
        # No target config
    )
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME)
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsPreviewOnPreview_LabelsInPreview(self):
    # Preview an already-previewed deployment.
    # The labels in the preview(key2=val2) will be ignored.
    # Based on current labels(key1=val1), the expected labels is key1=val3.
    current_labels = {'key1': 'val1'}
    preview_labels = {'key2': 'val2'}
    update_labels = 'key1=val3'
    expected_label = {'key1': 'val3'}
    deployment = self.buildDeploymentObjectFromSimpleYaml(labels=expected_label)
    self.expectBasicDeploymentGet(
        labels=current_labels, update_labels_entry=preview_labels)
    self.expectUpdate(deployment=deployment, preview=True)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources(preview=True)
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update %s --config %s '
             '--update-labels %s --preview' %
             (DEPLOYMENT_NAME, self.getSimpleYamlConfigFilePath(),
              update_labels))
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_Preview(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment, preview=True)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources(preview=True)
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --preview')
    self.AssertBasicOutputs()
    self.AssertOutputContains('IN_PREVIEW')
    self.AssertOutputContains('INTENT')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))
    if self.track is base.ReleaseTrack.ALPHA:
      for i in range(4):
        self.AssertOutputContains('action_name-' + str(i))
      self.AssertOutputContains('DELETE/NOT_RUN')
      self.AssertOutputContains('CREATE_OR_ACQUIRE/TO_RUN')
      self.AssertOutputContains('UPDATE/TO_RUN')
      self.AssertOutputContains('ABANDON')

  def testDeploymentsUpdate_OperationError(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()

    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate(normal_termination=False)

    # WaitForOperation throws an error after doing one final poll and seeing
    # errors set in the operation.
    error_string = 'baderrormessage'
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='update',
            status='DONE',
            error=self.messages.Operation.ErrorValue(
                errors=[
                    self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                        message=error_string)
                ]
            )
        )
    )
    try:
      self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
               + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')

      self.fail('Expected gcloud error for update operation with error.')
    except exceptions.Error as e:
      self.assertTrue(error_string in str(e))
      self.assertTrue(OPERATION_NAME in str(e))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)

  def testDeploymentsUpdate_WithWarning(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()

    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate(normal_termination=False)

    # WaitForOperation throws an error after doing one final poll and seeing
    # errors set in the operation.
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='update',
            status='DONE',
            warnings=[
                self.messages.Operation.WarningsValueListEntry(
                    message='warning')
            ]))
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME +
             ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('WARNING: Update operation operation-12345-67890 '
                           'completed with warnings:')
    self.AssertErrContains('message: warning')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def setupManifestTest(self, initial_yaml, updated_yaml):
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.messages.Manifest(
            config={'content': initial_yaml}
        )
    )
    deployment = self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        target=self.messages.TargetConfiguration(
            config=self.messages.ConfigFile(content=updated_yaml),
        ),
        fingerprint=FINGERPRINT,
    )
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()

    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[self.messages.Resource(name='resource')]
        )
    )
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

  def testDeploymentsUpdate_MissingFingerprint(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml(fingerprint=b'')
    self.expectBasicDeploymentGet(fingerprint=None)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')

    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_WithFingerprint(self):
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --fingerprint ' + FINGERPRINT_ENCODED)

    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_WithInvalidFingerprint(self):
    self.expectBasicDeploymentGet()
    try:
      self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
               + ' --config "' + self.getSimpleYamlConfigFilePath()
               + '" --fingerprint invalid')
      self.fail('Expected invalid fingerprint error')
    except calliope_exceptions.InvalidArgumentException as e:
      self.assertTrue('Invalid value for [--fingerprint]' in str(e))
      self.assertTrue(INVALID_FINGERPRINT_ERROR in str(e))

  def testDeploymentsUpdate_ErrorGettingFingerprint(self):
    error_string = 'messed up'
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        exception=http_error.MakeHttpError(500, error_string)
    )
    try:
      self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
               + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')
      self.fail('Expected HttpException when deployments get failed.')
    except api_exceptions.HttpException as e:
      self.assertTrue(error_string in e.message)
    self.AssertErrNotContains(NEW_FINGERPRINT_ENCODED)

  def expectBasicDeploymentGet(self, fingerprint=FINGERPRINT, description=None,
                               labels=None, update_labels_entry=None,
                               credential=None):
    """Helper method to set the expectation that a DeploymentGetRequest call.

    Args:
      fingerprint: fingerprint value in the deployment response. Default
          if the global FINGERPRINT.
      description: the deployment description in the response.
      labels: A dict of label key=value to create label entry of the deployment.
      update_labels_entry: A dict of label key=value in the update field.
      credential: Deployment credential in the response.
    """
    if credential:
      self.mocked_client.deployments.Get.Expect(
          request=self.messages.DeploymentmanagerDeploymentsGetRequest(
              project=self.Project(),
              deployment=DEPLOYMENT_NAME,
          ),
          response=self.messages.Deployment(
              name=DEPLOYMENT_NAME,
              fingerprint=fingerprint,
              description=description,
              manifest=MANIFEST_NAME,
              labels=self.buildLabelEntry(labels),
              credential=credential,
              update=self.messages.DeploymentUpdate(
                  labels=self.buildUpdateLabelEntry(update_labels_entry)
              ) if update_labels_entry else None,
          )
      )
    else:
      self.mocked_client.deployments.Get.Expect(
          request=self.messages.DeploymentmanagerDeploymentsGetRequest(
              project=self.Project(),
              deployment=DEPLOYMENT_NAME,
          ),
          response=self.messages.Deployment(
              name=DEPLOYMENT_NAME,
              fingerprint=fingerprint,
              description=description,
              manifest=MANIFEST_NAME,
              labels=self.buildLabelEntry(labels),
              update=self.messages.DeploymentUpdate(
                  labels=self.buildUpdateLabelEntry(update_labels_entry)
              ) if update_labels_entry else None,
          )
      )

  def expectOperationGetPollAndTerminate(self, pending_count=2,
                                         normal_termination=True):
    """Helper to set the expectation that Operations.Get will be called.

    Args:
      pending_count: Number of times the operation will return
          PENDING_OPERATION
      normal_termination: Boolean to indicate that a successful
          termination is expected. If this is set to false, then
          the caller is required to set their own expectation.
    """
    for _ in range(pending_count):
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='update',
              status='PENDING',
          )
      )

    if normal_termination:
      # Operation complete: one 'DONE' response to end poll
      self.mocked_client.operations.Get.Expect(
          request=self.messages.DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=OPERATION_NAME,
          ),
          response=self.messages.Operation(
              name=OPERATION_NAME,
              operationType='update',
              status='DONE',
          )
      )

  def expectDeploymentGetWithManifestUrlResponse(self):
    """Helper to set the expectation that Deployments.Get will be called.

    The response will be a deployment with only a manifest url.
    """
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Deployment(
            manifest=MANIFEST_URL
        )
    )

  def expectUpdate(self, deployment, preview=False):
    """Helper to set expectation that Deployments.Update will be called.

    Args:
      deployment: Deployment object for the update.
      preview: Boolean to indicate if this is a preview deployment. False
          by default.
    """
    self.mocked_client.deployments.Update.Expect(
        request=self.messages.DeploymentmanagerDeploymentsUpdateRequest(
            project=self.Project(),
            deploymentResource=deployment,
            deployment=DEPLOYMENT_NAME,
            preview=preview,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='update',
            status='PENDING',
        )
    )

  def expectResourceListWithResources(self,
                                      preview=False,
                                      resource_count=4,
                                      action_count=4):
    """Helper to set the expectation that Resources.List will be called.

    Args:
      preview: Optional boolean to specify if it is under preview
      resource_count: Number of resource created. They will be named
          resource-{0-3}. The default count is 4.
      action_count: Number of actions created. They will be named
          action_name-{0-3}. The default count is 4.
    """
    resource_list = [
        self.messages.Resource(
            name='resource-' + str(i),
            id=i,
            update=self.messages.ResourceUpdate(
                state='IN_PREVIEW', intent='UPDATE') if preview else None)
        for i in range(resource_count)
    ]
    if self.track is base.ReleaseTrack.ALPHA:
      runtime_policies = [['UPDATE_ON_CHANGE'], ['DELETE', 'CREATE'],
                          ['UPDATE_ALWAYS'], []]
      action_intent = ['DELETE', 'CREATE_OR_ACQUIRE', 'UPDATE', 'ABANDON']
      for i in range(action_count):
        resource_list.append(
            self.messages.Resource(
                name='action_name-' + str(i),
                id=i,
                runtimePolicies=runtime_policies[i],
                update=self.messages.ResourceUpdate(
                    runtimePolicies=runtime_policies[i],
                    state='IN_PREVIEW',
                    intent=action_intent[i]) if preview else None))
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(resources=resource_list))

  def AssertBasicOutputs(self):
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')

  def expectManifestGetRequestWithLayoutResponse(self):
    """Helper to set the expectation that a Manifests.Get be called.

    The response will contain a layout with an outputs section that has
    name = the-only-output and finalValue = successful-output.
    """
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.messages.Manifest(
            layout="""
              outputs:
              - name: the-only-output
                finalValue: successful-output
            """,
        )
    )

  def getSimpleYamlConfigFilePath(self):
    """All tests in this file use the same resource for tests.

    Returns:
      The simple.yaml Resource.
    """
    return self.Resource('tests',
                         'lib',
                         'surface',
                         'deployment_manager',
                         'test_data',
                         'simple_configs',
                         'simple.yaml')

  def buildDeploymentObjectFromSimpleYaml(self, fingerprint=FINGERPRINT,
                                          description=None, labels=None,
                                          credential=None):
    """Helper to use the common simple.yaml file to create a deployment object.

    Args:
      fingerprint: The fingerprint of the deployment returned. Default
          is the global FINGERPRINT.
      description: The description of the deployment.
      labels: A dict of label key=value to create label entry of the deployment.
      credential: The credential to update.
    Returns:
      Deployment object constructed from the simple.yaml file.
    """
    with open(self.getSimpleYamlConfigFilePath()) as config_file:
      if credential:
        deployment = self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            target=self.messages.TargetConfiguration(
                config=self.messages.ConfigFile(content=config_file.read())
            ),
            fingerprint=fingerprint,
            description=description,
            labels=self.buildLabelEntry(labels),
            credential=credential
        )
      else:
        deployment = self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            target=self.messages.TargetConfiguration(
                config=self.messages.ConfigFile(content=config_file.read())
            ),
            fingerprint=fingerprint,
            description=description,
            labels=self.buildLabelEntry(labels),
        )
    return deployment

  def buildLabelEntry(self, labels=None):
    """Helper to create DeploymentLabelEntry.

    Args:
      labels: A dict of label key=value to create label entry of the deployment.
    Returns:
      A list of DeploymentLabelEntry object.
    """
    label_entry = []
    if labels:
      label_entry = [self.messages.DeploymentLabelEntry(key=k, value=v)
                     for k, v in sorted(six.iteritems(labels))]
    return label_entry

  def buildUpdateLabelEntry(self, labels=None):
    """Helper to create DeploymentUpdateLabelEntry.

    Args:
      labels: A dict of label key=value to create label entry of the deployment.
    Returns:
      A list of DeploymentUpdateLabelEntry object.
    """
    label_entry = []
    if labels:
      label_entry = [self.messages.DeploymentUpdateLabelEntry(key=k, value=v)
                     for k, v in sorted(six.iteritems(labels))]
    return label_entry


class DeploymentsUpdateAlphaTest(DeploymentsUpdateTest):
  """Unit tests for deployments update alpha command."""

  def SetUp(self):
    self.TargetingAlphaCommandTrack()
    self.TargetingAlphaApi()

  def testDeploymentsUpdate_ManifestId(self):
    test_content = 'my configuration'
    imports = [self.messages.ImportFile(name='import1',
                                        content='import content')]

    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.messages.Manifest(
            config={'content': test_content},
            imports=imports,
        )
    )
    deployment = self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        target=self.messages.TargetConfiguration(
            config=self.messages.ConfigFile(content=test_content),
            imports=imports,
        ),
        fingerprint=FINGERPRINT,
    )
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()

    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[self.messages.Resource(name='resource')]
        )
    )
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update %s '
             '--manifest-id "%s"' % (DEPLOYMENT_NAME, MANIFEST_NAME))
    self.AssertErrContains(NEW_FINGERPRINT_ENCODED)

  def testDeploymentsUpdate_ErrorWithManifestAndConfigFlags(self):
    """Setting both the --manifest-id and --config flags is not supported."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument --config: At most one of --composite-type | --config | '
        '--manifest-id | --template may be specified.'):
      self.Run('deployment-manager deployments update foo '
               '--manifest-id bar --config "%s"'
               % (self.getSimpleYamlConfigFilePath()))

  def testDeploymentsUpdate_ManifestIdErrorWithProperties(self):
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        # respond with multiple resources, which is not supported with the
        # manifest-id argument.
        response=self.messages.Manifest(
            config={'content': """
resources:
  - name: vm1
  - name: vm2"""
                   }
        )
    )

    try:
      self.Run('deployment-manager deployments update %s '
               '--manifest-id %s --properties=foo=bar'
               % (DEPLOYMENT_NAME, MANIFEST_NAME))
      self.fail('Expected HttpException when deployments get failed.')
    except exceptions.Error as e:
      self.assertTrue('single resource' in str(e))
    self.AssertErrNotContains(NEW_FINGERPRINT_ENCODED)

  def testDeploymentsUpdate_ManifestIdWithProperties(self):
    # warning: yaml as strings is frail since the yaml formatter may not
    # return properties in the order we expect.
    initial_yaml = """resources:
- name: vm1
"""
    updated_yaml = """resources:
- name: vm1
  properties:
    foo: bar
"""
    self.setupManifestTest(initial_yaml=initial_yaml,
                           updated_yaml=updated_yaml)

    self.Run('deployment-manager deployments update %s '
             '--manifest-id "%s" --properties=foo=bar'
             % (DEPLOYMENT_NAME, MANIFEST_NAME))

  def testDeploymentsUpdate_ManifestIdWithPropertiesOverwrite(self):
    # warning: yaml as strings is frail since the yaml formatter may not
    # return properties in the order we expect.
    initial_yaml = """resources:
- name: vm1
  properties:
    foo: bar
"""
    updated_yaml = """resources:
- name: vm1
  properties:
    foo: bot
"""
    self.setupManifestTest(initial_yaml=initial_yaml,
                           updated_yaml=updated_yaml)

    self.Run('deployment-manager deployments update %s '
             '--manifest-id "%s" --properties=foo=bot'
             % (DEPLOYMENT_NAME, MANIFEST_NAME))

  def testDeploymentsUpdate_EmptyCredential(self):
    current_service_account_entry = self.messages.ServiceAccount(
        email='my-app@appspot.gserviceaccount.com')
    current_credential_entry = self.messages.Credential(
        serviceAccount=current_service_account_entry)
    deployment = self.buildDeploymentObjectFromSimpleYaml()
    self.expectBasicDeploymentGet(credential=current_credential_entry)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT,
                                  credential=current_credential_entry)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath() + '"')

    self.AssertBasicOutputs()
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_OverwriteCurrentCredential(self):
    current_service_account_entry = self.messages.ServiceAccount(
        email='my-app@appspot.gserviceaccount.com')
    current_credential_entry = self.messages.Credential(
        serviceAccount=current_service_account_entry)

    credential_input = 'serviceAccount:my-other-app@appspot.gserviceaccount.com'
    update_service_account_entry = self.messages.ServiceAccount(
        email='my-other-app@appspot.gserviceaccount.com')
    update_credential_entry = self.messages.Credential(
        serviceAccount=update_service_account_entry)
    deployment = self.buildDeploymentObjectFromSimpleYaml(
        credential=update_credential_entry)
    self.expectBasicDeploymentGet(credential=current_credential_entry)
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT,
                                  credential=update_credential_entry)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --credential ' + credential_input)

    self.AssertBasicOutputs()
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_WithCredential_hasType(self):
    credential_input = 'serviceAccount:my-other-app@appspot.gserviceaccount.com'
    service_account_entry = self.messages.ServiceAccount(
        email='my-other-app@appspot.gserviceaccount.com')
    credential_entry = self.messages.Credential(
        serviceAccount=service_account_entry)
    deployment = self.buildDeploymentObjectFromSimpleYaml(
        credential=credential_entry)
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --credential ' + credential_input)

    self.AssertBasicOutputs()
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsUpdate_WithCredential_noType(self):
    credential_input = 'my-app@appspot.gserviceaccount.com'
    error_string = ('credential must start with serviceAccount: '
                    'or use PROJECT_DEFAULT.')
    self.expectBasicDeploymentGet()

    try:
      self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
               + ' --config "' + self.getSimpleYamlConfigFilePath()
               + '" --credential ' + credential_input)
    except calliope_exceptions.InvalidArgumentException as e:
      self.assertTrue(error_string in str(e))

  def testDeploymentsUpdate_WithCredential_projectDefault(self):
    credential_input = 'PROJECT_DEFAULT'
    credential_entry = self.messages.Credential(useProjectDefault=True)
    deployment = self.buildDeploymentObjectFromSimpleYaml(
        credential=credential_entry)
    self.expectBasicDeploymentGet()
    self.expectUpdate(deployment=deployment)
    self.expectBasicDeploymentGet(fingerprint=NEW_FINGERPRINT)
    self.expectOperationGetPollAndTerminate()
    self.expectResourceListWithResources()
    self.expectDeploymentGetWithManifestUrlResponse()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments update ' + DEPLOYMENT_NAME
             + ' --config "' + self.getSimpleYamlConfigFilePath()
             + '" --credential ' + credential_input)

    self.AssertBasicOutputs()
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))


class DeploymentsUpdateBetaTest(DeploymentsUpdateTest):
  """Unit tests for deployments update beta command."""

  def SetUp(self):
    self.TargetingBetaCommandTrack()
    self.TargetingV2BetaApi()


if __name__ == '__main__':
  test_case.main()
