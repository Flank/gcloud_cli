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
"""Integration tests for forwarding rules."""

from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_resource_managers
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import resource_managers


class SecurityPolicyRulesTestBeta(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')

    # A new prefix added here should also be added to resources.yaml
    self.security_policy_prefix = 'compute-security-policy-rule-test'

  def _GetSecurityPolicyRef(self, prefix):
    return self.resources.Create(
        'compute.securityPolicies',
        securityPolicy=prefix,
        project=self.Project())

  def _GetSecurityPolicyParameters(self):
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetSecurityPolicyRef(self.security_policy_prefix))

  def testAddRule(self):
    with resource_managers.SecurityPolicy(self.Run,
                                          self._GetSecurityPolicyParameters(),
                                          self.resources) as security_policy:
      # Verify that security policy is successfully created
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]
      self.assertEqual(security_policy.ref.Name(), sp.name)

      # Verify we can add a rule to the security policy
      self.Run('compute security-policies rules create 1000 '
               '--security-policy {0} '
               '--description my-rule '
               '--src-ip-ranges 1.1.1.1 '
               '--action deny-404 '
               '--preview'.format(security_policy.ref.Name()))
      rule = self.Run(
          'compute security-policies rules describe 1000 --security-policy {0}'.
          format(security_policy.ref.Name()))[0]

      self.assertEqual('my-rule', rule.description)
      self.assertEqual('SRC_IPS_V1', str(rule.match.versionedExpr))
      self.assertEqual(['1.1.1.1'], rule.match.config.srcIpRanges)
      self.assertEqual('deny(404)', rule.action)
      self.assertTrue(rule.preview)

  def testUpdateRule(self):
    with resource_managers.SecurityPolicy(self.Run,
                                          self._GetSecurityPolicyParameters(),
                                          self.resources) as security_policy:
      # Verify that security policy is successfully created
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]
      self.assertEqual(security_policy.ref.Name(), sp.name)

      # Add a rule to the security policy
      self.Run('compute security-policies rules create 1000 '
               '--security-policy {0} '
               '--description my-rule '
               '--src-ip-ranges 1.1.1.1 '
               '--action deny-404 '
               '--preview'.format(security_policy.ref.Name()))

      # Verify we can update a rule in the security policy
      self.Run('compute security-policies rules update 1000 '
               '--security-policy {0} '
               '--description new-description '
               '--src-ip-ranges 1.2.3.4 '
               '--action deny-502 '
               '--no-preview'.format(security_policy.ref.Name()))
      rule = self.Run(
          'compute security-policies rules describe 1000 --security-policy {0}'.
          format(security_policy.ref.Name()))[0]

      self.assertEqual('new-description', rule.description)
      self.assertEqual('SRC_IPS_V1', str(rule.match.versionedExpr))
      self.assertEqual(['1.2.3.4'], rule.match.config.srcIpRanges)
      self.assertEqual('deny(502)', rule.action)
      self.assertFalse(rule.preview)

  def testUpdateRulePartial(self):
    with resource_managers.SecurityPolicy(self.Run,
                                          self._GetSecurityPolicyParameters(),
                                          self.resources) as security_policy:
      # Verify that security policy is successfully created
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]
      self.assertEqual(security_policy.ref.Name(), sp.name)

      # Add a rule to the security policy
      self.Run('compute security-policies rules create 1000 '
               '--security-policy {0} '
               '--description my-rule '
               '--src-ip-ranges 1.1.1.1 '
               '--action deny-404 '
               '--preview'.format(security_policy.ref.Name()))

      # Verify that fields that are not specified are not updated
      self.Run('compute security-policies rules update 1000 '
               '--security-policy {0} '
               '--action allow '.format(security_policy.ref.Name()))
      rule = self.Run(
          'compute security-policies rules describe 1000 --security-policy {0}'.
          format(security_policy.ref.Name()))[0]

      self.assertEqual('my-rule', rule.description)
      self.assertEqual('SRC_IPS_V1', str(rule.match.versionedExpr))
      self.assertEqual(['1.1.1.1'], rule.match.config.srcIpRanges)
      self.assertEqual('allow', rule.action)
      self.assertTrue(rule.preview)

  def testDeleteRule(self):
    with resource_managers.SecurityPolicy(self.Run,
                                          self._GetSecurityPolicyParameters(),
                                          self.resources) as security_policy:
      # Verify that security policy is successfully created
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]
      self.assertEqual(security_policy.ref.Name(), sp.name)

      # Add a rule to the security policy
      self.Run('compute security-policies rules create 1000 '
               '--security-policy {0} '
               '--description my-rule '
               '--src-ip-ranges 1.1.1.1 '
               '--action deny-404 '
               '--preview'.format(security_policy.ref.Name()))

      # Verify that the rule count count is now 2 (new + default rule)
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]
      self.assertEqual(2, len(sp.rules))

      # Verify that we can delete a rule from the security policy
      self.Run(
          'compute security-policies rules delete 1000 --security-policy {0}'.
          format(security_policy.ref.Name()))
      sp = self.Run('compute security-policies describe {0}'.format(
          security_policy.ref.Name()))[0]

      self.assertEqual(1, len(sp.rules))


class SecurityPolicyRulesTestAlpha(SecurityPolicyRulesTestBeta):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

    # A new prefix added here should also be added to resources.yaml
    self.security_policy_prefix = 'compute-security-policy-rule-test'


if __name__ == '__main__':
  e2e_test_base.main()
