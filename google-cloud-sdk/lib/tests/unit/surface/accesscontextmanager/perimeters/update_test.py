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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class PerimetersUpdateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, policy, perimeter):
    m = self.messages
    get_req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
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
    req_type = m.AccesscontextmanagerAccessPoliciesServicePerimetersPatchRequest
    self.client.accessPolicies_servicePerimeters.Patch.Expect(
        req_type(
            name=perimeter_name,
            servicePerimeter=perimeter_update,
            updateMask=update_mask),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    self._ExpectGet(policy, perimeter_after)

  def testUpdate_MissingRequired(self):
    self.SetUpForTrack(self.track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters update --policy MY_POLICY')

  def testUpdate_NoUpdates(self):
    self.SetUpForTrack(self.track)
    perimeter_kwargs = {
        'title': 'My Perimeter Title',
        'description': None,
        'restricted_services': [],
        'access_levels': [],
        'type_': 'PERIMETER_TYPE_REGULAR'
    }
    perimeter = self._MakePerimeter('MY_PERIMETER', **perimeter_kwargs)
    self._ExpectPatch(self.messages.ServicePerimeter(), perimeter, '',
                      'MY_POLICY')

    result = self.Run('access-context-manager perimeters update MY_PERIMETER '
                      '    --policy MY_POLICY')

    self.assertEqual(result, perimeter)

  def testUpdate_NonRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        access_levels=[],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_types = (
        self.messages.ServicePerimeter.PerimeterTypeValueValuesEnum)
    perimeter_update = self.messages.ServicePerimeter(
        title='My Perimeter Title',
        description='foo bar',
        perimeterType=perimeter_types.PERIMETER_TYPE_BRIDGE,
    )
    self._ExpectPatch(perimeter_update, perimeter,
                      'description,perimeterType,title', 'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '    --policy MY_POLICY --type bridge --title "My Perimeter Title" '
        '    --description "foo bar"')

    self.assertEqual(result, perimeter)

  def testUpdate_ClearRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        access_levels=[],
        resources=[],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_update = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            restrictedServices=[],
            accessLevels=[],
            resources=[]))
    self._ExpectPatch(
        perimeter_update, perimeter, 'status.accessLevels,status.resources,'
        'status.restrictedServices', 'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy MY_POLICY --clear-resources --clear-restricted-services '
        '   --clear-access-levels')

    self.assertEqual(result, perimeter)

  def testUpdate_SetRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        access_levels=['a', 'b'],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_update = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            restrictedServices=perimeter.status.restrictedServices,
            accessLevels=[  # _MakePerimeter has sugar for resource names
                'accessPolicies/MY_POLICY/accessLevels/a',
                'accessPolicies/MY_POLICY/accessLevels/b'
            ],
            resources=perimeter.status.resources))
    self._ExpectPatch(
        perimeter_update, perimeter, 'status.accessLevels,status.resources,'
        'status.restrictedServices', 'MY_POLICY')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy MY_POLICY '
        '   --set-resources projects/12345,projects/67890 '
        '   --set-restricted-services foo.googleapis.com,bar.googleapis.com '
        '   --set-access-levels a,b')

    self.assertEqual(result, perimeter)

  def testUpdate_AddRemoveRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        access_levels=['a', 'b'],
        resources=['projects/12345', 'projects/67890'],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['bar.googleapis.com'],
        access_levels=['a', 'b', 'c', 'd'],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_update = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            restrictedServices=perimeter_after.status.restrictedServices,
            accessLevels=perimeter_after.status.accessLevels))
    self._ExpectGet('MY_POLICY', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'status.accessLevels,status.restrictedServices',
                      'MY_POLICY')

    result = self.Run('access-context-manager perimeters update MY_PERIMETER '
                      '   --policy MY_POLICY '
                      '   --add-resources projects/12345,projects/67890 '
                      '   --remove-restricted-services foo.googleapis.com '
                      '   --add-access-levels c,d')

    self.assertEqual(result, perimeter_after)

  def testUpdate_PolicyFromProperty(self):
    self.SetUpForTrack(self.track)
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        policy=policy,
        restricted_services=[],
        access_levels=[],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter.name = (
        'accessPolicies/my_acm_policy/servicePerimeters/MY_PERIMETER')
    perimeter_types = (
        self.messages.ServicePerimeter.PerimeterTypeValueValuesEnum)
    perimeter_update = self.messages.ServicePerimeter(
        title='My Perimeter Title',
        description='foo bar',
        perimeterType=perimeter_types.PERIMETER_TYPE_BRIDGE,
    )
    self._ExpectPatch(perimeter_update, perimeter,
                      'description,perimeterType,title', policy)

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --type bridge --title "My Perimeter Title" --description "foo bar"')

    self.assertEqual(result, perimeter)


class PerimetersUpdateTestBeta(PerimetersUpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class PerimetersUpdateTestAlpha(PerimetersUpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
