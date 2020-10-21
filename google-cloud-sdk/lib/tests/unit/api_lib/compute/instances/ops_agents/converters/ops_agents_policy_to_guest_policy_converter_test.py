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

import collections
import json
import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import ops_agents_policy_to_guest_policy_converter as converter
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.core import yaml
from tests.lib import test_case


# TODO(b/160016059): cleaned up some duplications already in this cl/331039126,
# still there is redundant code left in the YAML file which needs another round.
class _GuestPolicyTemplates(
    collections.namedtuple('_GuestPolicyTemplates', ('os_types', 'instances'))):
  pass


_GUEST_POLICY_TEMPLATES = {
    'rhel':
        _GuestPolicyTemplates(
            os_types=[
                agent_policy.OpsAgentPolicy.Assignment.OsType('rhel', '7.8')
            ],
            instances=[
                'zones/us-central1-a/instances/rhel7-0',
                'zones/us-central1-a/instances/rhel7-1'
            ]),
    'sles':
        _GuestPolicyTemplates(
            os_types=[
                agent_policy.OpsAgentPolicy.Assignment.OsType('sles', '12.4')
            ],
            instances=[
                'zones/us-central1-a/instances/sles12',
            ]),
    'centos':
        _GuestPolicyTemplates(
            os_types=[
                agent_policy.OpsAgentPolicy.Assignment.OsType('centos', '7')
            ],
            instances=['zones/us-central1-a/instances/centos7']),
    'debian':
        _GuestPolicyTemplates(
            os_types=[
                agent_policy.OpsAgentPolicy.Assignment.OsType('debian', '9')
            ],
            instances=['zones/us-central1-a/instances/debian9']),
}
OPS_AGENT_RULE_DESCRIPTION = 'some desc'
GROUP_LABELS = [{'env': 'prod'}]
CENTOS_OS_TYPES = [{
    'version': '7',
    'short-name': 'centos',
}]
DEBIAN_OS_TYPES = [{
    'version': '9',
    'short-name': 'debian',
}]
ZONES = ['us-central1-a']


def _CreateOpsAgentPolicy(distro, agent_rules):
  return agent_policy.OpsAgentPolicy(
      assignment=agent_policy.OpsAgentPolicy.Assignment(
          group_labels=GROUP_LABELS,
          zones=ZONES,
          instances=_GUEST_POLICY_TEMPLATES[distro].instances,
          os_types=_GUEST_POLICY_TEMPLATES[distro].os_types),
      agent_rules=agent_rules,
      description=OPS_AGENT_RULE_DESCRIPTION,
      etag=ETAG,
      name=None,
      update_time=None,
      create_time=None)


def _CreateMetricsAgentRule(
    agent_version='6.0.0',
    package_state=agent_policy.OpsAgentPolicy.AgentRule.PackageState
    .INSTALLED,
    enable_autoupgrade=True):
  return agent_policy.OpsAgentPolicy.AgentRule(
      agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, agent_version,
      package_state, enable_autoupgrade)


def _CreateLoggingAgentRule(
    agent_version='1.6.35',
    package_state=agent_policy.OpsAgentPolicy.AgentRule.PackageState
    .INSTALLED,
    enable_autoupgrade=True):
  return agent_policy.OpsAgentPolicy.AgentRule(
      agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING, agent_version,
      package_state, enable_autoupgrade)


def _CreateOpsAgentRule(
    agent_version='1.0.0',
    package_state=agent_policy.OpsAgentPolicy.AgentRule.PackageState
    .INSTALLED,
    enable_autoupgrade=True):
  return agent_policy.OpsAgentPolicy.AgentRule(
      agent_policy.OpsAgentPolicy.AgentRule.Type.OPS_AGENT, agent_version,
      package_state, enable_autoupgrade)

LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES = [
    _CreateLoggingAgentRule(),
    _CreateMetricsAgentRule()
]
OPS_AGENT_RULE_POLICY_AGENT_RULES = [_CreateOpsAgentRule()]
ETAG = 'd9a52b84-2169-46ea-95e7-eb826c9fbc5f'

