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

"""Unit tests for deployments describe command."""

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


DEPLOYMENT_NAME = 'deployment-name'
DEPLOYMENT_ID = 12345
MANIFEST_NAME = 'manifest-name'
DESCRIPTION = 'deployment-description'
SERVICE_ACCOUNT = 'my-app@appspot.gserviceaccount.com'
NUM_RESOURCES = 10
RESOURCE_RANGE = range(1, NUM_RESOURCES + 1)
ERROR_NAMES = ['a', 'b', 'c']
BASE_ERROR_CODE = 40
DEFAULT_LAYOUT = """
  outputs:
  - name: the-only-output
    finalValue: successful-output
"""


class DeploymentsDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments describe command."""

  # TODO(b/36051085): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createDeployment(self, identifier=None, description=None, labels=None):
    """Helper function to create a simple deployment.

    Args:
      identifier: Optional integer to act as id and append to name.
      description: The description of the deployment.
      labels: A dict of label key=value to create label entry of the deployment.

    Returns:
      Deployment with name, id set, description and labels.
    """
    if identifier is not None:
      name = DEPLOYMENT_NAME + str(identifier)
      deployment_id = identifier
    else:
      name = DEPLOYMENT_NAME
      deployment_id = DEPLOYMENT_ID
    labels_entry = []
    if labels:
      labels_entry = [self.messages.DeploymentLabelEntry(key=k, value=v)
                      for k, v in labels.iteritems()]
    return self.messages.Deployment(
        name=name,
        id=deployment_id,
        description=description,
        labels=labels_entry
    )

  def createDeploymentWithManifest(self, identifier=''):
    """Helper function to create a simple deployment with Manifest.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Deployment with name, manifest and id set.
    """

    return self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        id=DEPLOYMENT_ID if not identifier else identifier,
        manifest=MANIFEST_NAME
    )

  def createDeploymentWithCredential(self, identifier=''):
    """Helper function to create a simple deployment with credential.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Deployment with name, manifest, credential and id set.
    """
    service_account_entry = self.messages.ServiceAccount(email=SERVICE_ACCOUNT)
    credential_entry = self.messages.Credential(
        serviceAccount=service_account_entry)
    return self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        id=DEPLOYMENT_ID if not identifier else identifier,
        manifest=MANIFEST_NAME,
        credential=credential_entry,
    )

  def deploymentWithErrorsAndWarnings(self, errors, warning_messages):
    """Helper function to create a simple deployment with errors and warnings.

    Args:
      errors: A list of Operation.ErrorValue.ErrorsValueListEntry errors.
      warning_messages: A list of string warning messages.

    Returns:
      Deployment with name, id, manifest, errors, and warnings.
    """
    warnings = [
        self.messages.Operation.WarningsValueListEntry(message=message)
        for message in warning_messages
    ]
    return self.messages.Deployment(
        name=DEPLOYMENT_NAME,
        id=DEPLOYMENT_ID,
        operation=self.messages.Operation(
            error=self.messages.Operation.ErrorValue(errors=errors),
            warnings=warnings),
        manifest=MANIFEST_NAME)

  def expectResourceListWithResources(self, resource_count=4):
    """Helper to set the expectation that Resources.List will be called.

    Args:
      resource_count: Number of resource created. They will be named
          resource-{0-3}. The default count is 4.
    """
    resource_range = range(1, resource_count)
    resource_list = [
        self.messages.Resource(
            name='resource-' + str(i), id=i * 11111, type='type-' + str(i))
        for i in resource_range]
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
            maxResults=500,
            pageToken=None,
        ),
        response=self.messages.ResourcesListResponse(
            resources=resource_list
        )
    )

  def expectManifestGetRequestWithLayoutResponse(self, layout=DEFAULT_LAYOUT):
    """Helper to set the expectation that a Manifests.Get be called.

    By default, the response will contain a layout with an outputs section
    that has name = the-only-output and finalValue = successful-output.

    Args:
      layout: The layout to return
    """
    self.mocked_client.manifests.Get.Expect(
        request=self.messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.messages.Manifest(layout=layout,))

  def testDeploymentsDescribe_NoManifest(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
        ),
        response=self.createDeployment(
            description=DESCRIPTION, labels={'key1': 'val1'}))
    # Mock out the call to list resources in Display
    resource_count = 11
    self.expectResourceListWithResources(resource_count)
    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputContains('COMPLETED')
    if self.track is base.ReleaseTrack.ALPHA:
      self.AssertOutputNotContains('INTENT')
      self.AssertOutputContains('RUNTIME_POLICIES')
    else:
      self.AssertOutputContains('INTENT')
      self.AssertOutputNotContains('RUNTIME_POLICIES')
    self.AssertOutputContains('STATE')
    self.AssertOutputContains('TYPE')
    self.AssertOutputContains(DESCRIPTION)
    self.AssertOutputContains('labels:\n- key: key1\n  value: val1\n')
    for i in range(1, resource_count):
      self.AssertOutputContains('resource-' + str(i))
      self.AssertOutputContains('type-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))
    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsDescribe_NoOutputs(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=self.createDeploymentWithManifest()
    )

    resource_count = 11
    self.expectResourceListWithResources(resource_count)
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
    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputContains('STATE')
    self.AssertOutputContains('TYPE')
    for i in range(1, resource_count):
      self.AssertOutputContains('resource-' + str(i))
      self.AssertOutputContains('type-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))

    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsDescribe_WithOutputs(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=self.createDeploymentWithManifest()
    )

    # Mock out the call to list resources in Display
    resource_count = 11
    self.expectResourceListWithResources(resource_count)
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputContains('STATE')
    self.AssertOutputContains('TYPE')
    for i in range(1, resource_count):
      self.AssertOutputContains('resource-' + str(i))
      self.AssertOutputContains('type-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))

    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')

  def testDeploymentsDescribe_NoResourcesNoOutputs(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
        ),
        response=self.createDeploymentWithManifest()
    )
    # Mock out the call to list resources in Display, return no resources
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
            maxResults=500,
            pageToken=None,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[]
        )
    )
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
    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputNotContains('resource-')
    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsDescribe_NoResources(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
        ),
        response=self.createDeploymentWithManifest()
    )
    # Mock out the call to list resources in Display, return no resources
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
            maxResults=500,
            pageToken=None,
        ),
        response=self.messages.ResourcesListResponse(
            resources=[]
        )
    )
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputNotContains('resource-')
    self.AssertOutputNotContains('INTENT')
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')

  def basicDeploymentErrors(self):
    return [
        self.messages.Operation.ErrorValue.ErrorsValueListEntry(
            message=str(ii) + error,
            code=str(10 * BASE_ERROR_CODE + ii),
        ) for ii, error in enumerate(ERROR_NAMES)
    ]

  def deploymentsDescribeGoofs_ResourceSetup(self,
                                             errors=(),
                                             warnings=(),
                                             state='FAILED'):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
        ),
        response=self.deploymentWithErrorsAndWarnings(
            errors=errors, warning_messages=warnings))
    # Mock out the call to list resources in Display
    resource_list = [
        self.messages.Resource(
            name='resource-' + str(i),
            update=self.messages.ResourceUpdate(state=state),
        ) for i in RESOURCE_RANGE
    ]
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project(),
            maxResults=500,
            pageToken=None,
        ),
        response=self.messages.ResourcesListResponse(
            resources=resource_list
        )
    )

  def deploymentsDescribeErrors_BasicAsserts(self):
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.assertEquals(self.GetOutput().count('FAILED'), NUM_RESOURCES)
    for i in RESOURCE_RANGE:
      self.AssertOutputContains('resource-' + str(i))
    for ii, error in enumerate(ERROR_NAMES):
      self.AssertOutputContains(str(ii) + error)
      self.AssertOutputContains(str(10 * BASE_ERROR_CODE + ii))

  def testDeploymentsDescribe_ResourceErrors(self):
    self.deploymentsDescribeGoofs_ResourceSetup(
        errors=self.basicDeploymentErrors())
    self.expectManifestGetRequestWithLayoutResponse(layout='')

    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)

    self.deploymentsDescribeErrors_BasicAsserts()
    self.AssertOutputNotContains('OUTPUT')

  def testDeploymentsDescribe_ResourceErrorsWithOutputs(self):
    self.deploymentsDescribeGoofs_ResourceSetup(
        errors=self.basicDeploymentErrors())
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)

    self.deploymentsDescribeErrors_BasicAsserts()
    for i in RESOURCE_RANGE:
      self.AssertOutputContains('resource-' + str(i))
    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')

  def testDeploymentsDescribe_ResourceWarnings(self):
    self.deploymentsDescribeGoofs_ResourceSetup(
        warnings=['BIG WARNING'], state='SUCCESS')
    self.expectManifestGetRequestWithLayoutResponse()

    self.Run('deployment-manager deployments describe ' + DEPLOYMENT_NAME)

    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.assertEquals(self.GetOutput().count('SUCCESS'), NUM_RESOURCES)
    for i in RESOURCE_RANGE:
      self.AssertOutputContains('resource-' + str(i))
    self.AssertOutputContains('BIG WARNING')


class DeploymentsDescribeAlphaTest(DeploymentsDescribeTest):
  """Unit tests for deployments describe alpha command."""

  def SetUp(self):
    self.TargetingAlphaCommandTrack()
    self.TargetingAlphaApi()

  def expectResourceListWithResources(self,
                                      resource_count=4,
                                      action_count=4,
                                      preview=False):
    """Helper to set the expectation that Resources.List will be called.

    Args:
      resource_count: Number of resource created. They will be named
          resource-{0-3}. The default count is 4.
      action_count: Number of action resources created. They will be named
          resource-{0-3}. The default count is 4.
      preview: Optional boolean to specify if the deployment is in preview.
    """
    resource_list = [
        self.messages.Resource(
            name='resource-' + str(i),
            type='type-' + str(i),
            id=i,
            update=self.messages.ResourceUpdate(
                state='IN_PREVIEW', intent='UPDATE') if preview else None)
        for i in range(resource_count)
    ]
    for i in range(action_count):
      resource_list.append(
          self.messages.Resource(
              name='action_name-' + str(i),
              type='action-' + str(i),
              id=i,
              runtimePolicies=['UPDATE_ON_CHANGE'],
              update=self.messages.ResourceUpdate(
                  runtimePolicies=['UPDATE_ON_CHANGE'],
                  state='IN_PREVIEW',
                  intent='UPDATE') if preview else None))
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.ResourcesListResponse(resources=resource_list))

  def testDeploymentsDescribe_WithCredential(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=self.createDeploymentWithCredential()
    )

    # Mock out the call to list resources in Display
    resource_count = 11
    action_count = 5
    self.expectResourceListWithResources(resource_count, action_count)
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments describe {}'
             .format(DEPLOYMENT_NAME))
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputContains('STATE')
    self.AssertOutputNotContains('INTENT')
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in xrange(1, resource_count):
      self.AssertOutputContains('resource-' + str(i))
      self.AssertOutputContains('type-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))
    self.AssertOutputContains('N/A')
    for i in xrange(1, action_count):
      self.AssertOutputContains('action_name-' + str(i))
      self.AssertOutputContains('action-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))
    self.AssertOutputContains('UPDATE_ON_CHANGE')

    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')
    self.AssertOutputContains('credential:')
    self.AssertOutputContains('serviceAccount:')
    self.AssertOutputContains('email: ' + SERVICE_ACCOUNT)

  def testDeploymentsDescribe_DeploymentInPreview(self):
    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME, project=self.Project()),
        response=self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            update=self.messages.DeploymentUpdate(manifest=MANIFEST_NAME)))

    # Mock out the call to list resources in Display
    resource_count = 11
    action_count = 5
    self.expectResourceListWithResources(
        resource_count, action_count, preview=True)
    self.expectManifestGetRequestWithLayoutResponse()
    self.Run('deployment-manager deployments describe {}'
             .format(DEPLOYMENT_NAME))
    self.AssertOutputContains(DEPLOYMENT_NAME)
    self.AssertOutputContains('IN_PREVIEW')
    self.AssertOutputContains('STATE')
    self.AssertOutputNotContains('RUNTIME_POLICIES')
    self.AssertOutputContains('INTENT')
    for i in xrange(1, resource_count):
      self.AssertOutputContains('resource-' + str(i))
      self.AssertOutputContains('type-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))
      self.AssertOutputContains('UPDATE')
    for i in xrange(1, action_count):
      self.AssertOutputContains('action_name-' + str(i))
      self.AssertOutputContains('action-' + str(i))
      self.AssertOutputNotContains(str(i * 11111))
      self.AssertOutputContains('UPDATE/TO_RUN')

    self.AssertOutputContains('OUTPUT')
    self.AssertOutputContains('the-only-output')
    self.AssertOutputContains('successful-output')


class DeploymentsDescribeBetaTest(DeploymentsDescribeTest):
  """Unit tests for deployments describe beta command."""

  def SetUp(self):
    self.TargetingBetaCommandTrack()


if __name__ == '__main__':
  test_case.main()
