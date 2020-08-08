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
"""Unit Tests for ops_agents_policy_converter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from tests.lib import test_case
import six

# These constants don't need to be kept in sync across test files.
OPS_AGENT_DESCRIPTION = 'some desc'
AGENT_RULES = [{
    'type': 'logging',
    'version': '1.6.35',
    'package-state': 'installed',
    'enable-autoupgrade': True,
}, {
    'type': 'metrics',
    'version': '6.0.0',
    'package-state': 'installed',
    'enable-autoupgrade': True,
}]
GROUP_LABELS = [{'env': 'prod'}]
OS_TYPES = [{'version': '7', 'short-name': 'centos'}]
ZONES = ['us-central1-a']
INSTANCES = ['zones/us-central1-a/instances/centos7']
ETAG = 'd9a52b84-2169-46ea-95e7-eb826c9fbc5f'
CREATE_TIME = '2020-06-26T21:59:51.529Z'
UPDATE_TIME = '2020-06-26T22:34:12.237Z'
NAME = 'ops-agents-test-policy'
POLICY_JSON = textwrap.dedent("""\
{
  "agent_rules": [
    {
      "enable_autoupgrade": true,
      "package_state": "installed",
      "type": "logging",
      "version": "1.6.35"
    },
    {
      "enable_autoupgrade": true,
      "package_state": "installed",
      "type": "metrics",
      "version": "6.0.0"
    }
  ],
  "assignment": {
    "group_labels": [
      {
        "env": "prod"
      }
    ],
    "instances": [
      "zones/us-central1-a/instances/centos7"
    ],
    "os_types": [
      {
        "short_name": "centos",
        "version": "7"
      }
    ],
    "zones": [
      "us-central1-a"
    ]
  },
  "create_time": "2020-06-26T21:59:51.529Z",
  "description": "some desc",
  "etag": "d9a52b84-2169-46ea-95e7-eb826c9fbc5f",
  "id": "ops-agents-test-policy",
  "update_time": "2020-06-26T22:34:12.237Z"
}""")

METRICS_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, '6.0.0',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
LOGGING_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING, '1.6.35',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
OPS_AGENT_POLICY_AGENT_RULES = [LOGGING_AGENT_RULE, METRICS_AGENT_RULE]
AGENT_OS_TYPE = agent_policy.OpsAgentPolicy.Assignment.OsType(
    agent_policy.OpsAgentPolicy.Assignment.OsType.OsShortName.CENTOS, '7')
AGENT_ASSIGNMENT = agent_policy.OpsAgentPolicy.Assignment(
    GROUP_LABELS, ZONES, INSTANCES, [AGENT_OS_TYPE])


class OpsAgentPolicyTest(test_case.TestCase):

  def SetUp(self):
    self.maxDiff = None  # pylint: disable=invalid-name

  def testEqual(self):
    policy1 = agent_policy.OpsAgentPolicy(AGENT_ASSIGNMENT,
                                          OPS_AGENT_POLICY_AGENT_RULES,
                                          OPS_AGENT_DESCRIPTION)
    policy2 = agent_policy.OpsAgentPolicy(AGENT_ASSIGNMENT,
                                          OPS_AGENT_POLICY_AGENT_RULES,
                                          OPS_AGENT_DESCRIPTION)
    self.assertEqual(policy1, policy2)

  def testRepr(self):
    policy = agent_policy.OpsAgentPolicy(
        assignment=AGENT_ASSIGNMENT,
        agent_rules=OPS_AGENT_POLICY_AGENT_RULES,
        create_time=CREATE_TIME,
        description=OPS_AGENT_DESCRIPTION,
        etag=ETAG,
        update_time=UPDATE_TIME,
        name=NAME,
    )
    self.assertMultiLineEqual(POLICY_JSON, repr(policy))
    self.assertMultiLineEqual(POLICY_JSON, six.text_type(policy))


class CreateOpsAgentPolicyTest(test_case.TestCase):

  def SetUp(self):
    self.maxDiff = None  # pylint: disable=invalid-name

  def testCreateOpsAgentPolicy(self):
    expected_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_ASSIGNMENT, OPS_AGENT_POLICY_AGENT_RULES, OPS_AGENT_DESCRIPTION)
    # Make sure this doesn't raise an exception.
    actual_ops_agents_policy = agent_policy.CreateOpsAgentPolicy(
        OPS_AGENT_DESCRIPTION, AGENT_RULES, GROUP_LABELS,
        OS_TYPES, ZONES, INSTANCES)
    self.assertMultiLineEqual(repr(expected_ops_agents_policy),
                              repr(actual_ops_agents_policy))

  def testAgentRuleDefaults(self):
    input_agent_rules = [{'type': 'logging'}, {'type': 'metrics'}]
    actual_ops_agents_policy = agent_policy.CreateOpsAgentPolicy(
        OPS_AGENT_DESCRIPTION, input_agent_rules,
        GROUP_LABELS, OS_TYPES, ZONES, INSTANCES)
    for agent_rule in actual_ops_agents_policy.agent_rules:
      self.assertEqual(
          agent_policy.OpsAgentPolicy.AgentRule.Version.CURRENT_MAJOR,
          agent_rule.version)
      self.assertEqual(
          agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED,
          agent_rule.package_state)
      self.assertTrue(agent_rule.enable_autoupgrade)


class UpdateOpsAgentsPolicyTest(test_case.TestCase):

  def SetUp(self):
    self.maxDiff = None  # pylint: disable=invalid-name

  def testUpdateOpsAgentsPolicyWithClearMatcher(self):
    original_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_ASSIGNMENT, OPS_AGENT_POLICY_AGENT_RULES, OPS_AGENT_DESCRIPTION)
    updated_assignment = agent_policy.OpsAgentPolicy.Assignment(
        group_labels=[],
        zones=['us-central1-c'],
        instances=[],
        os_types=[AGENT_OS_TYPE])
    updated_ops_agents_policy = agent_policy.OpsAgentPolicy(
        updated_assignment, OPS_AGENT_POLICY_AGENT_RULES, OPS_AGENT_DESCRIPTION)
    actual_ops_agents_policy = agent_policy.UpdateOpsAgentsPolicy(
        ops_agents_policy=original_ops_agents_policy,
        description=OPS_AGENT_DESCRIPTION,
        agent_rules=None,
        os_types=None,
        group_labels=[],
        zones=['us-central1-c'],
        instances=[])
    self.assertEqual(
        repr(updated_ops_agents_policy), repr(actual_ops_agents_policy))

  def testUpdateOpsAgentsPolicyWithNoneMatcher(self):
    original_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_ASSIGNMENT, OPS_AGENT_POLICY_AGENT_RULES, OPS_AGENT_DESCRIPTION)
    actual_ops_agents_policy = agent_policy.UpdateOpsAgentsPolicy(
        ops_agents_policy=original_ops_agents_policy,
        description=OPS_AGENT_DESCRIPTION,
        agent_rules=None,
        os_types=None,
        group_labels=None,
        zones=None,
        instances=None)
    self.assertEqual(
        repr(original_ops_agents_policy), repr(actual_ops_agents_policy))

  def testUpdateOpsAgentsPolicyWithUpdatingAgents(self):
    original_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_ASSIGNMENT, OPS_AGENT_POLICY_AGENT_RULES, OPS_AGENT_DESCRIPTION)
    updated_metrics_agent_rule = agent_policy.OpsAgentPolicy.AgentRule(
        agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, '6.*.*',
        agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, False)
    updated_agent_rules = [updated_metrics_agent_rule]
    updated_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_ASSIGNMENT, updated_agent_rules, OPS_AGENT_DESCRIPTION)
    actual_ops_agents_policy = agent_policy.UpdateOpsAgentsPolicy(
        ops_agents_policy=original_ops_agents_policy,
        description=OPS_AGENT_DESCRIPTION,
        agent_rules=[{
            'type': 'metrics',
            'version': '6.*.*',
            'package-state': 'installed',
            'enable-autoupgrade': False,
        }],
        os_types=None,
        group_labels=None,
        zones=None,
        instances=None)
    self.assertEqual(
        repr(updated_ops_agents_policy), repr(actual_ops_agents_policy))
