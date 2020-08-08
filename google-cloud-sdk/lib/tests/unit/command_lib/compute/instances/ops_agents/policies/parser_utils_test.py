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
"""Unit Tests for ops_agents.parsers.arg_parsers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.instances.ops_agents.policies import parser_utils
from tests.lib import subtests


class ArgEnumAgainstAgentTypeTest(subtests.Base):

  def RunSubTest(self, value, **kwargs):
    return parser_utils.ArgEnum(
        field_name='type',
        allowed_values=[
            agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING,
            agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS
        ],
        **kwargs)(
            value)

  def testParser(self):
    for arg_value in {'logging', 'metrics'}:
      self.Run(arg_value, arg_value)

  def testParserException(self):
    for arg_value in {'', '123', '21,2', 'trace', '^F&^%'}:
      self.Run(
          None,
          arg_value,
          exception=arg_parsers.ArgumentTypeError((
              'Invalid value [{}] from field [type], expected one of '
              '[logging, metrics].'
          ).format(arg_value)))


class ArgEnumAgainstAgentPackageStateTest(subtests.Base):

  def RunSubTest(self, value, **kwargs):
    return parser_utils.ArgEnum(
        field_name='package-state',
        allowed_values=[
            agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED,
            agent_policy.OpsAgentPolicy.AgentRule.PackageState.REMOVED
        ],
        **kwargs)(
            value)

  def testParser(self):
    for arg_value in {'installed', 'removed'}:
      self.Run(arg_value, arg_value)

  def testParserException(self):
    for arg_value in {'', '123', '21,2', 'uninstalled', 'purged', '^F&^%'}:
      self.Run(
          None,
          arg_value,
          exception=arg_parsers.ArgumentTypeError((
              'Invalid value [{}] from field [package-state], expected one of '
              '[installed, removed].'
          ).format(arg_value)))
