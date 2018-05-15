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
"""Tests for `gcloud access-context-manager perimeters list`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six.moves import map
from six.moves import range


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class PerimetersListTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePerimeterNum(self, idx):
    return self._MakePerimeter('MY_PERIMETER{}'.format(idx))

  def _MakePerimeters(self, num=3):
    return list(map(self._MakePerimeterNum, list(range(num))))

  def _ExpectList(self, perimeters, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessZonesListRequest
    self.client.accessPolicies_accessZones.List.Expect(
        request_type(parent=policy_name,),
        self.messages.ListAccessZonesResponse(accessZones=perimeters))

  def testList(self, track):
    self.SetUpForTrack(track)
    perimeters = self._MakePerimeters()
    self._ExpectList(perimeters, 'my-policy')

    results = self.Run(
        'access-context-manager perimeters list --policy my-policy')

    self.assertEqual(results, perimeters)

  def testList_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    perimeters = self._MakePerimeters()
    policy = 'my-acm-policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectList(perimeters, policy)

    results = self.Run('access-context-manager perimeters list')

    self.assertEqual(results, perimeters)

  def testList_Format(self, track):
    self.SetUpForTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    perimeters = self._MakePerimeters()
    self._ExpectList(perimeters, 'my-policy')

    self.Run('access-context-manager perimeters list --policy my-policy')

    self.AssertOutputEquals(
        """\
        NAME      TITLE
        MY_PERIMETER0  My Perimeter
        MY_PERIMETER1  My Perimeter
        MY_PERIMETER2  My Perimeter
        """,
        normalize_space=True)

if __name__ == '__main__':
  test_case.main()
