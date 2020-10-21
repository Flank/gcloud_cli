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
"""Unit Tests for ops_agents.validators.ops_agents_policy_common_validator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.compute.instances.ops_agents import exceptions
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import ops_agents_policy_validator as validator
from tests.lib import subtests

GOOD_DESCRIPTION = 'testing policy'
GOOD_LOGGING_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING, '1.*.*',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
GOOD_METRICS_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, 'latest',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, False)
GOOD_OPS_AGENT_RULE = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.OPS_AGENT, '1.*.*',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True)
GOOD_OS_TYPE = agent_policy.OpsAgentPolicy.Assignment.OsType(
    agent_policy.OpsAgentPolicy.Assignment.OsType.OsShortName.CENTOS, '8')
GOOD_ASSIGNMENT = agent_policy.OpsAgentPolicy.Assignment(
    group_labels=[],
    zones=[],
    instances=[],
    os_types=[GOOD_OS_TYPE])
GOOD_POLICY = agent_policy.OpsAgentPolicy(
    assignment=GOOD_ASSIGNMENT,
    agent_rules=[GOOD_LOGGING_AGENT_RULE, GOOD_METRICS_AGENT_RULE],
    description=GOOD_DESCRIPTION,
    etag=None,
    name=None,
    update_time=None,
    create_time=None)

BAD_LOGGING_AGENT_RULE_INVALID_VERSION = agent_policy.OpsAgentPolicy.AgentRule(
    agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING, '1',
    agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, False)
BAD_METRICS_AGENT_RULE_VERSION_AUTOUPGRADE_CONFLICT = (
    agent_policy.OpsAgentPolicy.AgentRule(
        agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS, '5.3.1',
        agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED, True))
BAD_OS_TYPE_INVALID_VERSION = agent_policy.OpsAgentPolicy.Assignment.OsType(
    agent_policy.OpsAgentPolicy.Assignment.OsType.OsShortName.CENTOS, '6')


def _WrapOneError(error):
  return exceptions.PolicyValidationMultiError([error])


class _ValidateAgentTypesUniquenessTest(subtests.Base):

  def RunSubTest(self, agent_rules, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = agent_rules
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for agent_rules in [
        [GOOD_LOGGING_AGENT_RULE],
        [GOOD_METRICS_AGENT_RULE],
        [GOOD_LOGGING_AGENT_RULE, GOOD_METRICS_AGENT_RULE],
    ]:
      self.Run(None, agent_rules)

  def testInvalid(self):
    for duplicate_type, agent_rules in [
        ('logging', [GOOD_LOGGING_AGENT_RULE, GOOD_LOGGING_AGENT_RULE]),
        ('metrics', [GOOD_METRICS_AGENT_RULE, GOOD_METRICS_AGENT_RULE]),
        ('logging',
         [GOOD_METRICS_AGENT_RULE, GOOD_LOGGING_AGENT_RULE,
          GOOD_LOGGING_AGENT_RULE]),
    ]:
      self.Run(
          None, agent_rules, exception=_WrapOneError(
              validator.AgentTypesUniquenessError(duplicate_type)))


class _ValidateAgentTypesConflict(subtests.Base):

  def RunSubTest(self, agent_rules, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = agent_rules
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for agent_rules in [
        [GOOD_LOGGING_AGENT_RULE],
        [GOOD_METRICS_AGENT_RULE],
        [GOOD_OPS_AGENT_RULE],
        [GOOD_LOGGING_AGENT_RULE, GOOD_METRICS_AGENT_RULE],
    ]:
      self.Run(None, agent_rules)

  def testInvalid(self):
    for agent_rules in [[GOOD_OPS_AGENT_RULE, GOOD_LOGGING_AGENT_RULE],
                        [GOOD_OPS_AGENT_RULE, GOOD_METRICS_AGENT_RULE],]:
      self.Run(
          None,
          agent_rules,
          exception=_WrapOneError(validator.AgentTypesConflictError()))


class _ValidateAgentTest(subtests.Base):

  def RunSubTest(self, agent_rule, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = [agent_rule]
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for agent_rule in [
        GOOD_LOGGING_AGENT_RULE,
        GOOD_METRICS_AGENT_RULE,
    ]:
      self.Run(None, agent_rule)

  def testInvalid(self):
    for agent_rule, exception in [
        (BAD_LOGGING_AGENT_RULE_INVALID_VERSION,
         validator.AgentVersionInvalidFormatError('1')),
        (BAD_METRICS_AGENT_RULE_VERSION_AUTOUPGRADE_CONFLICT,
         validator.AgentVersionAndEnableAutoupgradeConflictError('5.3.1'))
    ]:
      self.Run(None, agent_rule, exception=_WrapOneError(exception))


class _ValidateAgentVersionTest(subtests.Base):

  def RunSubTest(self, agent_type, version, **kwargs):
    agent_rule = copy.deepcopy(GOOD_LOGGING_AGENT_RULE)
    agent_rule.version = version
    agent_rule.type = agent_type
    agent_rule.enable_autoupgrade = False
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = [agent_rule]
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    logging = agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING
    metrics = agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS
    latest = agent_policy.OpsAgentPolicy.AgentRule.Version.LATEST_OF_ALL
    major = agent_policy.OpsAgentPolicy.AgentRule.Version.CURRENT_MAJOR
    valid_versions = {
        logging: {'1.2.33', '1.*.*', '1.9999.0000', latest, major},
        metrics: {'6.0.3', '5.*.*', '6.*.*', '6.9999.0000',
                  '5.5.2-1000', latest, major},
    }
    for agent_type, versions in valid_versions.items():
      for version in versions:
        self.Run(None, agent_type, version)

  def testSyntaxInvalid(self):
    logging = agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING
    for version in {
        '',
        '1.2',
        '6.0.',
        '9999.0000',
        '*.5.*',
        '6.*',
        '.*.*',
        '7.*.9',
        'lates',
        '1379',
        '*&#Y57',
    }:
      self.Run(
          None, logging, version, exception=_WrapOneError(
              validator.AgentVersionInvalidFormatError(version)))

  def testMajorVersionInvalid(self):
    logging = agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING
    metrics = agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS
    invalid_versions = {
        logging: {'9999.1.2', '9999.*.*', '6.0.1', '6.*.*'},
        metrics: {'9999.1.2', '9999.*.*', '1.1.2', '1.*.*'},
    }
    for agent_type, versions in invalid_versions.items():
      for version in versions:
        self.Run(None, agent_type, version, exception=_WrapOneError(
            validator.AgentUnsupportedMajorVersionError(agent_type, version)))


class _ValidateAgentVersionAndEnableAutoupgradeTest(subtests.Base):

  def RunSubTest(self, version, enable_autoupgrade, **kwargs):
    agent_rule = copy.deepcopy(GOOD_METRICS_AGENT_RULE)
    agent_rule.version = version
    agent_rule.enable_autoupgrade = enable_autoupgrade
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = [agent_rule]
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for version, enable_autoupgrade in {
        ('6.0.3', False),
        ('6.*.*', False),
        (agent_policy.OpsAgentPolicy.AgentRule.Version.CURRENT_MAJOR, False),
        (agent_policy.OpsAgentPolicy.AgentRule.Version.LATEST_OF_ALL, False),
        (agent_policy.OpsAgentPolicy.AgentRule.Version.CURRENT_MAJOR, True),
        (agent_policy.OpsAgentPolicy.AgentRule.Version.LATEST_OF_ALL, True),
    }:
      self.Run(None, version, enable_autoupgrade)

  def testInvalid(self):
    for version, enable_autoupgrade in {
        ('6.0.3', True),
        ('6.9999.999', True),
    }:
      self.Run(
          None,
          version,
          enable_autoupgrade,
          exception=_WrapOneError(
              validator.AgentVersionAndEnableAutoupgradeConflictError(
                  version)))


class _ValidateOnlyOneOsTypeAllowedTest(subtests.Base):

  def RunSubTest(self, os_types, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    policy.assignment.os_types = os_types
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for os_types in [
        [GOOD_OS_TYPE],
    ]:
      self.Run(None, os_types)

  def testInvalid(self):
    for os_types in [
        [GOOD_OS_TYPE, GOOD_OS_TYPE],
    ]:
      self.Run(None, os_types, exception=_WrapOneError(
          validator.OsTypesMoreThanOneError()))


class _ValidateSupportedOsType(subtests.Base):

  def RunSubTest(self, short_name, version, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    os_type = agent_policy.OpsAgentPolicy.Assignment.OsType(
        agent_policy.OpsAgentPolicy.Assignment.OsType.OsShortName(short_name),
        version)
    policy.assignment.os_types = [os_type]
    return validator.ValidateOpsAgentsPolicy(policy)

  def testValid(self):
    for short_name, version in [
        # CentOS.
        ('centos', '7'),
        ('centos', '7.8'),
        ('centos', '7*'),
        ('centos', '7.*'),
        ('centos', '8'),
        ('centos', '8.3'),
        ('centos', '8*'),
        ('centos', '8.*'),
        # Debian.
        ('debian', '9'),
        ('debian', '9.8'),
        ('debian', '9*'),
        ('debian', '9.*'),
        ('debian', '10'),
        ('debian', '10.3'),
        ('debian', '10*'),
        ('debian', '10.*'),
        # Rhel.
        ('rhel', '7'),
        ('rhel', '7.8'),
        ('rhel', '7*'),
        ('rhel', '7.*'),
        ('rhel', '8'),
        ('rhel', '8.3'),
        ('rhel', '8*'),
        ('rhel', '8.*'),
        # Sles.
        ('sles', '12'),
        ('sles', '12.8'),
        ('sles', '12*'),
        ('sles', '12.*'),
        ('sles', '15'),
        ('sles', '15.3'),
        ('sles', '15*'),
        ('sles', '15.*'),
        # Sles SAP.
        ('sles-sap', '12'),
        ('sles-sap', '12.8'),
        ('sles-sap', '12*'),
        ('sles-sap', '12.*'),
        ('sles-sap', '15'),
        ('sles-sap', '15.3'),
        ('sles-sap', '15*'),
        ('sles-sap', '15.*'),
        # Ubuntu.
        ('ubuntu', '16.04'),
        ('ubuntu', '18.04'),
        ('ubuntu', '19.10'),
        ('ubuntu', '20.04'),
    ]:
      self.Run(None, short_name, version)

  def testInvalid(self):
    for short_name, version in [
        # CentOS.
        ('centos', '5'),
        ('centos', '5*'),
        ('centos', '6'),
        ('centos', '6.8'),
        ('centos', 'some'),
        ('centos', '*&@#^%#$'),
        # Debian.
        ('debian', '7'),
        ('debian', '7*'),
        ('debian', '8'),
        ('debian', '8.8'),
        # Rhel.
        ('rhel', '5'),
        ('rhel', '6.8'),
        # Sles.
        ('sles', '11'),
        ('sles', '11.8'),
        ('sles', '11*'),
        # Sles SAP.
        ('sles-sap', '11'),
        ('sles-sap', '11.8'),
        ('sles-sap', '11*'),
        # Ubuntu.
        ('ubuntu', '12.04'),
        ('ubuntu', '14.04'),
        ('ubuntu', '18.10'),
        ('ubuntu', '19.04'),
    ]:
      self.Run(
          None, short_name, version,
          exception=_WrapOneError(
              validator.OsTypeNotSupportedError(short_name, version)))


class ValidateOpsAgentsPolicyTest(subtests.Base):

  def RunSubTest(self, agent_rules, os_types, **kwargs):
    policy = copy.deepcopy(GOOD_POLICY)
    policy.agent_rules = agent_rules
    policy.assignment.os_types = os_types
    return validator.ValidateOpsAgentsPolicy(policy)

  def testMultiErrors(self):
    agent_rules = [
        GOOD_LOGGING_AGENT_RULE,
        BAD_LOGGING_AGENT_RULE_INVALID_VERSION,
        GOOD_METRICS_AGENT_RULE,
        BAD_METRICS_AGENT_RULE_VERSION_AUTOUPGRADE_CONFLICT,
    ]
    os_types = [
        GOOD_OS_TYPE,
        BAD_OS_TYPE_INVALID_VERSION,
    ]
    exception = exceptions.PolicyValidationMultiError([
        validator.AgentTypesUniquenessError('logging'),
        validator.AgentTypesUniquenessError('metrics'),
        validator.AgentVersionInvalidFormatError('1'),
        validator.AgentVersionAndEnableAutoupgradeConflictError('5.3.1'),
        validator.OsTypesMoreThanOneError(),
        validator.OsTypeNotSupportedError('centos', '6'),
    ])
    self.Run(None, agent_rules, os_types, exception=exception)
