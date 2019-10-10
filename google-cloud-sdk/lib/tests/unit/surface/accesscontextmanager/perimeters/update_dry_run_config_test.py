# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from six import text_type


class PerimetersUpdateDryRunConfigTest(accesscontextmanager.Base):

  def PreSetUp(self):
    # BETA and GA tracks are currently not supported.
    self.track = calliope_base.ReleaseTrack.ALPHA

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
      self.Run(
          'access-context-manager perimeters update-dry-run-config --policy 123'
      )

  def testUpdate_NoUpdates(self):
    self.SetUpForTrack(self.track)
    # No patch message sent, because nothing is changed.

    self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '    --policy 123')
    self.AssertErrContains(
        'The update specified results in an identical resource.')

  def testUpdate_SpecifyingTitleForbidden(self):
    self.SetUpForTrack(self.track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'unrecognized arguments'):

      self.Run(
          'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
          '    --policy 123 --title "My Perimeter Title"')

  def testUpdate_ClearRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        access_levels=[],
        resources=[],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            restrictedServices=[], accessLevels=[], resources=[]))
    self._ExpectPatch(
        perimeter_update, perimeter, 'dryRun,spec.accessLevels,spec.resources,'
        'spec.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 --clear-resources --clear-restricted-services '
        '   --clear-access-levels')

    self.assertEqual(result, perimeter)

  def testUpdate_SetRepeatingFields(self):
    self.SetUpForTrack(self.track)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        resources=[],
        restricted_services=[],
        access_levels=[],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        resources=['projects/12345', 'projects/67890'],
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        access_levels=['a', 'b'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            restrictedServices=perimeter.spec.restrictedServices,
            accessLevels=[  # _MakePerimeter has sugar for resource names
                'accessPolicies/123/accessLevels/a',
                'accessPolicies/123/accessLevels/b'
            ],
            resources=perimeter.spec.resources))
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(
        perimeter_update, perimeter, 'dryRun,spec.accessLevels,spec.resources,'
        'spec.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 '
        '   --add-resources projects/12345,projects/67890 '
        '   --add-restricted-services foo.googleapis.com,bar.googleapis.com '
        '   --add-access-levels a,b')

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
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['bar.googleapis.com'],
        access_levels=['a', 'b', 'c', 'd'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            restrictedServices=perimeter_after.spec.restrictedServices,
            accessLevels=perimeter_after.spec.accessLevels))
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'dryRun,spec.accessLevels,spec.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 '
        '   --add-resources projects/12345,projects/67890 '
        '   --remove-restricted-services foo.googleapis.com '
        '   --add-access-levels c,d')

    self.assertEqual(result, perimeter_after)

  def testUpdate_PolicyFromProperty(self):
    self.SetUpForTrack(self.track)
    policy = '123'
    properties.VALUES.access_context_manager.policy.Set(policy)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        access_levels=['a', 'b'],
        resources=['projects/12345', 'projects/67890'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True,
        policy=policy)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['bar.googleapis.com'],
        access_levels=['a', 'b', 'c', 'd'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            restrictedServices=perimeter_after.spec.restrictedServices,
            accessLevels=perimeter_after.spec.accessLevels))
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'dryRun,spec.accessLevels,spec.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --add-resources projects/12345,projects/67890 '
        '   --remove-restricted-services foo.googleapis.com '
        '   --add-access-levels c,d')

    self.assertEqual(result, perimeter_after)

  def testUpdate_InvalidPolicyArg(self):
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run(
          'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
          '    --policy accessPolicies/123'
          '    --add-resources projects/12345 ')
    self.assertIn('set to the policy number', text_type(ex.exception))

  def testUpdate_AddServiceFilterFields(self):
    self.SetUpForTrack(self.track)

    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        vpc_allowed_services=['bar-vpc.googleapis.com'],
        dry_run=True,
    )
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            vpcServiceRestriction=perimeter_after.spec.vpcServiceRestriction))
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(
        perimeter_update, perimeter_after, 'dryRun,'
        'spec.vpcServiceRestriction.allowedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 '
        '   --add-vpc-allowed-services bar-vpc.googleapis.com ')

    self.assertEqual(result, perimeter_after)

  def testUpdate_EnableServiceFilters(self):
    self.SetUpForTrack(self.track)

    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        dry_run=True)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        enable_vpc_service_restriction=True,
        dry_run=True,
    )
    perimeter_update = self.messages.ServicePerimeter(
        dryRun=True,
        spec=self.messages.ServicePerimeterConfig(
            vpcServiceRestriction=perimeter_after.spec.vpcServiceRestriction))

    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(
        perimeter_update, perimeter_after, 'dryRun,'
        'spec.vpcServiceRestriction.enableRestriction', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 '
        '   --enable-vpc-service-restriction ')

    self.assertEqual(result, perimeter_after)

  def testUpdate_ClearDryRun(self):
    self.SetUpForTrack(self.track)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_update = self.messages.ServicePerimeter(dryRun=False, spec=None)

    self._ExpectPatch(perimeter_update, perimeter_after, 'dryRun,spec', '123')

    result = self.Run(
        'access-context-manager perimeters update-dry-run-config MY_PERIMETER '
        '   --policy 123 '
        '   --clear')

    self.assertEqual(result, perimeter_after)


if __name__ == '__main__':
  test_case.main()
