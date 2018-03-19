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

"""Unit tests for manifests describe command."""

from googlecloudsdk.api_lib.deployment_manager import exceptions as dm_exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base

messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

DEPLOYMENT_NAME = 'deployment-name'
MANIFEST_NAME = 'manifest-name'
MANIFEST_ID = 12345
CONFIG = 'config'


class ManifestsDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments list command."""

  def createManifest(self):
    """Helper function to create a simple manifest.

    Returns:
      Manifest with name, id, and evaluated config set.
    """
    return messages.Manifest(
        name=MANIFEST_NAME,
        id=MANIFEST_ID,
        config=messages.ConfigFile(content=CONFIG),
    )

  def testManifestsDescribe(self):
    self.mocked_client.manifests.Get.Expect(
        request=messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.createManifest()
    )
    self.Run('deployment-manager manifests describe ' + MANIFEST_NAME
             + ' --deployment ' + DEPLOYMENT_NAME)
    self.AssertOutputContains(MANIFEST_NAME)
    self.AssertOutputContains(str(MANIFEST_ID))
    self.AssertOutputContains(CONFIG)

  def testManifestsDescribeWithDeployment(self):
    self.mocked_client.deployments.Get.Expect(
        request=messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=messages.Deployment(
            name=DEPLOYMENT_NAME,
            id=123,
            manifest=MANIFEST_NAME
        )
    )
    self.mocked_client.manifests.Get.Expect(
        request=messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        response=self.createManifest()
    )
    self.Run('deployment-manager manifests describe --deployment '
             + DEPLOYMENT_NAME)
    self.AssertOutputContains(MANIFEST_NAME)
    self.AssertOutputContains(str(MANIFEST_ID))
    self.AssertOutputContains(CONFIG)

  def testManifestsDescribe_DeploymentMissing(self):
    not_found_message = 'Requested deployment %s not found' % DEPLOYMENT_NAME
    self.mocked_client.deployments.Get.Expect(
        request=messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        exception=http_error.MakeHttpError(
            404,
            not_found_message,
            url='FakeUrl')
    )
    with self.AssertRaisesHttpExceptionMatches(not_found_message):
      self.Run('deployment-manager manifests describe --deployment %s'
               % DEPLOYMENT_NAME)

  def testManifestsDescribe_NoManifestUnderDeployment(self):
    error_message = ('The deployment [%s] does not have a current manifest. '
                     'Please specify the manifest name.') % DEPLOYMENT_NAME
    self.mocked_client.deployments.Get.Expect(
        request=messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=messages.Deployment(
            name=DEPLOYMENT_NAME,
            id=123,
        )
    )
    with self.assertRaises(dm_exceptions.ManifestError):
      self.Run('deployment-manager manifests describe --deployment %s'
               % DEPLOYMENT_NAME)
    self.AssertErrContains(error_message)

  def testManifestsDescribe_ManifestMissing(self):
    not_found_message = 'Requested manifest %s not found' % MANIFEST_NAME
    self.mocked_client.deployments.Get.Expect(
        request=messages.DeploymentmanagerDeploymentsGetRequest(
            deployment=DEPLOYMENT_NAME,
            project=self.Project()
        ),
        response=messages.Deployment(
            name=DEPLOYMENT_NAME,
            id=123,
            manifest=MANIFEST_NAME
        )
    )
    self.mocked_client.manifests.Get.Expect(
        request=messages.DeploymentmanagerManifestsGetRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
            manifest=MANIFEST_NAME,
        ),
        exception=http_error.MakeHttpError(
            404,
            not_found_message,
            url='FakeUrl')
    )
    with self.AssertRaisesHttpExceptionMatches(not_found_message):
      self.Run('deployment-manager manifests describe --deployment %s'
               % DEPLOYMENT_NAME)

if __name__ == '__main__':
  test_case.main()
