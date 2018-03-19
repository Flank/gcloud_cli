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
"""Tests for `gcloud access-context-manager policies describe`."""
from googlecloudsdk.calliope import base as base
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.core.cache import fake
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class PoliciesDescribeTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePolicy(self, policy_id, parent=None):
    return self.messages.AccessPolicy(
        name='accessPolicies/{}'.format(policy_id),
        parent=parent,
        title='My Policy')

  def _ExpectGet(self, policy):
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesGetRequest
    self.client.accessPolicies.Get.Expect(
        request_type(
            name=policy.name,
        ),
        policy)

  def testDescribe(self, track):
    self.SetUpForTrack(track)

    organization_id = '12345'
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectGet(policy)

    result = self.Run('access-context-manager policies describe MY_POLICY')

    self.assertEqual(result, policy)

  def testDescribe_Format(self, track):
    self.SetUpForTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)

    organization_id = '12345'
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectGet(policy)

    self.Run('access-context-manager policies describe MY_POLICY')

    self.AssertOutputEquals("""\
        name: accessPolicies/MY_POLICY
        parent: organizations/12345
        title: My Policy
        """, normalize_space=True)

  def testDescribe_AutoResolution(self, track):
    self.SetUpForTrack(track)

    cache = fake.Cache('fake://dummy', create=True)
    self.StartObjectPatch(cache_util.GetCache, '_OpenCache', return_value=cache)

    organization_name = 'organizations/12345'
    organization = self.resource_manager_messages.Organization(
        name=organization_name,
        displayName='example.com'
    )
    policy = self._MakePolicy('MY_POLICY',
                              parent=organization_name)
    self._ExpectSearchOrganizations('domain:example.com', [organization])
    self._ExpectListPolicies(organization_name, [policy])
    self._ExpectGet(policy)

    result = self.Run('access-context-manager policies describe')

    self.assertEqual(result, policy)

    # Autoresolution should be cached! Only need to get the policy again.
    self._ExpectGet(policy)

    result = self.Run('access-context-manager policies describe')

    self.assertEqual(result, policy)


if __name__ == '__main__':
  test_case.main()
