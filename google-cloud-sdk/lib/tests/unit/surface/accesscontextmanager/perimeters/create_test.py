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
"""Tests for `gcloud access-context-manager perimeters create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class PerimetersCreateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _SupportsServiceFilters(self):
    return {
        calliope_base.ReleaseTrack.ALPHA: True,
        calliope_base.ReleaseTrack.BETA: False,
        calliope_base.ReleaseTrack.GA: False
    }[self.track]

  def _ExpectCreate(self, perimeter, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersCreateRequest)
    self.client.accessPolicies_servicePerimeters.Create.Expect(
        req_type(parent=policy_name, servicePerimeter=perimeter),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    get_req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
        get_req_type(name=perimeter.name), perimeter)

  def testCreate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must be specified'):
      self.Run('access-context-manager perimeters create my_perimeter '
               '    --policy 123 --title "My Title"')

  def testCreate(self):
    self.SetUpForAPI(self.api_version)
    perimeter_kwargs = {
        'title': 'My Perimeter Title',
        'description': None,
        'restricted_services': [],
        'access_levels': [],
        'type_': 'PERIMETER_TYPE_REGULAR'
    }

    if self.include_unrestricted_services:
      perimeter_kwargs['unrestricted_services'] = ['*']

    perimeter = self._MakePerimeter('MY_PERIMETER', **perimeter_kwargs)
    self._ExpectCreate(perimeter, '123')

    result = self.Run('access-context-manager perimeters create MY_PERIMETER '
                      '    --policy 123 --title "My Perimeter Title" '
                      '    --resources projects/12345,projects/67890')

    self.assertEqual(result, perimeter)

  def testCreate_PolicyFromProperty(self):

    self.SetUpForAPI(self.api_version)
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)

    perimeter_kwargs = {
        'title': 'My Perimeter Title',
        'description': None,
        'restricted_services': [],
        'access_levels': [],
        'type_': 'PERIMETER_TYPE_REGULAR'
    }

    if self.include_unrestricted_services:
      perimeter_kwargs['unrestricted_services'] = ['*']

    perimeter = self._MakePerimeter('MY_PERIMETER', **perimeter_kwargs)
    perimeter.name = 'accessPolicies/{}/servicePerimeters/MY_PERIMETER'.format(
        policy)
    self._ExpectCreate(perimeter, policy)

    result = self.Run('access-context-manager perimeters create MY_PERIMETER '
                      '    --title "My Perimeter Title" '
                      '    --resources projects/12345,projects/67890')

    self.assertEqual(result, perimeter)

  def testCreate_AllParamsRestrictedServices(self):
    self.SetUpForAPI(self.api_version)
    perimeter_kwargs = {
        'title': 'My Perimeter Title',
        'description': None,
        'restricted_services': ['foo.googleapis.com', 'bar.googleapis.com'],
        'unrestricted_services': [],
        'access_levels': ['MY_LEVEL', 'MY_LEVEL_2'],
        'type_': 'PERIMETER_TYPE_BRIDGE'
    }

    perimeter = self._MakePerimeter('MY_PERIMETER', **perimeter_kwargs)
    self._ExpectCreate(perimeter, '123')

    result = self.Run(
        'access-context-manager perimeters create MY_PERIMETER '
        '    --policy 123 --access-levels MY_LEVEL,MY_LEVEL_2 '
        '    --perimeter-type bridge '
        '    --restricted-services foo.googleapis.com,bar.googleapis.com'
        '    --title "My Perimeter Title" '
        '    --resources projects/12345,projects/67890')

    self.assertEqual(result, perimeter)

  def testCreate_InvalidPolicyArg(self):
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager perimeters create MY_PERIMETER '
               '    --policy accessPolicies/123'
               '    --restricted-services foo.googleapis.com,bar.googleapis.com'
               '    --title "My Perimeter Title" '
               '    --resources projects/12345,projects/67890')
    self.assertIn('set to the policy number', text_type(ex.exception))


class PerimetersCreateTestBeta(PerimetersCreateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA


class PerimetersCreateTestAlpha(PerimetersCreateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreate_ServiceFilterCreation(self):
    self.SetUpForAPI(self.api_version)
    perimeter_kwargs = {
        'title': 'My Perimeter Title',
        'description': None,
        'restricted_services': ['foo.googleapis.com', 'bar.googleapis.com'],
        'unrestricted_services': [],
        'access_levels': ['MY_LEVEL', 'MY_LEVEL_2'],
        'type_': 'PERIMETER_TYPE_BRIDGE',
        'vpc_allowed_services': ['foo-vpc.googleapis.com'],
        'enable_vpc_accessible_services': True,
    }

    perimeter = self._MakePerimeter('MY_PERIMETER', **perimeter_kwargs)
    self._ExpectCreate(perimeter, '123')

    result = self.Run(
        'access-context-manager perimeters create MY_PERIMETER '
        '    --policy 123 --access-levels MY_LEVEL,MY_LEVEL_2 '
        '    --perimeter-type bridge '
        '    --restricted-services foo.googleapis.com,bar.googleapis.com'
        '    --title "My Perimeter Title" '
        '    --resources projects/12345,projects/67890'
        '    --vpc-allowed-services foo-vpc.googleapis.com'
        '    --enable-vpc-accessible-services')

    self.assertEqual(result, perimeter)


if __name__ == '__main__':
  test_case.main()
