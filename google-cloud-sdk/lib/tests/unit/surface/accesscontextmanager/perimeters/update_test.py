# -*- coding: utf-8 -*- #
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
"""Tests for `gcloud access-context-manager perimeters update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class PerimetersUpdateTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, policy, perimeter):
    m = self.messages
    get_req_type = m.AccesscontextmanagerAccessPoliciesAccessZonesGetRequest
    self.client.accessPolicies_accessZones.Get.Expect(
        get_req_type(name=perimeter.name), perimeter)

  def _ExpectPatch(self,
                   perimeter_update,
                   perimeter_after,
                   update_mask,
                   policy,
                   perimeter_before=None):
    perimeter_name = perimeter_after.name
    m = self.messages
    if perimeter_before is not None:
      self._ExpectGet(policy, perimeter_before)
    req_type = m.AccesscontextmanagerAccessPoliciesAccessZonesPatchRequest
    self.client.accessPolicies_accessZones.Patch.Expect(
        req_type(
            name=perimeter_name,
            accessZone=perimeter_update,
            updateMask=update_mask),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    self._ExpectGet(policy, perimeter_after)

  def testUpdate_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters update --policy MY_POLICY')

  def testUpdate_NoUpdates(self, track):
    self.SetUpForTrack(track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description=None,
        restricted_services=[],
        unrestricted_services=[],
        access_levels=[],
        type_='ZONE_TYPE_REGULAR')
    self._ExpectPatch(self.messages.AccessZone(), perimeter, '', 'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '    --policy MY_POLICY'
    )

    self.assertEqual(result, perimeter)

  def testUpdate_NonRepeatingFields(self, track):
    self.SetUpForTrack(track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        unrestricted_services=[],
        access_levels=[],
        type_='ZONE_TYPE_BRIDGE')
    perimeter_types = self.messages.AccessZone.ZoneTypeValueValuesEnum
    perimeter_update = self.messages.AccessZone(
        title='My Perimeter Title',
        description='foo bar',
        zoneType=perimeter_types.ZONE_TYPE_BRIDGE,
    )
    self._ExpectPatch(perimeter_update, perimeter, 'description,title,zoneType',
                      'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '    --policy MY_POLICY --type bridge --title "My Perimeter Title" '
        '    --description "foo bar"')

    self.assertEqual(result, perimeter)

  def testUpdate_ClearRepeatingFields(self, track):
    self.SetUpForTrack(track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        unrestricted_services=[],
        access_levels=[],
        type_='ZONE_TYPE_BRIDGE')
    perimeter_update = self.messages.AccessZone(
        restrictedServices=[],
        unrestrictedServices=[],
        accessLevels=[],
        resources=[])
    self._ExpectPatch(
        perimeter_update, perimeter,
        'accessLevels,resources,restrictedServices,unrestrictedServices',
        'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy MY_POLICY --clear-resources --clear-restricted-services '
        '   --clear-unrestricted-services --clear-access-levels')

    self.assertEqual(result, perimeter)

  def testUpdate_SetRepeatingFields(self, track):
    self.SetUpForTrack(track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        unrestricted_services=['*'],
        access_levels=['a', 'b'],
        type_='ZONE_TYPE_BRIDGE')
    perimeter_update = self.messages.AccessZone(
        restrictedServices=perimeter.restrictedServices,
        unrestrictedServices=perimeter.unrestrictedServices,
        accessLevels=[  # _MakePerimeter has sugar for resource names
            'accessPolicies/MY_POLICY/accessLevels/a',
            'accessPolicies/MY_POLICY/accessLevels/b'
        ],
        resources=perimeter.resources)
    self._ExpectPatch(
        perimeter_update, perimeter,
        'accessLevels,resources,restrictedServices,unrestrictedServices',
        'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy MY_POLICY '
        '   --set-resources projects/12345,projects/67890 '
        '   --set-restricted-services foo.googleapis.com,bar.googleapis.com '
        '   --set-unrestricted-services * '
        '   --set-access-levels a,b')

    self.assertEqual(result, perimeter)

  def testUpdate_AddRemoveRepeatingFields(self, track):
    self.SetUpForTrack(track)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        unrestricted_services=['baz.googleapis.com'],
        access_levels=['a', 'b'],
        resources=['projects/12345', 'projects/67890'],
        type_='ZONE_TYPE_BRIDGE')
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['bar.googleapis.com'],
        unrestricted_services=['baz.googleapis.com'],
        access_levels=['a', 'b', 'c', 'd'],
        type_='ZONE_TYPE_BRIDGE')
    perimeter_update = self.messages.AccessZone(
        restrictedServices=perimeter_after.restrictedServices,
        accessLevels=perimeter_after.accessLevels)
    self._ExpectGet('MY_POLICY', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'accessLevels,restrictedServices', 'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy MY_POLICY '
        '   --add-resources projects/12345,projects/67890 '
        '   --remove-restricted-services foo.googleapis.com '
        '   --remove-unrestricted-services qux.googleapis.com '
        '   --add-access-levels c,d')

    self.assertEqual(result, perimeter_after)

  def testUpdate_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        policy=policy,
        restricted_services=[],
        unrestricted_services=[],
        access_levels=[],
        type_='ZONE_TYPE_BRIDGE')
    perimeter.name = 'accessPolicies/my_acm_policy/accessZones/MY_PERIMETER'
    perimeter_types = self.messages.AccessZone.ZoneTypeValueValuesEnum
    perimeter_update = self.messages.AccessZone(
        title='My Perimeter Title',
        description='foo bar',
        zoneType=perimeter_types.ZONE_TYPE_BRIDGE,
    )
    self._ExpectPatch(perimeter_update, perimeter, 'description,title,zoneType',
                      policy)

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --type bridge --title "My Perimeter Title" --description "foo bar"')

    self.assertEqual(result, perimeter)


if __name__ == '__main__':
  test_case.main()
