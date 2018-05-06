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

"""Unit tests for manifests list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin

messages = apis.GetMessagesModule('deploymentmanager', 'v2')

DEPLOYMENT_NAME = 'deployment-name'
MANIFEST_NAME = 'manifest-name'
MANIFEST_ID = 12345


class ManifestsListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for deployments list command."""

  # TODO(b/36057056): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createManifest(self, identifier=None):
    """Helper function to create a simple manifest.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Manifest with name, id, and config set.
    """
    if identifier is not None:
      name = MANIFEST_NAME + str(identifier)
      manifest_id = identifier
    else:
      name = MANIFEST_NAME
      manifest_id = MANIFEST_ID
    return messages.Manifest(
        name=name,
        id=manifest_id,
    )

  def testManifestsList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    num_manifests = 10
    manifests = [self.createManifest(i) for i in range(num_manifests)]
    self.mocked_client.manifests.List.Expect(
        request=messages.DeploymentmanagerManifestsListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=messages.ManifestsListResponse(
            manifests=manifests,
        ),
    )
    result = self.Run('deployment-manager manifests list --deployment '
                      + DEPLOYMENT_NAME)
    result = list(result)  # consume generator
    self.assertEqual(manifests, result)

  def testManifestsList_EmptyList(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.mocked_client.manifests.List.Expect(
        request=messages.DeploymentmanagerManifestsListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME
        ),
        response=messages.ManifestsListResponse()
    )
    self.Run('deployment-manager manifests list --deployment '
             + DEPLOYMENT_NAME)
    self.AssertErrContains('0 items')

  def testManifestsList_Limit(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    num_manifests = 10
    limit = 5
    manifests = [self.createManifest(i) for i in range(num_manifests)]
    self.mocked_client.manifests.List.Expect(
        request=messages.DeploymentmanagerManifestsListRequest(
            project=self.Project(),
            deployment=DEPLOYMENT_NAME,
        ),
        response=messages.ManifestsListResponse(
            manifests=manifests,
        ),
    )
    result = self.Run('deployment-manager manifests list --deployment '
                      + DEPLOYMENT_NAME + ' --limit ' + str(limit))
    result = list(result)  # consume generator
    self.assertEqual(manifests[:limit], result)

if __name__ == '__main__':
  test_case.main()