# TODO(b/160016059): Fix the indentation in AGENT_RULE_RUN_SCRIPT.
AGENT_RULE_RUN_SCRIPT = textwrap.dedent("""\
    #!/bin/bash -e
            sudo rm {repo_dir}/{repo_name}.repo || true; find {cache_dir} -name '*{repo_name}*' | xargs sudo rm -rf || true
            for i in {{1..5}}; do
              if (sudo {package_manager} remove -y {package_name} || true; sudo {package_manager} install -y '{package_name}{package_suffix}';{additional_install} sudo service {package_name} start); then
                break
              fi
              sleep 1m
            done""")

OPS_AGENT_RULE_RUN_SCRIPT = textwrap.dedent("""\
    #!/bin/bash -e
            sudo rm {repo_dir}/{repo_name}.repo || true; find {cache_dir} -name '*{repo_name}*' | xargs sudo rm -rf || true
            for i in {{1..5}}; do
              if (sudo {package_manager} remove -y {package_name} || true; sudo {package_manager} install -y '{package_name}{package_suffix}';{additional_install} sudo systemctl start google-cloud-ops-agent.target); then
                break
              fi
              sleep 1m
            done""")

APT_GUEST_POLICY_YAML = textwrap.dedent("""\
    assignment:
      groupLabels:
      - labels:
          env: prod
      instances:
      - zones/us-central1-a/instances/debian9
      osTypes:
      - osShortName: debian
        osVersion: '9'
      zones:
      - us-central1-a
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {logging_enable_autoupgrade}, "packageState": "{logging_package_state}", "type": "logging", "version": "{logging_version}"}},{{"enableAutoupgrade": {metrics_enable_autoupgrade}, "packageState": "{metrics_package_state}", "type": "metrics", "version": "{metrics_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - apt:
        components:
        - main
        distribution: google-cloud-logging-stretch{logging_repo_suffix}
        gpgKey: https://packages.cloud.google.com/apt/doc/apt-key.gpg
        uri: http://packages.cloud.google.com/apt
    - apt:
        components:
        - main
        distribution: google-cloud-monitoring-stretch{metrics_repo_suffix}
        gpgKey: https://packages.cloud.google.com/apt/doc/apt-key.gpg
        uri: http://packages.cloud.google.com/apt
    packages:
    - desiredState: {logging_desired_state}
      name: google-fluentd
    - desiredState: {logging_desired_state}
      name: google-fluentd-catch-all-config
    - desiredState: {metrics_desired_state}
      name: stackdriver-agent
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {logging_run_script}
      name: set-google-fluentd-version-0
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {metrics_run_script}
      name: set-stackdriver-agent-version-0
    """)
UNIFIED_AGENT_APT_GUEST_POLICY_YAML = textwrap.dedent("""\
    assignment:
      groupLabels:
      - labels:
          env: prod
      instances:
      - zones/us-central1-a/instances/debian9
      osTypes:
      - osShortName: debian
        osVersion: '9'
      zones:
      - us-central1-a
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {ops_agent_enable_autoupgrade}, "packageState": "{ops_agent_package_state}", "type": "ops-agent", "version": "{ops_agent_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - apt:
        components:
        - main
        distribution: google-cloud-ops-agent-stretch{ops_agent_repo_suffix}
        gpgKey: https://packages.cloud.google.com/apt/doc/apt-key.gpg
        uri: http://packages.cloud.google.com/apt
    packages:
    - desiredState: {ops_agent_desired_state}
      name: google-cloud-ops-agent
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {ops_agent_run_script}
      name: set-ops-agent-version-0
    """)
YUM_GUEST_POLICY_YAML = textwrap.dedent("""\
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
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {logging_enable_autoupgrade}, "packageState": "{logging_package_state}", "type": "logging", "version": "{logging_version}"}},{{"enableAutoupgrade": {metrics_enable_autoupgrade}, "packageState": "{metrics_package_state}", "type": "metrics", "version": "{metrics_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - yum:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-logging-el7-x86_64{logging_repo_suffix}
        displayName: Google Cloud Logging Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-logging
    - yum:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-monitoring-el7-x86_64{metrics_repo_suffix}
        displayName: Google Cloud Monitoring Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-monitoring
    packages:
    - desiredState: {logging_desired_state}
      name: google-fluentd
    - desiredState: {logging_desired_state}
      name: google-fluentd-catch-all-config
    - desiredState: {logging_desired_state}
      name: google-fluentd-start-service
    - desiredState: {metrics_desired_state}
      name: stackdriver-agent
    - desiredState: {metrics_desired_state}
      name: stackdriver-agent-start-service
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {logging_run_script}
      name: set-google-fluentd-version-0
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {metrics_run_script}
      name: set-stackdriver-agent-version-0
    """)
