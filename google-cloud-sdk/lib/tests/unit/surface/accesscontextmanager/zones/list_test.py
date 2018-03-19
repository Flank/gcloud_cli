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
"""Tests for `gcloud access-context-manager zones list`."""
from googlecloudsdk.calliope import base as base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class ZonesListTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeZoneNum(self, idx):
    return self._MakeZone('MY_ZONE{}'.format(idx))

  def _MakeZones(self, num=3):
    return map(self._MakeZoneNum, range(num))

  def _ExpectList(self, zones, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessZonesListRequest
    self.client.accessPolicies_accessZones.List.Expect(
        request_type(
            parent=policy_name,
        ),
        self.messages.ListAccessZonesResponse(accessZones=zones))

  def testList(self, track):
    self.SetUpForTrack(track)
    zones = self._MakeZones()
    self._ExpectList(zones, 'my-policy')

    results = self.Run('access-context-manager zones list --policy my-policy')

    self.assertEqual(results, zones)

  def testList_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    zones = self._MakeZones()
    policy = 'my-acm-policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectList(zones, policy)

    results = self.Run('access-context-manager zones list')

    self.assertEqual(results, zones)

  def testList_Format(self, track):
    self.SetUpForTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    zones = self._MakeZones()
    self._ExpectList(zones, 'my-policy')

    self.Run('access-context-manager zones list --policy my-policy')

    self.AssertOutputEquals("""\
        NAME      TITLE
        MY_ZONE0  My Zone
        MY_ZONE1  My Zone
        MY_ZONE2  My Zone
        """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
