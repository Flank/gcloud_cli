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

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import guest_policy_to_ops_agents_policy_converter as converter
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from tests.lib import test_case

# These constants don't need to be kept in sync across test files.
OPS_AGENT_DESCRIPTION = 'some desc'
AGENT_RULES = [{
    'type': 'logging',
    'version': '1.6.35-1',
    'packageState': 'installed',
    'enableAutoupgrade': True
}, {
    'type': 'metrics',
    'version': '6.0.0-1',
    'packageState': 'installed',
    'enableAutoupgrade': True
}]
GROUP_LABELS = [{'env': 'prod'}]
OS_TYPES = [{'version': '7', 'short-name': 'centos'}]
ZONES = ['us-central1-a']
INSTANCES = ['zones/us-central1-a/instances/centos7']
METRICS_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, '6.0.0-1',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
LOGGING_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING, '1.6.35-1',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
OPS_AGENT_POLICY_AGENT_RULES = [LOGGING_AGENT_RULE, METRICS_AGENT_RULE]
AGENT_RULE_OS_TYPE = agent_policy.OpsAgentPolicy.Assignment.OsType(
    agent_policy.OpsAgentPolicy.Assignment.OsType.OsShortName.CENTOS, '7')
AGENT_RULE_ASSIGNMENT = agent_policy.OpsAgentPolicy.Assignment(
    GROUP_LABELS, ZONES, INSTANCES, [AGENT_RULE_OS_TYPE])
CREATE_TIME = '2020-06-17T22:42:38.676Z'
UPDATE_TIME = '2020-06-18T23:42:38.676Z'
ETAG = 'c0c751ec-839d-4de5-b5bb-1a934011020a'
POLICY_NAME = 'projects/160362642680/guestPolicies/test-policy-debian'
GUEST_POLICY_YAML = textwrap.dedent("""\
assignment:
  groupLabels:
  - labels:
      env: prod
  instances:
  - zones/us-central1-a/instances/centos7
  osTypes:
  - osShortName: centos
    osVersion: '7'
  zones:
  - us-central1-a
createTime: '2020-06-17T22:42:38.676Z'
updateTime: '2020-06-18T23:42:38.676Z'
etag: c0c751ec-839d-4de5-b5bb-1a934011020a
name: projects/160362642680/guestPolicies/test-policy-debian
description: '{"type": "ops-agents","description": "some desc","agentRules": [{"enableAutoupgrade": true, "packageState": "installed", "type": "logging", "version": "1.6.35-1"},{"enableAutoupgrade": true, "packageState": "installed", "type": "metrics", "version": "6.0.0-1"}]}'
packageRepositories:
- yum:
    baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-logging-el7-x86_64-all
    displayName: Google Cloud Logging Agent Repository
    gpgKeys:
    - https://packages.cloud.google.com/yum/doc/yum-key.gpg
    - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
    id: google-cloud-logging
- yum:
    baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-monitoring-el7-x86_64-all
    displayName: Google Cloud Monitoring Agent Repository
    gpgKeys:
    - https://packages.cloud.google.com/yum/doc/yum-key.gpg
    - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
    id: google-cloud-monitoring
packages:
- desiredState: UPDATED
  name: google-fluentd
- desiredState: UPDATED
  name: google-fluentd-catch-all-config
- desiredState: UPDATED
  name: stackdriver-agent
recipes:
- desiredState: UPDATED
  installSteps:
  - scriptRun:
      script: |-
        #!/bin/bash
        sleep 5m
        sudo service google-fluentd stop
        sudo yum remove google-fluentd
        sudo yum install -y "google-fluentd-1.6.35-1"

        # Start the service post installation.
        /usr/sbin/service google-fluentd start

  name: start-google-fluentd-service
- desiredState: UPDATED
  installSteps:
  - scriptRun:
      script: |-
        #!/bin/bash
        sleep 5m
        sudo service stackdriver-agent stop
        sudo yum remove stackdriver-agent
        sudo yum install -y "stackdriver-agent-6.0.0-1"

        # Start the service post installation.
        /usr/sbin/service stackdriver-agent start

  name: start-stackdriver-agent-service
""")


class GuestPolicyToOpsAgentPolicyTest(test_case.TestCase):

  def _LoadMessage(self, serialized_yaml, message_type):
    resource_to_parse = yaml.load(serialized_yaml)
    return encoding.PyValueToMessage(message_type, resource_to_parse)

  def SetUp(self):
    self.messages = osconfig_api_utils.GetClientMessages(
        None, api_version_override='v1beta')
    self.expected_ops_agents_policy = agent_policy.OpsAgentPolicy(
        AGENT_RULE_ASSIGNMENT, OPS_AGENT_POLICY_AGENT_RULES,
        OPS_AGENT_DESCRIPTION, ETAG, POLICY_NAME, UPDATE_TIME, CREATE_TIME)
    self.guest_policy = self._LoadMessage(
        GUEST_POLICY_YAML, self.messages.GuestPolicy)

  def testConvertGuestPolicyToOpsAgentPolicy(self):
    actual_ops_agents_policy = converter.ConvertGuestPolicyToOpsAgentPolicy(
        self.guest_policy)
    self.assertEqual(self.expected_ops_agents_policy, actual_ops_agents_policy)

  def testConvertGuestPolicyToOpsAgentPolicyNonJsonDescription_Raises(self):
    description_missing_quote = '{type": "ops-agents}'
    self.guest_policy.description = description_missing_quote
    with self.assertRaisesRegex(
        exceptions.BadArgumentException,
        'description field is not a JSON object: .*'):
      converter.ConvertGuestPolicyToOpsAgentPolicy(self.guest_policy)

  def testConvertGuestPolicyToOpsAgentPolicyNonJsonObjDescription_Raises(self):
    description_json_array = '[]'
    self.guest_policy.description = description_json_array
    with self.assertRaisesRegex(
        exceptions.BadArgumentException,
        'description field is not a JSON object.'):
      converter.ConvertGuestPolicyToOpsAgentPolicy(self.guest_policy)

  def testConvertGuestPolicyToOpsAgentPolicyMissingKeyDescription_Raises(self):
    description_key_missing = (
        '{"type": "ops-agents", "agentRules": [{"enableAutoupgrade": true, '
        '"type": "logging", "version": "1.6.35-1"}]}')
    self.guest_policy.description = description_key_missing
    with self.assertRaisesRegex(
        exceptions.BadArgumentException,
        'missing a required key description:.*'):
      converter.ConvertGuestPolicyToOpsAgentPolicy(self.guest_policy)

  def testConvertGuestPolicyToOpsAgentPolicyMissingKeyAgentRules_Raises(self):
    agent_rules_key_missing = (
        '{"type": "ops-agents","description": "some desc"}')
    self.guest_policy.description = agent_rules_key_missing
    with self.assertRaisesRegex(
        exceptions.BadArgumentException,
        'missing a required key agentRules:.*'):
      converter.ConvertGuestPolicyToOpsAgentPolicy(self.guest_policy)

  def testConvertGuestPolicyToOpsAgentPolicyMissingField_Raises(self):
    agent_rules_missing_package_state_field = (
        '{"type": "ops-agents","description": "some desc","agentRules": '
        '[{"enableAutoupgrade": true, "type": "logging", "version": '
        '"1.6.35-1"}]}')
    self.guest_policy.description = agent_rules_missing_package_state_field
    with self.assertRaisesRegex(
        exceptions.BadArgumentException,
        'agent rule specification .* missing a required key.*packageState'):
      converter.ConvertGuestPolicyToOpsAgentPolicy(self.guest_policy)


if __name__ == '__main__':
  test_case.main()
