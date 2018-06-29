# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Unit tests for deployments create command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin

DEPLOYMENT_NAME = 'deployment-name'
FINGERPRINT = b'123456'
MANIFEST_NAME = 'manifest-name'
FINGERPRINT_ENCODED = 'MTIzNDU2'
OPERATION_NAME = 'operation-12345-67890'


class DeploymentsCreateTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments create command."""

  # TODO(b/36053576): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def testDeploymentsCreate(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrNotContains('Note: maximum of %s resources are shown, please '
                              'use list command to show all of the resources.'
                              % dm_api_util.MAX_RESOURCE_TO_DISPLAY)
    self.AssertBasicOutputs()
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))
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

  def testDeploymentsCreate_WithWarning(self):
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    for _ in range(2):
      # Operation is pending for a while
      self.ExpectOperationGet()

    # WaitForOperation throws an error, so create does not do an extra Get
    # call on the Operation. Only one 'DONE' get to expect here.
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='create',
            status='DONE',
            warnings=[
                self.messages.Operation.WarningsValueListEntry(
                    message='warning')
            ]))
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME +
             ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('WARNING: Create operation operation-12345-67890 '
                           'completed with warnings:')
    self.AssertErrContains('message: warning')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCreate_TruncatedResources(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    resource_count = dm_api_util.MAX_RESOURCE_TO_DISPLAY + 1
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet(resource_count=resource_count)
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains('Note: maximum of %s resources are shown, please '
                           'use describe command to show all of the resources.'
                           % dm_api_util.MAX_RESOURCE_TO_DISPLAY)
    self.AssertBasicOutputs()
    self.AssertOutputContains('COMPLETED')
    if self.track is base.ReleaseTrack.ALPHA:
      self.AssertOutputContains('RUNTIME_POLICIES')
    else:
      self.AssertOutputContains('INTENT')
    for i in range(dm_api_util.MAX_RESOURCE_TO_DISPLAY):
      self.AssertOutputContains('resource-' + str(i))
    self.AssertOutputNotContains('resource-' + str(resource_count))

  def testDeploymentsCreate_withLabel(self):
    label_input = 'key1=val1'
    label_entry = [self.messages.DeploymentLabelEntry(key='key1', value='val1')]
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(
        config_file_path, labels=label_entry)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet(labels=label_entry)
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,),
        response=self.messages.Manifest(layout='\n'))
    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME +
             ' --config "' + config_file_path + '" --labels ' + label_input)
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputNotContains('PENDING')
    if self.track is base.ReleaseTrack.ALPHA:
      self.AssertOutputContains('RUNTIME_POLICIES')
    else:
      self.AssertOutputContains('INTENT')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCreate_NoResources(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[]
        )
    )
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputNotContains('PENDING')

    self.AssertOutputNotContains('COMPLETED')
    self.AssertOutputNotContains('STATE')
    self.AssertOutputNotContains('TYPE')
    self.AssertOutputNotContains('ERRORS')
    self.AssertOutputNotContains('INTENT')

    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')

  def testDeploymentsCreate_NoOutputs(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()

    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
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

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsCreate_NoResourcesNoOutputs(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[]
        )
    )
    self.expectBasicDeploymentGet()
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

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputNotContains('PENDING')

    self.AssertOutputNotContains('COMPLETED')
    self.AssertOutputNotContains('STATE')
    self.AssertOutputNotContains('TYPE')
    self.AssertOutputNotContains('ERRORS')

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsCreate_NoManifest(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()

    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name which is empty.
    self.expectResourceGet()
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Deployment(
        )
    )

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputNotContains('PENDING')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsCreate_WithDescription(self):
    description = 'description string'
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(
        config_file_path, description=description)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"'
             + ' --description "' + description + '"')
    self.AssertBasicOutputs()
    self.AssertOutputContains('COMPLETED')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCreate_Async(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --async --config "' + config_file_path + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputContains('PENDING')

  def testDeploymentsCreate_WithError(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')
    error_string = 'baderrormessage'
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    for _ in range(2):
      # Operation is pending for a while
      self.ExpectOperationGet()

    # WaitForOperation throws an error, so create does not do an extra Get
    # call on the Operation. Only one 'DONE' get to expect here.
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='create',
            status='DONE',
            error=self.messages.Operation.ErrorValue(errors=[
                self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                    message=error_string)
            ]),
            warnings=[
                self.messages.Operation.WarningsValueListEntry(
                    message='warning')
            ]))
    try:
      self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
               + ' --config "' + config_file_path + '"')

      self.fail('Expected gcloud error for create operation with error.')
    except exceptions.OperationError as e:
      self.assertTrue(error_string in str(e))
      self.assertTrue(OPERATION_NAME in str(e))
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertOutputNotContains('WARNING:')

  def testDeploymentsCreate_WithErrorAndRollback(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')
    error_string = 'baderrormessage'
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    # insert
    self.expectDeploymentInsert(deployment)

    # get fingerprint
    self.expectBasicDeploymentGet()

    for _ in range(2):
      # Operation is pending for a while
      self.ExpectOperationGet()

    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='create',
            status='DONE',
            error=self.messages.Operation.ErrorValue(
                errors=[
                    self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                        message=error_string)
                ]
            )
        )
    )

    delete_operation_name = 'operation-delete'
    self.mocked_client.deployments.Delete.Expect(
        request=self.messages.DeploymentmanagerDeploymentsDeleteRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Operation(
            name=delete_operation_name,
            operationType='delete',
            status='PENDING',
        )
    )

    for _ in range(2):
      # Operation is pending for a while
      self.ExpectOperationGet('PENDING', delete_operation_name)

    for _ in range(2):
      # Operation complete: one 'DONE' response to end poll, one Get to display.
      self.ExpectOperationGet('DONE', delete_operation_name)

    # Get finished create operation to display.
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=OPERATION_NAME,
        ),
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='create',
            status='DONE',
            error=self.messages.Operation.ErrorValue(
                errors=[
                    self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                        message=error_string)
                ]
            )
        )
    )

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --automatic-rollback-on-error --config "' + config_file_path
             + '"')

    self.AssertErrContains("""MTIzNDU2""")
    self.AssertErrContains("""\
{"ux": "PROGRESS_TRACKER", "message": "Waiting for create [operation-12345-67890]", "status": "FAILURE"}
WARNING: There was an error deploying deployment-name:
Error in Operation [operation-12345-67890]: errors:
- message: baderrormessage

