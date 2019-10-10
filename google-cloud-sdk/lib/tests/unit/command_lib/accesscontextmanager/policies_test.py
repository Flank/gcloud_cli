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
"""Tests for googlecloudsdk.command_lib.accesscontextmanager.policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.core.cache import fake
from tests.lib.surface import accesscontextmanager


class GetDefaultPolicyTest(parameterized.TestCase, accesscontextmanager.Base):

  def SetUp(self):
    self.SetUpForTrack(calliope_base.ReleaseTrack.GA)

    self.organizations = [
        self.resource_manager_messages.Organization(
            name='organizations/1',
            displayName='example.com'
        ),
        self.resource_manager_messages.Organization(
            name='organizations/2',
            displayName='example.co.uk'
        )
    ]

    self.policies = [
        self.messages.AccessPolicy(
            name='accessPolicies/3',
            parent='organizations/1'
        ),
        self.messages.AccessPolicy(
            name='accessPolicies/4',
            parent='organizations/2'
        )
    ]

    cache = fake.Cache('fake://dummy', create=True)
    self.StartObjectPatch(cache_util.GetCache, '_OpenCache', return_value=cache)

  def testGetDefaultPolicy_NoAccount(self):
    properties.VALUES.core.account.Set(None)

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains('account property is not set')

  @parameterized.parameters(
      'name@project.iam.gserviceaccount.com',
      '123@developer.gserviceaccount.com',
  )
  def testGetDefaultPolicy_ServiceAccount(self, account):
    properties.VALUES.core.account.Set(account)

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains('Unable to resolve domain')

  def testGetDefaultPolicy(self):
    self._ExpectSearchOrganizations('domain:example.com',
                                    self.organizations[:1])
    self._ExpectListPolicies('organizations/1', self.policies[:1])

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, 'accessPolicies/3')

    # Try again without expecting another Search/List call to make sure it's
    # cached
    result = policies.GetDefaultPolicy()

    self.assertEqual(result, 'accessPolicies/3')

  @parameterized.parameters(
      (0, 'No matching organizations'),
      (2, 'Found more than one organization')
  )
  def testGetDefaultPolicy_WrongNumberMatchingOrganizations(self, num, error):
    self._ExpectSearchOrganizations('domain:example.com',
                                    self.organizations[:num])

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains(error)

  def testGetDefaultPolicy_OrganizationsSearchFails(self):
    self._ExpectSearchOrganizations('domain:example.com',
                                    exceptions.HttpError(None, None, None))

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains('Unable to resolve organization for domain')

  @parameterized.parameters(
      (0, 'No matching policies'),
      (2, 'Found more than one access policy')
  )
  def testGetDefaultPolicy_WrongNumberMatchingPolicies(self, num, error):
    self._ExpectSearchOrganizations('domain:example.com',
                                    self.organizations[:1])
    self._ExpectListPolicies('organizations/1', self.policies[:num])

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains(error)

  def testGetDefaultPolicy_PoliciesListFails(self):
    self._ExpectSearchOrganizations('domain:example.com',
                                    self.organizations[:1])
    self._ExpectListPolicies('organizations/1',
                             exceptions.HttpError(None, None, None))

    result = policies.GetDefaultPolicy()

    self.assertEqual(result, None)
    self.AssertLogContains('Unable to resolve policy for organization')


class GetDefaultPolicyNoCacheTest(accesscontextmanager.Base):

  def testGetDefaultPolicy_NoCache_NoPolicy(self):
    result = policies.GetDefaultPolicy()
    self.assertIsNone(result)


if __name__ == '__main__':
  test_case.main()