UNIFIED_AGENT_YUM_GUEST_POLICY_YAML = textwrap.dedent("""\
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
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {ops_agent_enable_autoupgrade}, "packageState": "{ops_agent_package_state}", "type": "ops-agent", "version": "{ops_agent_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - yum:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-ops-agent-el7-x86_64{ops_agent_repo_suffix}
        displayName: Google Cloud Ops Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-ops-agent
    packages:
    - desiredState: {ops_agent_desired_state}
      name: google-cloud-ops-agent
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {ops_agent_run_script}
      name: set-ops-agent-version-0
    """)
ZYPPER_GUEST_POLICY_YAML = textwrap.dedent("""\
    assignment:
      groupLabels:
      - labels:
          env: prod
      instances:
      - zones/us-central1-a/instances/sles12
      osTypes:
      - osShortName: sles
        osVersion: '12.4'
      zones:
      - us-central1-a
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {logging_enable_autoupgrade}, "packageState": "{logging_package_state}", "type": "logging", "version": "{logging_version}"}},{{"enableAutoupgrade": {metrics_enable_autoupgrade}, "packageState": "{metrics_package_state}", "type": "metrics", "version": "{metrics_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - zypper:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-logging-sles12-x86_64{logging_repo_suffix}
        displayName: Google Cloud Logging Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-logging
    - zypper:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-monitoring-sles12-x86_64{metrics_repo_suffix}
        displayName: Google Cloud Monitoring Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-monitoring
    packages:
    - desiredState: {logging_desired_state}
      name: google-fluentd
    - desiredState: {logging_desired_state}
      name: google-fluentd-catch-all-config
    - desiredState: {logging_desired_state}
      name: google-fluentd-start-service
    - desiredState: {metrics_desired_state}
      name: stackdriver-agent
    - desiredState: {metrics_desired_state}
      name: stackdriver-agent-start-service
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {logging_run_script}
      name: set-google-fluentd-version-0
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {metrics_run_script}
      name: set-stackdriver-agent-version-0
    """)
UNIFIED_AGENT_ZYPPER_GUEST_POLICY_YAML = textwrap.dedent("""\
    assignment:
      groupLabels:
      - labels:
          env: prod
      instances:
      - zones/us-central1-a/instances/sles12
      osTypes:
      - osShortName: sles
        osVersion: '12.4'
      zones:
      - us-central1-a
    description: '{{"type": "ops-agents", "description": "some desc", "agentRules": [{{"enableAutoupgrade": {ops_agent_enable_autoupgrade}, "packageState": "{ops_agent_package_state}", "type": "ops-agent", "version": "{ops_agent_version}"}}]}}'
    etag: {etag}
    packageRepositories:
    - zypper:
        baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-ops-agent-sles12-x86_64{ops_agent_repo_suffix}
        displayName: Google Cloud Ops Agent Repository
        gpgKeys:
        - https://packages.cloud.google.com/yum/doc/yum-key.gpg
        - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
        id: google-cloud-ops-agent
    packages:
    - desiredState: {ops_agent_desired_state}
      name: google-cloud-ops-agent
    recipes:
    - desiredState: UPDATED
      version: '0'
      installSteps:
      - scriptRun:
          script: |-
            {ops_agent_run_script}
      name: set-ops-agent-version-0
    """)