`--automatic-rollback-on-error` flag was supplied; deleting failed deployment
{"ux": "PROGRESS_TRACKER", "message": "Waiting for delete [operation-delete]", "status": "SUCCESS"}
""", normalize_space='.')

    self.AssertOutputEquals(
        """NAME                   TYPE    STATUS  TARGET  ERRORS  WARNINGS
operation-12345-67890  create  DONE            []      []
operation-delete       create  DONE            []      []
""")

  def testDeploymentsCreate_SuccessWithAutoRollback(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --automatic-rollback-on-error  --config "' + config_file_path
             + '"')
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrNotContains('Note: maximum of %s resources are shown, please '
                              'use list command to show all of the resources.'
                              % dm_api_util.MAX_RESOURCE_TO_DISPLAY)
    self.AssertOutputContains('COMPLETED')
    self.AssertBasicOutputs()
    if self.track is base.ReleaseTrack.ALPHA:
      self.AssertOutputContains('RUNTIME_POLICIES')
    else:
      self.AssertOutputContains('INTENT')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCreate_WithImports(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple_with_import.yaml')
    # Import contents don't matter here since they are not sent to server
    # for expansion.
    import_names = ['simple_bad_imports.yaml', 'simple.yaml']
    imports = []
    for import_name in import_names:
      fname = self.Resource('tests',
                            'lib',
                            'surface',
                            'deployment_manager',
                            'test_data',
                            'simple_configs', import_name)
      with open(fname, 'r') as import_file:
        imports.append(
            self.messages.ImportFile(
                name=import_name,
                content=import_file.read(),
            )
        )
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path,
                                                          imports=imports)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '"')
    self.AssertBasicOutputs()
    self.AssertOutputContains('COMPLETED')
    if self.track is base.ReleaseTrack.ALPHA:
      self.AssertOutputContains('RUNTIME_POLICIES')
    else:
      self.AssertOutputContains('INTENT')
    for i in range(4):
      self.AssertOutputContains('resource-' + str(i))

  def testDeploymentsCreate_InvalidConfigName(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'nonexistent_config_file.yaml')
    try:
      self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
               + ' --config "' + config_file_path + '"')
      self.fail('Expected ImportFileError for nonexistent import file.')
    except exceptions.ConfigError as e:
      self.assertTrue('config' in str(e))
      self.assertTrue(config_file_path in str(e))
    self.AssertErrNotContains(FINGERPRINT_ENCODED)

  def testDeploymentsCreate_WithImportError(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple_bad_imports.yaml')
    try:
      self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
               + ' --config "' + config_file_path + '"')
      self.fail('Expected ImportFileError for nonexistent import file.')
    except exceptions.ConfigError as e:
      self.assertTrue('Unable to read file' in str(e))
      self.assertTrue('filethatdoesnotexist.py' in str(e))
    self.AssertErrNotContains(FINGERPRINT_ENCODED)

  def testDeploymentsCreate_Preview(self):
    config_file_path = self.Resource('tests',
                                     'lib',
                                     'surface',
                                     'deployment_manager',
                                     'test_data',
                                     'simple_configs',
                                     'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment, preview=True)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()

    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet(preview=True)
    self.expectBasicDeploymentGet()
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments create ' + DEPLOYMENT_NAME
             + ' --config "' + config_file_path + '" --preview')
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

  def testDeploymentsCreate_OldProperties(self):
    template_name = 'string_properties'

    with open(self.getResource(template_name + '.yaml'), 'r') as config_file:
      with open(
          self.getResource(template_name + '.jinja'), 'r') as template_file:
        with open(self.getResource(
            template_name + '.jinja.schema'), 'r') as schema_file:
          deployment = self.messages.Deployment(
              name=DEPLOYMENT_NAME,
              target=self.messages.TargetConfiguration(
                  config=self.messages.ConfigFile(content=config_file.read()),
                  imports=[
                      self.messages.ImportFile(
                          name=template_name + '.jinja',
                          content=template_file.read()),
                      self.messages.ImportFile(
                          name=template_name + '.jinja.schema',
                          content=schema_file.read()
                      )
                  ]
              ),
          )
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.Run(('deployment-manager deployments create %s --async --template "%s"'
              ''' --properties "a=foo,b=3,c=true,d='3'"''') %
             (DEPLOYMENT_NAME, self.getResource(template_name + '.jinja')))
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputContains('PENDING')
    # Use ^regex$ to confirm that warning is printed exactly once.
    self.AssertErrMatches(
        r"^WARNING: Delimiter '=' is deprecated for properties flag. "
        r"Use ':' instead.$")

  def testDeploymentsCreate_NewProperties(self):
    template_name = 'typed_properties'
    config_file_path = ['tests',
                        'lib',
                        'surface',
                        'deployment_manager',
                        'test_data',
                        'simple_configs']

    with open(self.Resource(
        *(config_file_path + [template_name + '.yaml'])), 'r') as config_file:
      with open(self.Resource(
          *(config_file_path + [template_name + '.jinja'])), 'r'
               ) as template_file:
        with open(self.Resource(*(
            config_file_path + [template_name + '.jinja.schema'])), 'r'
                 ) as schema_file:
          deployment = self.messages.Deployment(
              name=DEPLOYMENT_NAME,
              target=self.messages.TargetConfiguration(
                  config=self.messages.ConfigFile(content=config_file.read()),
                  imports=[
                      self.messages.ImportFile(
                          name=template_name + '.jinja',
                          content=template_file.read()),
                      self.messages.ImportFile(
                          name=template_name + '.jinja.schema',
                          content=schema_file.read()
                      )
                  ]
              ),
          )
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.Run(('deployment-manager deployments create %s --async --template "%s"'
              ' --properties "a:foo,b:3,c:true,d:\'3\'"')
             % (DEPLOYMENT_NAME, self.getResource(template_name + '.jinja')))
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputContains('PENDING')
    self.AssertErrNotContains('deprecated')
    self.AssertErrNotContains('WARNING')

  def getResource(self, template_name):
    config_file_path = ['tests',
                        'lib',
                        'surface',
                        'deployment_manager',
                        'test_data',
                        'simple_configs']
    return self.Resource(*(config_file_path + [template_name]))

  def BuildDeploymentObjectFromConfigFile(self, config_file_path, imports=None,
                                          description=None, labels=None,
                                          credential=None):
    with open(config_file_path, 'r') as config_file:
      if credential:
        deployment = self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            target=self.messages.TargetConfiguration(
                config=self.messages.ConfigFile(content=config_file.read()),
                imports=imports if imports else [],
            ),
            description=description,
            labels=labels if labels else [],
            credential=credential
        )
      else:
        deployment = self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            target=self.messages.TargetConfiguration(
                config=self.messages.ConfigFile(content=config_file.read()),
                imports=imports if imports else [],
            ),
            description=description,
            labels=labels if labels else []
        )
    return deployment

  def expectDeploymentInsert(self,
                             deployment,
                             preview=False,
                             create_policy=None):
    request = self.messages.DeploymentmanagerDeploymentsInsertRequest(
        project=self.Project(),
        deployment=deployment,
        preview=preview,
    )
    if create_policy is not None:
      request.createPolicy = (
          self.messages.DeploymentmanagerDeploymentsInsertRequest.
          CreatePolicyValueValuesEnum(create_policy))
    self.mocked_client.deployments.Insert.Expect(
        request=request,
        response=self.messages.Operation(
            name=OPERATION_NAME,
            operationType='create',
            status='PENDING',
        ))

  def expectBasicDeploymentGet(self, fingerprint=FINGERPRINT, description=None,
                               labels=None):
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
            labels=labels if labels else [],
        )
    )

  def ExpectOperationGet(self, status='PENDING', operation_name=OPERATION_NAME):
    self.mocked_client.operations.Get.Expect(
        request=self.messages.DeploymentmanagerOperationsGetRequest(
            project=self.Project(),
            operation=operation_name,
        ),
        response=self.messages.Operation(
            name=operation_name,
            operationType='create',
            status=status,
        )
    )

  def ExpectOperationGetPollAndTerminate(self, pending_count=2):
    for _ in range(pending_count):
      self.ExpectOperationGet()

    # Operation complete: one 'DONE' response to end poll
    self.ExpectOperationGet('DONE')

  def expectResourceGet(self, preview=False, resource_count=4, action_count=4):
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

  def expectManifestGetRequestWithLayoutResponse(self):
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

  def AssertBasicOutputs(self):
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrContains('completed successfully')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')


class DeploymentsCreateAlphaTest(DeploymentsCreateTest):
  """Unit tests for deployments create alpha command."""

  def SetUp(self):
    self.TargetingAlphaCommandTrack()
    self.TargetingAlphaApi()

  def testDeploymentsCreate_withCredential_hasType(self):
    credential_input = 'serviceAccount:my-other-app@appspot.gserviceaccount.com'
    service_account_entry = self.messages.ServiceAccount(
        email='my-other-app@appspot.gserviceaccount.com')
    credential_entry = self.messages.Credential(
        serviceAccount=service_account_entry)
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(
        config_file_path, credential=credential_entry)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,),
        response=self.messages.Manifest(layout='\n'))
    self.Run(
        'deployment-manager deployments create {} --config {} --credential {}'
        .format(DEPLOYMENT_NAME, config_file_path, credential_input))
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))

  def testDeploymentsCreate_withCredential_noType(self):
    credential_input = 'my-other-app@appspot.gserviceaccount.com'
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')
    error_string = ('credential must start with serviceAccount: '
                    'or use PROJECT_DEFAULT.')

    try:
      self.Run(
          'deployment-manager deployments create {} --config {} --credential {}'
          .format(DEPLOYMENT_NAME, config_file_path, credential_input))
    except calliope_exceptions.InvalidArgumentException as e:
      self.assertIn(error_string, str(e))

  def testDeploymentsCreate_withCredential_projectDefault(self):
    credential_input = 'PROJECT_DEFAULT'
    credential_entry = self.messages.Credential(useProjectDefault=True)
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')

    deployment = self.BuildDeploymentObjectFromConfigFile(
        config_file_path, credential=credential_entry)
    self.expectDeploymentInsert(deployment)
    self.expectBasicDeploymentGet()
    self.ExpectOperationGetPollAndTerminate()
    # Once the operation completes successfully, expect:
    # - A list call to display completed resources.
    # - A get deployment call to get the manifest name.
    # - A get manifest call to get the layout.
    self.expectResourceGet()
    self.expectBasicDeploymentGet()
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,),
        response=self.messages.Manifest(layout='\n'))
    self.Run(
        'deployment-manager deployments create {} --config {} --credential {}'
        .format(DEPLOYMENT_NAME, config_file_path, credential_input))
    self.AssertErrContains(FINGERPRINT_ENCODED)
    self.AssertErrContains(OPERATION_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputNotContains('PENDING')
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(4):
      self.AssertOutputContains('resource-{}'.format(i))


class DeploymentsCreateBetaTest(DeploymentsCreateTest):
  """Unit tests for deployments create beta command."""

  def SetUp(self):
    self.TargetingBetaCommandTrack()
    self.TargetingV2BetaApi()

  def testDeploymentsCreate_CreatePolicy(self):
    config_file_path = self.Resource('tests', 'lib', 'surface',
                                     'deployment_manager', 'test_data',
                                     'simple_configs', 'simple.yaml')
    create_policy = 'CREATE'
    deployment = self.BuildDeploymentObjectFromConfigFile(config_file_path)
    self.expectDeploymentInsert(deployment, create_policy=create_policy)
    self.expectBasicDeploymentGet()
    self.Run(
        'deployment-manager deployments create {} --async --create-policy={} '
        '--config {}'.format(DEPLOYMENT_NAME, create_policy, config_file_path))


if __name__ == '__main__':
  test_case.main()
