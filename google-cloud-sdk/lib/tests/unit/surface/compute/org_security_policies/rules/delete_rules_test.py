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
"""Tests for the organization security policy associations delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class OrgSecurityPoliciesRulessDeleteBetaTest(sdk_test_base.WithFakeAuth,
                                              cli_test_base.CliTestBase,
                                              waiter_test_base.Base):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def CreateTestOrgSecurityPolicyMessage(self, **kwargs):
    return self.messages.SecurityPolicy(
        description='test-description',
        displayName='test-sp',
        type=self.messages.SecurityPolicy.TypeValueValuesEnum.FIREWALL)

  def _GetOperationMessage(self, operation_name, status, resource_uri=None):
    return self.messages.Operation(
        name=operation_name,
        status=status,
        selfLink='https://compute.googleapis.com/compute/{0}/locations/'
        'global/operations/{1}'.format(self.api_version, operation_name),
        targetLink=resource_uri)

  def testRulesDeleteOrgSecurityPolicy(self):
    self.mock_client.organizationSecurityPolicies.RemoveRule.Expect(
        self.messages.ComputeOrganizationSecurityPoliciesRemoveRuleRequest(
            securityPolicy='12345678910', priority=10),
        self._GetOperationMessage(
            operation_name='org-12345-operation-myop',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING))
    self.mock_client.globalOrganizationOperations.Get.Expect(
        self.messages.ComputeGlobalOrganizationOperationsGetRequest(
            parentId='organizations/12345',
            operation='org-12345-operation-myop'),
        self._GetOperationMessage(
            operation_name='org-12345-operation-myop',
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            resource_uri='https://compute.googleapis.com/compute/{0}/'
            'locations/global/securityPolicies/{1}'.format(
                self.api_version, '12345678910')))
    self.Run('compute org-security-policies rules delete 10 '
             '--security-policy 12345678910')
    self.AssertOutputEquals('')
    self.AssertErrContains('Delete a rule of the organization Security Policy.')


class OrgSecurityPoliciesRulessDeleteAlphaTest(
    OrgSecurityPoliciesRulessDeleteBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)


if __name__ == '__main__':
  test_case.main()
