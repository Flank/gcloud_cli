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
"""Tests for `gcloud access-context-manager perimeters dry-run create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class DryRunCreateTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def _GetPerimeterType(self, kind):
    return perimeters.GetPerimeterTypeEnumForShortName(kind, self.api_version)

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, perimeter, not_present=False):
    m = self.messages
    get_req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    if not_present:
      self.client.accessPolicies_servicePerimeters.Get.Expect(
          get_req_type(name=perimeter.name),
          exception=apitools_exceptions.HttpNotFoundError(None, None, None))
    else:
      self.client.accessPolicies_servicePerimeters.Get.Expect(
          get_req_type(name=perimeter.name), perimeter)

  def _ExpectPatch(self,
                   perimeter_update,
                   perimeter_after,
                   update_mask,
                   perimeter_before=None):
    perimeter_name = perimeter_after.name
    m = self.messages
    if perimeter_before is not None:
      self._ExpectGet(perimeter_before)
    else:
      self._ExpectGet(
          self.messages.ServicePerimeter(name=perimeter_after.name),
          not_present=True)
    req_type = m.AccesscontextmanagerAccessPoliciesServicePerimetersPatchRequest
    self.client.accessPolicies_servicePerimeters.Patch.Expect(
        req_type(
            name=perimeter_name,
            servicePerimeter=perimeter_update,
            updateMask=update_mask),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    self._ExpectGet(perimeter_after)

  def testCreate_PerimeterNameMissing(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters dry-run create --policy 123')

  def testCreate_newPerimeter(self):
    self.SetUpForAPI(self.api_version)
    perimeter_before = None
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        description='foo',
        restricted_services=['bigquery.googleapis.com'],
        resources=['projects/123', 'projects/456'],
        access_levels=['hello_level'],
        enable_vpc_accessible_services=True,
        vpc_allowed_services=['storage.googleapis.com'],
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        name='accessPolicies/123/servicePerimeters/MY_PERIMETER',
        title='My Perimeter Title',
        perimeterType=self._GetPerimeterType('regular'),
        description='foo',
        spec=perimeter_after.spec,
        useExplicitDryRunSpec=True)
    self._ExpectPatch(
        perimeter_update, perimeter_after,
        'description,name,perimeterType,spec.accessLevels,spec.resources,'
        'spec.restrictedServices,spec.vpcAccessibleServices.allowedServices,'
        'spec.vpcAccessibleServices.enableRestriction,title,'
        'useExplicitDryRunSpec', perimeter_before)

    result = self.Run(
        'access-context-manager perimeters dry-run create MY_PERIMETER '
        '   --policy 123 --perimeter-title="My Perimeter Title" '
        '   --perimeter-description="foo" --perimeter-type="regular" '
        '   --perimeter-resources="projects/123,projects/456" '
        '   --perimeter-restricted-services=bigquery.googleapis.com '
        '   --perimeter-access-levels="hello_level"'
        '   --perimeter-vpc-allowed-services=storage.googleapis.com '
        '   --perimeter-enable-vpc-accessible-services')

    self.assertEqual(result, perimeter_after)

  def testCreate_existingPerimeter(self):
    self.SetUpForAPI(self.api_version)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        description='foo')
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        description='foo',
        restricted_services=['bigquery.googleapis.com'],
        resources=['projects/123', 'projects/456'],
        access_levels=['hello_level'],
        enable_vpc_accessible_services=True,
        vpc_allowed_services=['storage.googleapis.com'],
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        spec=perimeter_after.spec, useExplicitDryRunSpec=True)
    self._ExpectPatch(
        perimeter_update, perimeter_after,
        'spec.accessLevels,spec.resources,spec.restrictedServices,'
        'spec.vpcAccessibleServices.allowedServices,'
        'spec.vpcAccessibleServices.enableRestriction,useExplicitDryRunSpec',
        perimeter_before)

    result = self.Run(
        'access-context-manager perimeters dry-run create MY_PERIMETER '
        '   --policy 123 --resources="projects/123,projects/456" '
        '   --restricted-services=bigquery.googleapis.com '
        '   --access-levels="hello_level"'
        '   --vpc-allowed-services=storage.googleapis.com '
        '   --enable-vpc-accessible-services')

    self.assertEqual(result, perimeter_after)

  def testCreate_RepeatingFieldsEmpty(self):
    self.SetUpForAPI(self.api_version)
    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['bigquery.googleapis.com'],
        resources=['projects/123', 'projects/456'],
        type_='PERIMETER_TYPE_REGULAR',
        dry_run=True)
    perimeter_update = self.messages.ServicePerimeter(
        useExplicitDryRunSpec=True,
        spec=self.messages.ServicePerimeterConfig(
            restrictedServices=[], accessLevels=[], resources=[]))
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=[],
        resources=[],
        access_levels=[],
        type_='PERIMETER_TYPE_REGULAR',
        dry_run=True)
    self._ExpectPatch(
        perimeter_update, perimeter_after,
        'spec.accessLevels,spec.resources,spec.restrictedServices,'
        'useExplicitDryRunSpec', perimeter_before)

    result = self.Run(
        'access-context-manager perimeters dry-run create MY_PERIMETER '
        '   --policy 123 --resources="" --restricted-services="" '
        '   --access-levels=""')

    self.assertEqual(result, perimeter_after)


class DryRunCreateTestAlpha(DryRunCreateTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateDirectionalPolicies_existingPerimeter(self):
    self.SetUpForAPI(self.api_version)
    ingress_policies = self._MakeIngressPolicies()
    egress_policies = self._MakeEgressPolicies()

    initial_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        type_=self._GetPerimeterType('regular'),
        access_levels=None,
        resources=None,
        restricted_services=None)

    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        type_='PERIMETER_TYPE_REGULAR',
        ingress_policies=ingress_policies,
        egress_policies=egress_policies,
        dry_run=True,
        access_levels=None,
        resources=None,
        restricted_services=None)

    perimeter_in_update_request = self.messages.ServicePerimeter(
        spec=expected_perimeter.spec, useExplicitDryRunSpec=True)

    self._ExpectPatch(
        perimeter_in_update_request, expected_perimeter,
        'spec.egressPolicies,spec.ingressPolicies,useExplicitDryRunSpec',
        initial_perimeter)

    ingress_policies_spec_path = self.Touch(
        self.temp_path, 'ingress.yaml', contents=self.INGRESS_POLICIES_SPECS)

    egress_policies_spec_path = self.Touch(
        self.temp_path, 'egress.yaml', contents=self.EGRESS_POLICIES_SPECS)

    result = self.Run(
        'access-context-manager perimeters dry-run create MY_PERIMETER '
        '   --policy 123 --ingress-policies {} --egress-policies {}'.format(
            ingress_policies_spec_path, egress_policies_spec_path))

    self.assertEqual(result, expected_perimeter)

  def testCreateDirectionalPolicies_newPerimeter(self):
    self.SetUpForAPI(self.api_version)
    ingress_policies = self._MakeIngressPolicies()
    egress_policies = self._MakeEgressPolicies()

    initial_perimeter = None

    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        type_='PERIMETER_TYPE_REGULAR',
        ingress_policies=ingress_policies,
        egress_policies=egress_policies,
        dry_run=True,
        access_levels=None,
        resources=None,
        restricted_services=None)

    perimeter_in_update_request = self.messages.ServicePerimeter(
        name='accessPolicies/123/servicePerimeters/MY_PERIMETER',
        title='My Perimeter Title',
        perimeterType=self._GetPerimeterType('regular'),
        description='foo bar',
        spec=expected_perimeter.spec,
        useExplicitDryRunSpec=True)

    self._ExpectPatch(
        perimeter_in_update_request, expected_perimeter,
        'description,name,perimeterType,spec.egressPolicies,spec.ingressPolicies'
        ',title,useExplicitDryRunSpec', initial_perimeter)

    ingress_policies_spec_path = self.Touch(
        self.temp_path, 'ingress.yaml', contents=self.INGRESS_POLICIES_SPECS)

    egress_policies_spec_path = self.Touch(
        self.temp_path, 'egress.yaml', contents=self.EGRESS_POLICIES_SPECS)

    result = self.Run(
        'access-context-manager perimeters dry-run create MY_PERIMETER '
        '   --policy 123 --perimeter-title="My Perimeter Title" '
        '   --perimeter-description="foo bar" --perimeter-type="regular" '
        '   --perimeter-ingress-policies {} --perimeter-egress-policies {}'
        .format(ingress_policies_spec_path, egress_policies_spec_path))

    self.assertEqual(result, expected_perimeter)


if __name__ == '__main__':
  test_case.main()
