# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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


class PerimetersUpdateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
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
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters update --policy 123')

  def testUpdate_NoUpdates(self):
    self.SetUpForAPI(self.api_version)
    # No patch message sent, because nothing is changed.

    self.Run('access-context-manager perimeters update MY_PERIMETER '
             '    --policy 123')
    self.AssertErrContains(
        'The update specified results in an identical resource.')

  def testUpdate_NonRepeatingFields(self):
    self.SetUpForAPI(self.api_version)
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
                      'description,perimeterType,title', '123')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '    --policy 123 --type bridge --title "My Perimeter Title" '
        '    --description "foo bar"')

    self.assertEqual(result, perimeter)

  def testUpdate_ClearRepeatingFields(self):
    self.SetUpForAPI(self.api_version)
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
            restrictedServices=[], accessLevels=[], resources=[]))
    self._ExpectPatch(
        perimeter_update, perimeter, 'status.accessLevels,status.resources,'
        'status.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy 123 --clear-resources --clear-restricted-services '
        '   --clear-access-levels')

    self.assertEqual(result, perimeter)

  def testUpdate_SetRepeatingFields(self):
    self.SetUpForAPI(self.api_version)
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
                'accessPolicies/123/accessLevels/a',
                'accessPolicies/123/accessLevels/b'
            ],
            resources=perimeter.status.resources))
    self._ExpectPatch(
        perimeter_update, perimeter, 'status.accessLevels,status.resources,'
        'status.restrictedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy 123 '
        '   --set-resources projects/12345,projects/67890 '
        '   --set-restricted-services foo.googleapis.com,bar.googleapis.com '
        '   --set-access-levels a,b')

    self.assertEqual(result, perimeter)

  def testUpdate_AddRemoveRepeatingFields(self):
    self.SetUpForAPI(self.api_version)
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
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'status.accessLevels,status.restrictedServices', '123')

    result = self.Run('access-context-manager perimeters update MY_PERIMETER '
                      '   --policy 123 '
                      '   --add-resources projects/12345,projects/67890 '
                      '   --remove-restricted-services foo.googleapis.com '
                      '   --add-access-levels c,d')

    self.assertEqual(result, perimeter_after)

  def testUpdate_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        policy=policy,
        restricted_services=[],
        access_levels=[],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter.name = ('accessPolicies/456/servicePerimeters/MY_PERIMETER')
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

  def testUpdate_InvalidPolicyArg(self):
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager perimeters update MY_PERIMETER '
               '    --policy accessPolicies/123'
               '    --title "My Perimeter Title" ')
    self.assertIn('set to the policy number', text_type(ex.exception))

  def testUpdate_AddServiceFilterFields(self):
    self.SetUpForAPI(self.api_version)

    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        vpc_allowed_services=['bar-vpc.googleapis.com'],
    )
    perimeter_update = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            vpcAccessibleServices=perimeter_after.status.vpcAccessibleServices))
    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'status.vpcAccessibleServices.allowedServices', '123')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy 123 '
        '   --add-vpc-allowed-services bar-vpc.googleapis.com ')

    self.assertEqual(result, perimeter_after)

  def testUpdate_EnableServiceFilters(self):
    self.SetUpForAPI(self.api_version)

    perimeter_before = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE')
    perimeter_after = self._MakePerimeter(
        'MY_PERIMETER',
        title='My Perimeter Title',
        description='foo bar',
        restricted_services=['foo.googleapis.com', 'bar.googleapis.com'],
        type_='PERIMETER_TYPE_BRIDGE',
        enable_vpc_accessible_services=True,
    )
    perimeter_update = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            vpcAccessibleServices=perimeter_after.status.vpcAccessibleServices))

    self._ExpectGet('123', perimeter_before)
    self._ExpectPatch(perimeter_update, perimeter_after,
                      'status.vpcAccessibleServices.enableRestriction', '123')

    result = self.Run('access-context-manager perimeters update MY_PERIMETER '
                      '   --policy 123 '
                      '   --enable-vpc-accessible-services ')

    self.assertEqual(result, perimeter_after)


class PerimetersUpdateTestBeta(PerimetersUpdateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA


class PerimetersUpdateTestAlpha(PerimetersUpdateTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdate_SetDirectionalPolicies(self):
    self.SetUpForAPI(self.api_version)

    ingress_policies = self._MakeIngressPolicies()
    egress_policies = self._MakeEgressPolicies()
    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title=None,
        description=None,
        type_='PERIMETER_TYPE_REGULAR',
        ingress_policies=ingress_policies,
        egress_policies=egress_policies)

    perimeter_in_update_request = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            ingressPolicies=ingress_policies, egressPolicies=egress_policies))

    self._ExpectPatch(perimeter_in_update_request, expected_perimeter,
                      'status.egressPolicies,status.ingressPolicies', '123')

    ingress_policies_spec_path = self.Touch(
        self.temp_path, 'ingress.yaml', contents=self.INGRESS_POLICIES_SPECS)

    egress_policies_spec_path = self.Touch(
        self.temp_path, 'egress.yaml', contents=self.EGRESS_POLICIES_SPECS)

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy 123 '
        '   --set-ingress-policies {} --set-egress-policies {}'.format(
            ingress_policies_spec_path, egress_policies_spec_path))
    self.assertEqual(result, expected_perimeter)

  def testUpdate_clearDirectionalPolicies(self):
    self.SetUpForAPI(self.api_version)

    expected_perimeter = self._MakePerimeter(
        'MY_PERIMETER',
        title=None,
        description=None,
        type_='PERIMETER_TYPE_REGULAR',
        ingress_policies=[],
        egress_policies=[])

    perimeter_in_update_request = self.messages.ServicePerimeter(
        status=self.messages.ServicePerimeterConfig(
            ingressPolicies=[], egressPolicies=[]))
    self._ExpectPatch(perimeter_in_update_request, expected_perimeter,
                      'status.egressPolicies,status.ingressPolicies', '123')

    result = self.Run(
        'access-context-manager perimeters update MY_PERIMETER '
        '   --policy 123 --clear-ingress-policies --clear-egress-policies')

    self.assertEqual(result, expected_perimeter)


if __name__ == '__main__':
  test_case.main()
