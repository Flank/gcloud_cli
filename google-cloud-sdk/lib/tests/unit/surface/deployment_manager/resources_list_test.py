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

"""Unit tests for resources list command."""

import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base

DEPLOYMENT_NAME = 'deployment-name'
RESOURCE_NAME = 'resource-name'
RESOURCE_ID = 12345
ACTION_NAME = 'action-name'
MANIFEST_NAME = 'manifest-1234'


class ResourcesListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for resources list command."""

  def testResourcesList(self):
    num_resources = 10
    self.setListResponse(num_resources=num_resources)
    self.Run('deployment-manager resources list --deployment '
             + DEPLOYMENT_NAME)
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      self.AssertOutputContains('COMPLETED')

  def testResourcesList_EmptySimpleList(self):
    self.setListResponse()
    self.Run('deployment-manager resources list --simple-list --deployment '
             + DEPLOYMENT_NAME)
    self.AssertOutputEquals('')

  def testResourcesList_EmptyList(self):
    self.setListResponse()
    self.Run('deployment-manager resources list --deployment '
             + DEPLOYMENT_NAME)
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testResourcesList_SimpleList(self):
    num_resources = 10
    self.setListResponse(num_resources=num_resources)
    self.Run('deployment-manager resources list --simple-list '
             '--deployment ' + DEPLOYMENT_NAME)
    expected_output = '\n'.join(
        [RESOURCE_NAME + str(i) for i in range(num_resources)]) + '\n'
    self.AssertOutputEquals(expected_output)

  def testResourcesList_Limit(self):
    num_resources = 10
    limit = 5
    self.setListResponse(num_resources=num_resources)
    self.Run('deployment-manager resources list --limit ' + str(limit)
             + ' --deployment ' + DEPLOYMENT_NAME)
    for i in range(limit):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
    for i in range(limit, num_resources):
      self.AssertOutputNotContains(str(i))
      self.AssertOutputNotContains(RESOURCE_NAME + str(i))

  def testResourcesList_WithPreview(self):
    num_resources = 10
    self.setListResponse(num_resources=num_resources, preview=True)
    self.Run('deployment-manager resources list --deployment '
             + DEPLOYMENT_NAME)
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      self.AssertOutputContains('IN_PREVIEW')
      self.AssertOutputContains('DELETE')

  def testResourcesList_WithErrors(self):
    num_resources = 10
    error_string = 'error'
    error_suffixes = ['a', 'b', 'c']
    resources = []
    for i in range(num_resources):
      resource = self.createResource(i)
      resource.update = self.messages.ResourceUpdate(
          error=self.messages.ResourceUpdate.ErrorValue(errors=[
              self.messages.ResourceUpdate.ErrorValue.ErrorsValueListEntry(
                  code='%s-%d-%s' % (error_string, i, error_suffix),)
              for error_suffix in error_suffixes
          ]))
      resources.append(resource)

    self.setListResponse(resources=resources)

    self.Run('deployment-manager resources list --deployment '
             + DEPLOYMENT_NAME)
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      for error_suffix in error_suffixes:
        self.AssertOutputContains('%s-%d-%s' % (error_string, i, error_suffix))

  def testListWithException(self):
    self.setListResponseWithError(
        http_error.MakeHttpError(code=404, message='quux'))
    with self.assertRaisesRegexp(
        api_exceptions.HttpException,
        re.compile(r'.*ResponseError: code=404, message=quux.*')):
      # only interested in the generator throwing an exception so we suppress
      # output
      results = self.Run('deployment-manager resources list '
                         '--user-output-enabled=false --deployment '
                         + DEPLOYMENT_NAME)
      for res in results:
        str(res)

  def testResourcesListNoDeploymentFlag(self):
    with self.assertRaisesRegexp(exceptions.ArgumentError,
                                 'argument --deployment is required'):
      self.Run('deployment-manager resources list')

  def createResource(self, identifier=None, preview=False):
    """Helper function to create a simple resource.

    Args:
      identifier: Optional integer to act as id and append to name.
      preview: Optional boolean to specify if the resource is in preview.

    Returns:
      Resource with name and id set.
    """
    if identifier is not None:
      name = RESOURCE_NAME + str(identifier)
      resource_id = identifier
    else:
      name = RESOURCE_NAME
      resource_id = RESOURCE_ID
    return self.messages.Resource(
        name=name,
        id=resource_id,
        update=self.messages.ResourceUpdate(
            state='IN_PREVIEW', intent='DELETE') if preview else None)

  def createActionResource(self, identifier=None, preview=False):
    """Helper function to create an action resource.

    Args:
      identifier: Optional integer to act as id and append to name.
      preview: Optional boolean to specify if the resource is in preview.

    Returns:
      Resource with name and id set.
    """
    if identifier is not None:
      name = ACTION_NAME + str(identifier)
      resource_id = identifier
    else:
      name = ACTION_NAME
      resource_id = RESOURCE_ID
    return self.messages.Resource(
        name=name,
        id=resource_id,
        runtimePolicies=['UPDATE_ON_CHANGE'],
        update=self.messages.ResourceUpdate(
            state='IN_PREVIEW',
            intent='UPDATE',
            runtimePolicies=['UPDATE_ON_CHANGE'])
        if preview else None)

  def setListResponse(self,
                      num_resources=0,
                      resources=None,
                      preview=False,
                      num_actions=0):
    if resources is None:
      resources = [
          self.createResource(i, preview) for i in range(num_resources)
      ]
      for i in xrange(num_actions):
        resources.append(self.createActionResource(i, preview))
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            filter=None,
            maxResults=500,
            orderBy=None,
            pageToken=None,
        ),
        response=self.messages.ResourcesListResponse(resources=resources))

  def setListResponseWithError(self, error):
    self.mocked_client.resources.List.Expect(
        request=self.messages.DeploymentmanagerResourcesListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            filter=None,
            maxResults=500,
            orderBy=None,
            pageToken=None,
        ),
        exception=error)


class ResourcesListAlphaTest(ResourcesListTest):
  """Unit tests for resources list alpha command."""

  def SetUp(self):
    self.TargetingAlphaCommandTrack()
    self.TargetingAlphaApi()

  def expectGetDeployment(self, preview=False):

    self.mocked_client.deployments.Get.Expect(
        request=self.messages.DeploymentmanagerDeploymentsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=self.messages.Deployment(
            name=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
            update=self.messages.DeploymentUpdate(manifest=MANIFEST_NAME)
            if preview else None))

  def expectAssertions(self, num_resources, num_actions=0, preview=False):
    self.AssertOutputContains('IN_PREVIEW' if preview else 'COMPLETED')
    self.AssertOutputNotContains('COMPLETED' if preview else 'IN_PREVIEW')
    self.AssertOutputContains('INTENT' if preview else 'RUNTIME_POLICIES')
    self.AssertOutputNotContains('RUNTIME_POLICIES' if preview else 'INTENT')
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      self.AssertOutputContains('DELETE' if preview else 'N/A')
    for i in range(num_actions):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(ACTION_NAME + str(i))
      self.AssertOutputContains('UPDATE/TO_RUN'
                                if preview else 'UPDATE_ON_CHANGE')

  def testResourcesList(self):
    self.expectGetDeployment()
    num_resources = 10
    num_action_resources = 5
    self.setListResponse(
        num_resources=num_resources, num_actions=num_action_resources)
    self.Run(
        'deployment-manager resources list --deployment ' + DEPLOYMENT_NAME)
    self.AssertOutputContains('COMPLETED')
    self.AssertOutputContains('RUNTIME_POLICIES')
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      self.AssertOutputContains('N/A')
    for i in range(num_action_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(ACTION_NAME + str(i))
      self.AssertOutputContains('UPDATE_ON_CHANGE')

  def testResourcesList_EmptyList(self):
    self.expectGetDeployment()
    super(ResourcesListAlphaTest, self).testResourcesList_EmptyList()

  def testResourcesList_Limit(self):
    self.expectGetDeployment()
    super(ResourcesListAlphaTest, self).testResourcesList_Limit()
    self.AssertOutputNotContains('INTENT')
    self.AssertOutputContains('RUNTIME_POLICIES')

  def testResourcesList_WithPreview(self):
    self.expectGetDeployment(preview=True)
    num_resources = 10
    num_actions = 5
    self.setListResponse(
        num_resources=num_resources, preview=True, num_actions=num_actions)
    self.Run(
        'deployment-manager resources list --deployment ' + DEPLOYMENT_NAME)
    self.AssertOutputContains('IN_PREVIEW')
    self.AssertOutputContains('INTENT')
    for i in range(num_resources):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(RESOURCE_NAME + str(i))
      self.AssertOutputContains('DELETE')
    for i in range(num_actions):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(ACTION_NAME + str(i))
      self.AssertOutputContains('UPDATE/TO_RUN')

  def testResourcesList_WithErrors(self):
    self.expectGetDeployment()
    super(ResourcesListAlphaTest, self).testResourcesList_WithErrors()

  def testListWithException(self):
    self.expectGetDeployment()
    super(ResourcesListAlphaTest, self).testListWithException()


class ResourcesListBetaTest(ResourcesListTest):
  """Unit tests for resources list beta command."""

  def SetUp(self):
    self.TargetingBetaCommandTrack()


if __name__ == '__main__':
  test_case.main()
