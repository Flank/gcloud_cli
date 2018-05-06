# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for security policies."""

import contextlib
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils
from googlecloudsdk.core import yaml
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


def _UniqueName(name):
  return e2e_utils.GetResourceNameGenerator(
      prefix='compute-security-policy-test-' + name).next()


class SecurityPoliciesTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _SecurityPolicy(self, name):
    try:
      yield self.RunCompute('security-policies', 'create', name)
    finally:
      self.CleanUpResource('security-policies', name)

  def testSecurityPolicy(self):
    security_policy_name = _UniqueName('my-policy')

    with self._SecurityPolicy(security_policy_name):
      # Update the security policy
      self.result_file_path = os.path.join(self.temp_path, 'exported')
      self.Run('compute security-policies export {0}'
               ' --file-name {1} --file-format yaml'.format(
                   security_policy_name, self.result_file_path))
      security_policy = yaml.load_path(self.result_file_path)

      self.assertEqual('', security_policy['description'])
      self.assertEqual(1, len(security_policy['rules']))
      default_rule = security_policy['rules'][0]
      self.assertEqual('default rule', default_rule['description'])
      self.assertEqual(2147483647, default_rule['priority'])
      self.assertEqual('SRC_IPS_V1', default_rule['match']['versionedExpr'])
      self.assertEqual('*', default_rule['match']['config']['srcIpRanges'][0])
      self.assertEqual('allow', default_rule['action'])
      self.assertEqual(False, default_rule['preview'])

      security_policy['description'] = 'new description'
      security_policy['rules'] = []

      with open(self.result_file_path, 'w') as export_file:
        security_policies_utils.WriteToFile(export_file, security_policy,
                                            'json')

      self.Run('compute security-policies import {0}'
               ' --file-name {1} --file-format yaml'.format(
                   security_policy_name, self.result_file_path))
      self.Run('compute security-policies export {0}'
               ' --file-name {1} --file-format json'.format(
                   security_policy_name, self.result_file_path))
      security_policy = yaml.load_path(self.result_file_path)

      self.assertEqual('new description', security_policy['description'])
      self.assertEqual(1, len(security_policy['rules']))
      default_rule = security_policy['rules'][0]
      self.assertEqual('default rule', default_rule['description'])
      self.assertEqual(2147483647, default_rule['priority'])
      self.assertEqual('SRC_IPS_V1', default_rule['match']['versionedExpr'])
      self.assertEqual('*', default_rule['match']['config']['srcIpRanges'][0])
      self.assertEqual('allow', default_rule['action'])
      self.assertEqual(False, default_rule['preview'])


class SecurityPoliciesTestBeta(SecurityPoliciesTestAlpha):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

if __name__ == '__main__':
  e2e_test_base.main()
