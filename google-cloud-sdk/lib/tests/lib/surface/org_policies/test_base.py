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
"""Base classes for all Org Policy tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class _OrgPolicyTestBase(cli_test_base.CliTestBase):
  """Base class for all Org Policy tests."""

  ORGANIZATION_FLAG = '--organization'
  FOLDER_FLAG = '--folder'
  PROJECT_FLAG = '--project'
  CONDITION_FLAG = '--condition'
  ETAG_FLAG = '--etag'
  REMOVE_FLAG = '--remove'
  EFFECTIVE_FLAG = '--effective'
  SHOW_UNSET_FLAG = '--show-unset'

  def RunOrgPolicyCommand(self, *args):
    return self.Run(('alpha', 'org-policies') + args)


class OrgPolicyUnitTestBase(sdk_test_base.WithFakeAuth, _OrgPolicyTestBase):
  """Base class for all Org Policy unit tests."""

  # Constants representing fake resources and values to be used by tests.

  CONSTRAINT_A = 'constraints/testService.testRestrictionA'
  POLICY_NAME_A = 'organizations/12345678/policies/testService.testRestrictionA'
  CONSTRAINT_NAME_A = 'organizations/12345678/constraints/testService.testRestrictionA'

  CONSTRAINT_B = 'constraints/testService.testRestrictionB'
  POLICY_NAME_B = 'organizations/12345678/policies/testService.testRestrictionB'
  CONSTRAINT_NAME_B = 'organizations/12345678/constraints/testService.testRestrictionB'

  ORGANIZATION_ID = '12345678'
  ORGANIZATION_RESOURCE = 'organizations/12345678'

  FOLDER_ID = '12345678'
  FOLDER_RESOURCE = 'folders/12345678'

  PROJECT_ID = 'test-project-id'
  PROJECT_RESOURCE = 'projects/test-project-id'

  RESOURCE_FLAG = _OrgPolicyTestBase.ORGANIZATION_FLAG
  RESOURCE_ID = ORGANIZATION_ID
  RESOURCE = ORGANIZATION_RESOURCE

  VALUE_A = 'test_value_A'
  VALUE_B = 'test_value_B'
  VALUE_C = 'test_value_C'
  VALUE_D = 'test_value_D'

  CONDITION_EXPRESSION_A = 'resource.matchLabels(123, 456)'
  CONDITION_EXPRESSION_B = 'resource.matchLabels(234, 567)'

  ETAG_A = '12345678'
  ETAG_B = '23456789'

  TIMESTAMP_A = '2019-01-01T01:00:00.00Z'
  TIMESTAMP_B = '2019-01-01T01:00:01.00Z'

  def SetUp(self):
    org_policy_client_class = apis.GetClientClass(
        org_policy_service.ORG_POLICY_API_NAME,
        org_policy_service.ORG_POLICY_API_VERSION)
    org_policy_real_client = apis.GetClientInstance(
        org_policy_service.ORG_POLICY_API_NAME,
        org_policy_service.ORG_POLICY_API_VERSION,
        no_http=True)
    mock_org_policy_client = mock.Client(org_policy_client_class,
                                         org_policy_real_client)
    mock_org_policy_client.Mock()
    self.addCleanup(mock_org_policy_client.Unmock)

    self.mock_policy_service = mock_org_policy_client.policies
    self.mock_constraint_service = mock_org_policy_client.constraints
    self.org_policy_messages = org_policy_service.OrgPolicyMessages()

  def Policy(self,
             name=POLICY_NAME_A,
             etag=ETAG_A,
             update_time=TIMESTAMP_A,
             inherit_from_parent=None,
             reset=None,
             rule_data=None):
    """Returns a policy object.

    Args:
      name: str, The name field on the policy.
      etag: str, The etag field on the policy.
      update_time: str, The updateTime field on the policy.
      inherit_from_parent: bool, The inheritFromParent field on the policy.
      reset: bool, The reset field on the policy.
      rule_data: [{str:value}], A list of dicts specifying the information to
        create rules with. The following fields on the dict are supported:
            'condition': str,
            'allow_all': bool,
            'deny_all': bool,
            'enforce': bool,
            'allowed_values': [str],
            'denied_values': [str].
    """
    rules = []
    if rule_data is not None:
      rules = list(map(self._GetRuleFromRuleDatum, rule_data))

    return self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy(
        name=name,
        etag=etag,
        updateTime=update_time,
        inheritFromParent=inherit_from_parent,
        reset=reset,
        rules=rules)

  def Constraint(self, name=CONSTRAINT_NAME_A):
    """Returns a constraint object.

    Args:
      name: str, The name field on the constraint.
    """
    return self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1Constraint(
        name=name)

  def ExpectCreatePolicy(self,
                         response_policy,
                         request_constraint=CONSTRAINT_A,
                         request_parent=RESOURCE,
                         request_etag=None,
                         request_update_time=None):
    """Expect a CreatePolicy call.

    Args:
      response_policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy
        object to be returned as part of the response from the service.
      request_constraint: str, The constraint to be sent as part of the request
        to the service.
      request_parent: str, The parent to be sent as part of the request to the
        service.
      request_etag: str, The etag to be sent as part of the request to the
        service.
      request_update_time: str, The updateTime to be sent as part of the request
        to the service.
    """
    request_policy = copy.deepcopy(response_policy)
    request_policy.etag = request_etag
    request_policy.updateTime = request_update_time
    request = self.org_policy_messages.OrgpolicyPoliciesCreateRequest(
        constraint=request_constraint,
        parent=request_parent,
        googleCloudOrgpolicyV2alpha1Policy=request_policy)

    self.mock_policy_service.Create.Expect(
        request=request, response=response_policy)

  def ExpectGetPolicy(self, response_policy):
    """Expect a GetPolicy call.

    Args:
      response_policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy
        object to be returned as part of the response from the service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesGetRequest(
        name=response_policy.name)

    self.mock_policy_service.Get.Expect(
        request=request, response=response_policy)

  def ExpectGetPolicyWithException(self, exception, request_name=POLICY_NAME_A):
    """Expect a GetPolicy call that throws an exception.

    Args:
      exception: apitools.base.py.exceptions.Error, The exception to be thrown
        from the service.
      request_name: str, The name to be sent as part of the request to the
        service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesGetRequest(
        name=request_name)

    self.mock_policy_service.Get.Expect(request=request, exception=exception)

  def ExpectGetEffectivePolicy(self, response_policy):
    """Expect a GetEffectivePolicy call.

    Args:
      response_policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy
        object to be returned as part of the response from the service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesGetEffectivePolicyRequest(
        name=response_policy.name)

    self.mock_policy_service.GetEffectivePolicy.Expect(
        request=request, response=response_policy)

  def ExpectListPolicies(self, response_policies=None, request_parent=RESOURCE):
    """Expect a ListPolicies call.

    Args:
      response_policies: [messages.GoogleCloudOrgpolicyV2alpha1Policy], The list
        of policy objects to be returned as part of the response from the
        service.
      request_parent: str, The parent to be sent as part of the request to the
        service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesListRequest(
        parent=request_parent)

    if response_policies is None:
      response_policies = []
    response = self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1ListPoliciesResponse(
        policies=response_policies)

    self.mock_policy_service.List.Expect(request=request, response=response)

  def ExpectListConstraints(self,
                            response_constraints=None,
                            request_parent=RESOURCE):
    """Mock a ListConstraints call.

    Args:
      response_constraints: [messages.GoogleCloudOrgpolicyV2alpha1Constraint],
        The list of constraint objects to be returned as part of the response
        from the service.
      request_parent: str, The parent to be sent as part of the request to the
        service.
    """
    request = self.org_policy_messages.OrgpolicyConstraintsListRequest(
        parent=request_parent)

    if response_constraints is None:
      response_constraints = []
    response = self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1ListConstraintsResponse(
        constraints=response_constraints)

    self.mock_constraint_service.List.Expect(request=request, response=response)

  def ExpectUpdatePolicy(self,
                         request_policy,
                         request_force_unconditional_write=False,
                         response_etag=ETAG_B,
                         response_update_time=TIMESTAMP_B):
    """Mock an UpdatePolicy call.

    Args:
      request_policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy
        object to be sent as part of the request to the service.
      request_force_unconditional_write: bool, The forceUnconditionalWrite
        toggle to be sent as part of the request to the service.
      response_etag: str, The etag to be returned as part of the response from
        the service.
      response_update_time: str, The updateTime to be returned as part of the
        response from the service.

    Returns:
      The policy object returned from the service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesPatchRequest(
        name=request_policy.name,
        forceUnconditionalWrite=request_force_unconditional_write,
        googleCloudOrgpolicyV2alpha1Policy=request_policy)

    response_policy = copy.deepcopy(request_policy)
    response_policy.etag = response_etag
    response_policy.updateTime = response_update_time

    self.mock_policy_service.Patch.Expect(
        request=request, response=response_policy)

    return response_policy

  def ExpectDeletePolicy(self, request_name=POLICY_NAME_A):
    """Expect a DeletePolicy call.

    Args:
      request_name: str, The name to be sent as part of the request to the
        service.

    Returns:
      The response from the service.
    """
    request = self.org_policy_messages.OrgpolicyPoliciesDeleteRequest(
        name=request_name)

    response = self.org_policy_messages.GoogleProtobufEmpty()

    self.mock_policy_service.Delete.Expect(request=request, response=response)

    return response

  def _GetRuleFromRuleDatum(self, rule_datum):
    """Returns a policy rule object.

    Args:
      rule_datum: {str:value}, A dict specifying the information to create a
        rule with. The following fields on the dict are supported:
            'condition': str,
            'allow_all': bool,
            'deny_all': bool,
            'enforce': bool,
            'allowed_values': [str],
            'denied_values': [str].
    """
    # Check that rule_datum has no unsupported keys.
    if not {
        'condition', 'allow_all', 'deny_all', 'enforce', 'allowed_values',
        'denied_values'
    }.issuperset(rule_datum):
      raise ValueError('Unsupported keys in rule_datum.')

    condition = None
    if 'condition' in rule_datum:
      condition = self.org_policy_messages.GoogleTypeExpr(
          expression=rule_datum.get('condition'))

    values = None
    if 'allowed_values' in rule_datum or 'denied_values' in rule_datum:
      values = self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1PolicyPolicyRuleStringValues(
          allowedValues=rule_datum.get('allowed_values') or [],
          deniedValues=rule_datum.get('denied_values') or [])

    return self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1PolicyPolicyRule(
        condition=condition,
        allowAll=rule_datum.get('allow_all'),
        denyAll=rule_datum.get('deny_all'),
        enforce=rule_datum.get('enforce'),
        values=values)
