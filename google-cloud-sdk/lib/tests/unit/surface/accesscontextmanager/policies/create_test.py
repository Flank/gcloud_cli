# Copyright 2018 Google Inc. All Rights Reserved.  #
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
"""Tests for `gcloud access-context-manager policies create`."""
from googlecloudsdk.calliope import base as base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class PoliciesCreateTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePolicy(self, policy_id=None, parent=None):
    return self.messages.AccessPolicy(
        name='accessPolicies/{}'.format(policy_id) if policy_id else None,
        parent=parent,
        title='My Policy')

  def _ExpectCreate(self, policy_req, policy):
    self.client.accessPolicies.Create.Expect(
        policy_req,
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op',
                             resource_name='accessPolicies/67890')

  def testCreate(self, track):
    self.SetUpForTrack(track)

    organization_id = '12345'
    policy_req = self._MakePolicy(None,
                                  parent='organizations/' + organization_id)
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectCreate(policy_req, policy)

    result = self.Run('access-context-manager policies create '
                      '    --title "My Policy" '
                      '    --organization 12345')
    self.assertEqual(result.additionalProperties[0].value.string_value,
                     'accessPolicies/67890')


if __name__ == '__main__':
  test_case.main()
