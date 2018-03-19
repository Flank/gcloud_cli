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

"""Unit tests for resources describe command."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base

messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

DEPLOYMENT_NAME = 'deployment-name'
RESOURCE_NAME = 'resource-name'
RESOURCE_ID = 12345


class ResourcesDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for resources describe command."""

  # TODO(b/36051084): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createResource(self):
    """Helper function to create a simple resource.

    Returns:
      Resource with name and id set.
    """
    return messages.Resource(
        name=RESOURCE_NAME,
        id=RESOURCE_ID,
    )

  def testResourcesDescribe(self):
    self.mocked_client.resources.Get.Expect(
        request=messages.DeploymentmanagerResourcesGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            resource=RESOURCE_NAME,
        ),
        response=self.createResource()
    )
    self.Run('deployment-manager resources describe ' + RESOURCE_NAME
             + ' --deployment ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(RESOURCE_NAME)
    self.AssertOutputContains(str(RESOURCE_ID))

  def testResourcesDescribe_WithErrors(self):
    errors = ['error-string ' + c for c in ['a', 'b', 'c']]
    resource_with_errors = self.createResource()
    resource_with_errors.update = messages.ResourceUpdate(
        error=messages.ResourceUpdate.ErrorValue(
            errors=[
                messages.ResourceUpdate.ErrorValue.ErrorsValueListEntry(
                    message=error,
                    code=str(409),
                )
                for error in errors
            ]
        )
    )
    self.mocked_client.resources.Get.Expect(
        request=messages.DeploymentmanagerResourcesGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            resource=RESOURCE_NAME,
        ),
        response=resource_with_errors
    )
    self.Run('deployment-manager resources describe ' + RESOURCE_NAME
             + ' --deployment ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(RESOURCE_NAME)
    self.AssertOutputContains(str(RESOURCE_ID))
    for error in errors:
      self.AssertOutputContains(error)

if __name__ == '__main__':
  test_case.main()
