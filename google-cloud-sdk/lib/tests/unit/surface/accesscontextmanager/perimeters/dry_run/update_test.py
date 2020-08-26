# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager perimeters dry-run update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class DryRunUpdateTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def _GetPerimeterType(self, kind):
    return perimeters.GetPerimeterTypeEnumForShortName(kind, self.api_version)

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, perimeter):
    m = self.messages
    get_req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
        get_req_type(name=perimeter.name), perimeter)

  def _ExpectPatch(self, perimeter_name, perimeter_before, perimeter_update,
                   perimeter_after, update_mask):
    m = self.messages
    self._ExpectGet(perimeter_before)
    req_type = m.AccesscontextmanagerAccessPoliciesServicePerimetersPatchRequest
    self.client.accessPolicies_servicePerimeters.Patch.Expect(
        req_type(
            name=perimeter_name,
            servicePerimeter=perimeter_update,
            updateMask=update_mask),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    self._ExpectGet(perimeter_after)

  def testUpdateWithExistingSpec(self):
    self.SetUpForAPI(self.api_version)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        restricted_services=['bigquery.googleapis.com'],
        resources=['projects/123', 'projects/456'],
        enable_vpc_accessible_services=True,
        vpc_allowed_services=['storage.googleapis.com'],
        dry_run=True)
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        restricted_services=[
            'bigquery.googleapis.com', 'storage.googleapis.com'
        ],
        resources=['projects/456'],
        access_levels=['MY_LEVEL', 'MY_LEVEL_2', 'hello_level'],
        enable_vpc_accessible_services=False,
        vpc_allowed_services=None,
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        spec=perimeter_after.spec, useExplicitDryRunSpec=True)
    self._ExpectPatch(
        'accessPolicies/123/servicePerimeters/MY_PERIMETER', perimeter_before,
        perimeter_update, perimeter_after, 'spec.accessLevels,spec.resources,'
        'spec.restrictedServices,spec.vpcAccessibleServices.allowedServices,'
        'spec.vpcAccessibleServices.enableRestriction,useExplicitDryRunSpec')

    result = self.Run(
        'access-context-manager perimeters dry-run update MY_PERIMETER '
        '   --policy 123 '
        '   --remove-resources="projects/123" '
        '   --add-restricted-services=storage.googleapis.com '
        '   --add-access-levels="accessPolicies/123/accessLevels/hello_level"'
        '   --clear-vpc-allowed-services '
        '   --no-enable-vpc-accessible-services')

    self.assertEqual(result, perimeter_after)

  def testUpdateWithNoPreviousSpec(self):
    self.SetUpForAPI(self.api_version)
    # Note that, unlike in the test case above, dry_run is not True here.
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        restricted_services=['bigquery.googleapis.com'],
        resources=['projects/123', 'projects/456'],
        enable_vpc_accessible_services=True,
        vpc_allowed_services=['storage.googleapis.com'])
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        restricted_services=[
            'bigquery.googleapis.com', 'storage.googleapis.com'
        ],
        resources=['projects/456'],
        access_levels=['MY_LEVEL', 'MY_LEVEL_2', 'hello_level'],
        enable_vpc_accessible_services=False,
        vpc_allowed_services=None,
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        spec=perimeter_after.spec, useExplicitDryRunSpec=True)
    self._ExpectPatch(
        'accessPolicies/123/servicePerimeters/MY_PERIMETER', perimeter_before,
        perimeter_update, perimeter_after, 'spec.accessLevels,spec.resources,'
        'spec.restrictedServices,spec.vpcAccessibleServices.allowedServices,'
        'spec.vpcAccessibleServices.enableRestriction,useExplicitDryRunSpec')

    result = self.Run(
        'access-context-manager perimeters dry-run update MY_PERIMETER '
        '   --policy 123 '
        '   --remove-resources="projects/123" '
        '   --add-restricted-services=storage.googleapis.com '
        '   --add-access-levels="accessPolicies/123/accessLevels/hello_level"'
        '   --clear-vpc-allowed-services '
        '   --no-enable-vpc-accessible-services')

    self.assertEqual(result, perimeter_after)


class DryRunUpdateTestAlpha(DryRunUpdateTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdate_SetDirectionalPolicies(self):
    self.SetUpForAPI(self.api_version)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        access_levels=None,
        resources=None,
        restricted_services=None)

    ingress_policies = self._MakeIngressPolicies()
    egress_policies = self._MakeEgressPolicies()
    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        type_=self._GetPerimeterType('regular'),
        ingress_policies=ingress_policies,
        egress_policies=egress_policies,
        dry_run=True,
        access_levels=None,
        resources=None,
        restricted_services=None)

    perimeter_in_update_request = self.messages.ServicePerimeter(
        spec=self.messages.ServicePerimeterConfig(
            ingressPolicies=ingress_policies, egressPolicies=egress_policies),
        useExplicitDryRunSpec=True)

    self._ExpectPatch(
        'accessPolicies/123/servicePerimeters/MY_PERIMETER',
        perimeter_before,
        perimeter_in_update_request,
        expected_perimeter,
        # Currently, dry run will update repeated fields no matter what.
        'spec.accessLevels,spec.egressPolicies,spec.ingressPolicies,spec.resources,spec.restrictedServices,useExplicitDryRunSpec'
    )

    ingress_policies_spec_path = self.Touch(
        self.temp_path, 'ingress.yaml', contents=self.INGRESS_POLICIES_SPECS)

    egress_policies_spec_path = self.Touch(
        self.temp_path, 'egress.yaml', contents=self.EGRESS_POLICIES_SPECS)

    result = self.Run(
        'access-context-manager perimeters dry-run update MY_PERIMETER '
        '   --policy 123 '
        '   --set-ingress-policies {} --set-egress-policies {}'.format(
            ingress_policies_spec_path, egress_policies_spec_path))
    self.assertEqual(result, expected_perimeter)

  def testUpdate_clearDirectionalPolicies(self):
    self.SetUpForAPI(self.api_version)

    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        access_levels=None,
        resources=None,
        restricted_services=None,
        ingress_policies=self._MakeIngressPolicies(),
        egress_policies=self._MakeEgressPolicies())

    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        type_='PERIMETER_TYPE_REGULAR',
        ingress_policies=[],
        egress_policies=[],
        dry_run=True,
        access_levels=None,
        resources=None,
        restricted_services=None)

    perimeter_in_update_request = self.messages.ServicePerimeter(
        spec=self.messages.ServicePerimeterConfig(
            ingressPolicies=[], egressPolicies=[]),
        useExplicitDryRunSpec=True)
    self._ExpectPatch(
        'accessPolicies/123/servicePerimeters/MY_PERIMETER',
        perimeter_before,
        perimeter_in_update_request,
        expected_perimeter,
        # Currently, dry run will update repeated fields no matter what.
        'spec.accessLevels,spec.egressPolicies,spec.ingressPolicies,spec.resources,spec.restrictedServices,useExplicitDryRunSpec'
    )

    result = self.Run(
        'access-context-manager perimeters dry-run update MY_PERIMETER '
        '   --policy 123 --clear-ingress-policies --clear-egress-policies')

    self.assertEqual(result, expected_perimeter)


if __name__ == '__main__':
  test_case.main()
