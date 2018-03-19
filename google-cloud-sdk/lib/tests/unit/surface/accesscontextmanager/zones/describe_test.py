# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager zones describe`."""
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class ZonesDescribeTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, zone, policy):
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessZonesGetRequest
    self.client.accessPolicies_accessZones.Get.Expect(
        request_type(name=zone.name), zone)

  def testDescribe_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager zones describe --policy MY_POLICY')

  def testDescribe(self, track):
    self.SetUpForTrack(track)
    zone = self._MakeZone('my_zone')
    self._ExpectGet(zone, 'my_policy')

    result = self.Run(
        'access-context-manager zones describe my_zone --policy MY_POLICY')

    self.assertEqual(result, zone)

  def testDescribe_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    zone = self._MakeZone('my_zone')
    policy = 'my_acm_policy'
    zone.name = 'accessPolicies/my_acm_policy/accessZones/my_zone'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectGet(zone, policy)

    result = self.Run(
        'access-context-manager zones describe my_zone')

    self.assertEqual(result, zone)

if __name__ == '__main__':
  test_case.main()
