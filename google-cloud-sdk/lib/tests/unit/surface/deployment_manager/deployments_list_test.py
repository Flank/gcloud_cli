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

"""Unit tests for deployments list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin


DEPLOYMENT_NAME = 'deployment-name'
DEPLOYMENT_ID = 12345


class DeploymentsListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments list command."""

  # TODO(b/36050342): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createDeployment(self, identifier=None):
    """Helper function to create a simple deployment.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Deployment with name and id set.
    """
    if identifier is not None:
      name = DEPLOYMENT_NAME + str(identifier)
      deployment_id = identifier
    else:
      name = DEPLOYMENT_NAME
      deployment_id = DEPLOYMENT_ID
    return self.messages.Deployment(
        name=name,
        id=deployment_id
    )

  def testDeploymentsList(self):
    num_deployments = 10
    self.mocked_client.deployments.List.Expect(
        request=self.messages.DeploymentmanagerDeploymentsListRequest(
            project=self.Project()
        ),
        response=self.messages.DeploymentsListResponse(
            deployments=[self.createDeployment(i)
                         for i in range(num_deployments)]
        )
    )
    self.Run('deployment-manager deployments list')
    for i in range(num_deployments):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(DEPLOYMENT_NAME + str(i))

  def testDeploymentsList_EmptyList(self):
    self.mocked_client.deployments.List.Expect(
        request=self.messages.DeploymentmanagerDeploymentsListRequest(
            project=self.Project()
        ),
        response=self.messages.DeploymentsListResponse()
    )
    self.Run('deployment-manager deployments list')
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testDeploymentsList_EmptySimpleList(self):
    self.mocked_client.deployments.List.Expect(
        request=self.messages.DeploymentmanagerDeploymentsListRequest(
            project=self.Project()
        ),
        response=self.messages.DeploymentsListResponse()
    )
    self.Run('deployment-manager deployments list --simple-list')
    self.AssertOutputEquals('')

  def testDeploymentsList_SimpleList(self):
    num_deployments = 10
    self.mocked_client.deployments.List.Expect(
        request=self.messages.DeploymentmanagerDeploymentsListRequest(
            project=self.Project()
        ),
        response=self.messages.DeploymentsListResponse(
            deployments=[self.createDeployment(i)
                         for i in range(num_deployments)]
        )
    )
    self.Run('deployment-manager deployments list --simple-list')
    expected_output = '\n'.join(
        [DEPLOYMENT_NAME + str(i) for i in range(num_deployments)]) + '\n'
    self.AssertOutputEquals(expected_output)

  def testDeploymentsList_Limit(self):
    num_deployments = 10
    limit = 5
    self.mocked_client.deployments.List.Expect(
        request=self.messages.DeploymentmanagerDeploymentsListRequest(
            project=self.Project(),
        ),
        response=self.messages.DeploymentsListResponse(
            deployments=[self.createDeployment(i)
                         for i in range(num_deployments)]
        )
    )
    self.Run('deployment-manager deployments list --limit ' + str(limit))
    for i in range(limit):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(DEPLOYMENT_NAME + str(i))
    for i in range(limit, num_deployments):
      self.AssertOutputNotContains(str(i))
      self.AssertOutputNotContains(DEPLOYMENT_NAME + str(i))

if __name__ == '__main__':
  test_case.main()
