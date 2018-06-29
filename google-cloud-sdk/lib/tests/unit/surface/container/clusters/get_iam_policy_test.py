# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for 'clusters get-iam-policy' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import base64

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetIamPolicyTestAlphaV1Alpha1API(parameterized.TestCase,
                                       base.AlphaTestBase,
                                       base.TestBaseV1Alpha1,
                                       base.ClustersTestBase):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False

  @parameterized.named_parameters(
      ('Zonal', '--zone', 'us-central1-f'),
      ('Regional', '--region', 'us-central1'))
  def testGetIamPolicy(self, location_flag, location):
    policy = self.messages.GoogleIamV1Policy(
        # u'?
        bindings=[
            self.messages.GoogleIamV1Binding(
                members=['user:harry', 'user:hermione'], role='dumbledoresarmy')
        ],
        etag=base64.b64decode('1234'))
    self.mocked_client.projects.GetIamPolicy.Expect(
        self.messages.ContainerProjectsGetIamPolicyRequest(
            resource=api_adapter.ProjectLocationCluster(
                self.PROJECT_ID, location, self.CLUSTER_NAME)),
        policy)
    self.Run('container clusters get-iam-policy {} {} {}'.format(
        self.CLUSTER_NAME, location_flag, location))


if __name__ == '__main__':
  test_case.main()