class OpsAgentPolicyToGuestPolicyTest(test_case.TestCase):

  def _LoadMessage(self, serialized_yaml, message_type):
    resource_to_parse = yaml.load(serialized_yaml)
    return encoding.PyValueToMessage(message_type, resource_to_parse)

  def _AssertProtoMessageEqual(self, expected, actual):
    """Assert two protos are equal by comparing the converted JSON strings."""
    return self.assertMultiLineEqual(
        json.dumps(
            json.loads(encoding.MessageToJson(expected)),
            sort_keys=True,
            indent=2),
        json.dumps(
            json.loads(encoding.MessageToJson(actual)),
            sort_keys=True,
            indent=2))

  def _CreateGuestPolicyYUM(self,
                            logging_enable_autoupgrade='true',
                            logging_package_state='installed',
                            logging_version='1.6.35',
                            metrics_enable_autoupgrade='true',
                            metrics_package_state='installed',
                            metrics_version='6.0.0',
                            logging_desired_state='UPDATED',
                            metrics_desired_state='UPDATED',
                            logging_repo_suffix='-all',
                            metrics_repo_suffix='-all',
                            logging_package_suffix='-1.6.35-1.el7',
                            metrics_package_suffix='-6.0.0-1.el7'):
    return self._LoadMessage(
        YUM_GUEST_POLICY_YAML.format(
            logging_enable_autoupgrade=logging_enable_autoupgrade,
            logging_package_state=logging_package_state,
            logging_version=logging_version,
            metrics_enable_autoupgrade=metrics_enable_autoupgrade,
            metrics_package_state=metrics_package_state,
            metrics_version=metrics_version,
            logging_desired_state=logging_desired_state,
            metrics_desired_state=metrics_desired_state,
            logging_repo_suffix=logging_repo_suffix,
            metrics_repo_suffix=metrics_repo_suffix,
            etag=ETAG,
            logging_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/yum.repos.d',
                repo_name='google-cloud-logging',
                additional_install=' sudo yum install -y google-fluentd-catch-all-config;',
                cache_dir='/var/cache/yum',
                package_name='google-fluentd',
                package_manager='yum',
                package_suffix=logging_package_suffix),
            metrics_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/yum.repos.d',
                repo_name='google-cloud-monitoring',
                additional_install='',
                cache_dir='/var/cache/yum',
                package_name='stackdriver-agent',
                package_manager='yum',
                package_suffix=metrics_package_suffix)),
        self.messages.GuestPolicy)

  def _CreateGuestPolicyZypper(self,
                               logging_enable_autoupgrade='true',
                               logging_package_state='installed',
                               logging_version='1.6.35',
                               metrics_enable_autoupgrade='true',
                               metrics_package_state='installed',
                               metrics_version='6.0.0',
                               logging_desired_state='UPDATED',
                               metrics_desired_state='UPDATED',
                               logging_repo_suffix='-all',
                               metrics_repo_suffix='-all',
                               logging_package_suffix='=1.6.35-1',
                               metrics_package_suffix='=6.0.0-1'):
    return self._LoadMessage(
        ZYPPER_GUEST_POLICY_YAML.format(
            logging_enable_autoupgrade=logging_enable_autoupgrade,
            logging_package_state=logging_package_state,
            logging_version=logging_version,
            metrics_enable_autoupgrade=metrics_enable_autoupgrade,
            metrics_package_state=metrics_package_state,
            metrics_version=metrics_version,
            logging_desired_state=logging_desired_state,
            metrics_desired_state=metrics_desired_state,
            logging_repo_suffix=logging_repo_suffix,
            metrics_repo_suffix=metrics_repo_suffix,
            etag=ETAG,
            logging_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/zypp/repos.d',
                repo_name='google-cloud-logging',
                additional_install=' sudo zypper install -y google-fluentd-catch-all-config;',
                cache_dir='/var/cache/zypp',
                package_name='google-fluentd',
                package_manager='zypper',
                package_suffix=logging_package_suffix),
            metrics_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/zypp/repos.d',
                repo_name='google-cloud-monitoring',
                additional_install='',
                cache_dir='/var/cache/zypp',
                package_name='stackdriver-agent',
                package_manager='zypper',
                package_suffix=metrics_package_suffix)),
        self.messages.GuestPolicy)

  def _CreateGuestPolicyAPT(self,
                            logging_enable_autoupgrade='true',
                            logging_package_state='installed',
                            logging_version='1.6.35',
                            metrics_enable_autoupgrade='true',
                            metrics_package_state='installed',
                            metrics_version='6.0.0',
                            logging_desired_state='UPDATED',
                            metrics_desired_state='UPDATED',
                            logging_repo_suffix='-all',
                            metrics_repo_suffix='-all',
                            logging_package_suffix='=1.6.35-1*',
                            metrics_package_suffix='=6.0.0-1*'):
    return self._LoadMessage(
        APT_GUEST_POLICY_YAML.format(
            logging_enable_autoupgrade=logging_enable_autoupgrade,
            logging_package_state=logging_package_state,
            logging_version=logging_version,
            metrics_enable_autoupgrade=metrics_enable_autoupgrade,
            metrics_package_state=metrics_package_state,
            metrics_version=metrics_version,
            logging_desired_state=logging_desired_state,
            metrics_desired_state=metrics_desired_state,
            logging_repo_suffix=logging_repo_suffix,
            metrics_repo_suffix=metrics_repo_suffix,
            etag=ETAG,
            logging_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/apt/sources.list.d',
                repo_name='google-cloud-logging',
                additional_install=' sudo apt-get install -y google-fluentd-catch-all-config;',
                cache_dir='/var/cache/apt',
                package_name='google-fluentd',
                package_manager='apt-get',
                package_suffix=logging_package_suffix),
            metrics_run_script=AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/apt/sources.list.d',
                repo_name='google-cloud-monitoring',
                additional_install='',
                cache_dir='/var/cache/apt',
                package_name='stackdriver-agent',
                package_manager='apt-get',
                package_suffix=metrics_package_suffix)),
        self.messages.GuestPolicy)

  def SetUp(self):
    self.maxDiff = None  # pylint: disable=invalid-name
    self.messages = osconfig_api_utils.GetClientMessages(
        None, api_version_override='v1beta')

  def testConvertOpsAgentPolicyToGuestPolicyCentos(self):
    expected_guest_policy = self._CreateGuestPolicyYUM()
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyCentos_UnifiedAgent(self):
    expected_guest_policy = self._LoadMessage(
        UNIFIED_AGENT_YUM_GUEST_POLICY_YAML.format(
            ops_agent_enable_autoupgrade='true',
            ops_agent_package_state='installed',
            ops_agent_version='1.0.0',
            ops_agent_desired_state='UPDATED',
            ops_agent_repo_suffix='-all',
            etag=ETAG,
            ops_agent_run_script=OPS_AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/yum.repos.d',
                repo_name='google-cloud-ops-agent',
                additional_install='',
                cache_dir='/var/cache/yum',
                package_name='google-cloud-ops-agent',
                package_manager='yum',
                package_suffix='-1.0.0-1.el7')),
        self.messages.GuestPolicy)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyCentosLegacy(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        metrics_version='5.5.2-1000',
        metrics_enable_autoupgrade='false',
        metrics_desired_state='INSTALLED',
        metrics_package_suffix='-5.5.2-1000.el7')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='5.5.2-1000', enable_autoupgrade=False)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos',
        [_CreateLoggingAgentRule(), metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyCentosLatest(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        metrics_version='latest',
        logging_version='latest',
        metrics_package_suffix='',
        logging_package_suffix='')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='latest')
    logging_agent_latest = _CreateLoggingAgentRule(
        agent_version='latest')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', [logging_agent_latest, metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyCentosCurrentMajor(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        metrics_version='latest',
        logging_version='1.*.*',
        logging_repo_suffix='-1',
        metrics_package_suffix='',
        logging_package_suffix='-1.*')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='latest')
    logging_agent_current_major = _CreateLoggingAgentRule(
        agent_version='current-major')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', [logging_agent_current_major, metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self.assertEqual(
        expected_guest_policy, actual_guest_policy,
        'Expected guest policy:\n{}\nActual guest policy:\n{}'.format(
            expected_guest_policy, actual_guest_policy))

  def testConvertOpsAgentPolicyToGuestPolicySles(self):
    expected_guest_policy = self._CreateGuestPolicyZypper()
    ops_agents_policy = _CreateOpsAgentPolicy(
        'sles', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicySles_UnifiedAgent(self):
    expected_guest_policy = self._LoadMessage(
        UNIFIED_AGENT_ZYPPER_GUEST_POLICY_YAML.format(
            ops_agent_enable_autoupgrade='true',
            ops_agent_package_state='installed',
            ops_agent_version='1.0.0',
            ops_agent_desired_state='UPDATED',
            ops_agent_repo_suffix='-all',
            etag=ETAG,
            ops_agent_run_script=OPS_AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/zypp/repos.d',
                repo_name='google-cloud-ops-agent',
                additional_install='',
                cache_dir='/var/cache/zypp',
                package_name='google-cloud-ops-agent',
                package_manager='zypper',
                package_suffix='=1.0.0-1')),
        self.messages.GuestPolicy)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'sles', OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicySlesLegacy(self):
    expected_guest_policy = self._CreateGuestPolicyZypper(
        metrics_enable_autoupgrade='false',
        metrics_version='5.5.2-1000',
        metrics_desired_state='INSTALLED',
        metrics_package_suffix='=5.5.2-1000')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='5.5.2-1000', enable_autoupgrade=False)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'sles', [_CreateLoggingAgentRule(), metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicySlesLatest(self):
    expected_guest_policy = self._CreateGuestPolicyZypper(
        logging_version='latest',
        metrics_version='latest',
        logging_repo_suffix='-all',
        metrics_repo_suffix='-all',
        logging_package_suffix='',
        metrics_package_suffix='')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='latest')
    logging_agent_latest = _CreateLoggingAgentRule(
        agent_version='latest')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'sles', [logging_agent_latest, metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyRhel(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        logging_repo_suffix='-all',
        metrics_repo_suffix='-all')
    expected_guest_policy.assignment.osTypes[0].osShortName = 'rhel'
    expected_guest_policy.assignment.instances = [
        'zones/us-central1-a/instances/rhel7-0',
        'zones/us-central1-a/instances/rhel7-1',
    ]
    expected_guest_policy.assignment.osTypes[0].osVersion = '7.8'
    ops_agents_policy = _CreateOpsAgentPolicy(
        'rhel', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebian(self):
    expected_guest_policy = self._CreateGuestPolicyAPT()
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebian_UnifiedAgent(self):
    expected_guest_policy = self._LoadMessage(
        UNIFIED_AGENT_APT_GUEST_POLICY_YAML.format(
            ops_agent_enable_autoupgrade='true',
            ops_agent_package_state='installed',
            ops_agent_version='1.0.0',
            ops_agent_desired_state='UPDATED',
            ops_agent_repo_suffix='-all',
            etag=ETAG,
            ops_agent_run_script=OPS_AGENT_RULE_RUN_SCRIPT.format(
                repo_dir='/etc/apt/sources.list.d',
                repo_name='google-cloud-ops-agent',
                additional_install='',
                cache_dir='/var/cache/apt',
                package_name='google-cloud-ops-agent',
                package_manager='apt-get',
                package_suffix='=1.0.0-1*')),
        self.messages.GuestPolicy)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian', OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebianLegacy(self):
    expected_guest_policy = self._CreateGuestPolicyAPT(
        metrics_version='5.5.2-1000',
        metrics_enable_autoupgrade='false',
        metrics_desired_state='INSTALLED',
        metrics_package_suffix='=5.5.2-1000*')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='5.5.2-1000', enable_autoupgrade=False)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian',
        [_CreateLoggingAgentRule(), metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebianLatest(self):
    expected_guest_policy = self._CreateGuestPolicyAPT(
        logging_version='latest',
        metrics_version='latest',
        logging_package_suffix='',
        metrics_package_suffix='')
    metrics_agent_latest = _CreateMetricsAgentRule(
        agent_version='latest')
    logging_agent_latest = _CreateLoggingAgentRule(
        agent_version='latest')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian', [logging_agent_latest, metrics_agent_latest])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebianCurrentMajor(self):
    expected_guest_policy = self._CreateGuestPolicyAPT(
        logging_version='1.*.*',
        metrics_version='6.*.*',
        logging_repo_suffix='-1',
        metrics_repo_suffix='-6',
        logging_package_suffix='=1.*',
        metrics_package_suffix='=6.*')
    metrics_agent_current_major = _CreateMetricsAgentRule(
        agent_version='current-major')
    logging_agent_current_major = _CreateLoggingAgentRule(
        agent_version='')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian', [logging_agent_current_major, metrics_agent_current_major])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self.assertEqual(
        expected_guest_policy, actual_guest_policy,
        'Expected guest policy:\n{}\nActual guest policy:\n{}'.format(
            expected_guest_policy, actual_guest_policy))

  def testConvertOpsAgentPolicyToGuestPolicyCentosWildCard(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        logging_version='1.*.*',
        metrics_version='6.*.*',
        logging_repo_suffix='-1',
        metrics_repo_suffix='-6',
        logging_package_suffix='-1.*',
        metrics_package_suffix='-6.*')
    metrics_agent = _CreateMetricsAgentRule(
        agent_version='6.*.*')
    logging_agent = _CreateLoggingAgentRule(
        agent_version='1.*.*')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', [logging_agent, metrics_agent])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyDebianWildCard(self):
    expected_guest_policy = self._CreateGuestPolicyAPT(
        logging_version='1.*.*',
        metrics_version='6.*.*',
        logging_repo_suffix='-1',
        metrics_repo_suffix='-6',
        logging_package_suffix='=1.*',
        metrics_package_suffix='=6.*')
    metrics_agent = _CreateMetricsAgentRule(
        agent_version='6.*.*')
    logging_agent = _CreateLoggingAgentRule(
        agent_version='1.*.*')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'debian', [logging_agent, metrics_agent])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicySlesWildCard(self):
    expected_guest_policy = self._CreateGuestPolicyZypper(
        logging_version='1.*.*',
        metrics_version='6.*.*',
        logging_repo_suffix='-1',
        metrics_repo_suffix='-6',
        logging_package_suffix='<2.*',
        metrics_package_suffix='<7.*')
    metrics_agent = _CreateMetricsAgentRule(
        agent_version='6.*.*')
    logging_agent = _CreateLoggingAgentRule(
        agent_version='1.*.*')
    ops_agents_policy = _CreateOpsAgentPolicy(
        'sles', [logging_agent, metrics_agent])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyIntalled(self):
    expected_guest_policy = self._CreateGuestPolicyYUM(
        logging_enable_autoupgrade='false',
        metrics_enable_autoupgrade='false',
        logging_desired_state='INSTALLED',
        metrics_desired_state='INSTALLED')
    metrics_agent = _CreateMetricsAgentRule(
        agent_version='6.0.0', enable_autoupgrade=False)
    logging_agent = _CreateLoggingAgentRule(
        agent_version='1.6.35', enable_autoupgrade=False)
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', [logging_agent, metrics_agent])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicyRemoved(self):
    expected_guest_policy = self._LoadMessage(
        YUM_GUEST_POLICY_YAML.format(
            logging_enable_autoupgrade='false',
            logging_package_state='removed',
            logging_version='1.6.35',
            metrics_enable_autoupgrade='false',
            metrics_package_state='removed',
            metrics_version='6.0.0',
            logging_desired_state='REMOVED',
            metrics_desired_state='REMOVED',
            logging_repo_suffix='-all',
            metrics_repo_suffix='-all',
            etag=ETAG,
            logging_run_script=textwrap.dedent("""\
                #!/bin/bash
                        echo 'Skipping as the package state is [removed].'"""),
            metrics_run_script=textwrap.dedent("""\
                #!/bin/bash
                        echo 'Skipping as the package state is [removed].'""")),
        self.messages.GuestPolicy)
    metrics_agent = _CreateMetricsAgentRule(
        agent_version='6.0.0',
        enable_autoupgrade=False,
        package_state=agent_policy.OpsAgentPolicy.AgentRule.PackageState.REMOVED
    )
    logging_agent = _CreateLoggingAgentRule(
        agent_version='1.6.35',
        enable_autoupgrade=False,
        package_state=agent_policy.OpsAgentPolicy.AgentRule.PackageState.REMOVED
    )
    ops_agents_policy = _CreateOpsAgentPolicy('centos',
                                              [logging_agent, metrics_agent])
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy)
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicy_PreviousRecipe(self):
    expected_guest_policy = self._CreateGuestPolicyYUM()
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy, expected_guest_policy.recipes)
    for recipe in expected_guest_policy.recipes:
      recipe.version = '1'
      recipe.name = recipe.name.replace('0', '1')
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)

  def testConvertOpsAgentPolicyToGuestPolicy_AddNewRecipe(self):
    expected_guest_policy = self._CreateGuestPolicyYUM()
    ops_agents_policy = _CreateOpsAgentPolicy(
        'centos', LEGACY_OPS_AGENT_RULE_POLICY_AGENT_RULES)
    actual_guest_policy = converter.ConvertOpsAgentPolicyToGuestPolicy(
        self.messages, ops_agents_policy, [expected_guest_policy.recipes[0]])
    expected_guest_policy.recipes[0].version = '1'
    expected_guest_policy.recipes[0].name = expected_guest_policy.recipes[
        0].name.replace('0', '1')
    expected_guest_policy.recipes[1].version = '0'
    self._AssertProtoMessageEqual(expected_guest_policy, actual_guest_policy)


if __name__ == '__main__':
  test_case.main()
