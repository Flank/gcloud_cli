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
"""Tests for gcloud app firewall-rules."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib.surface.app import firewall_rules_base


class FirewallUpdateTest(firewall_rules_base.FirewallRulesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectUpdateFirewallRule(self, priority, source_range, description,
                               action, mask):
    """Adds expected firewall-rules update request and response.

    Args:
      priority: str, the priority of the rule to expect.
      source_range: str, the ip address or range to expect for the rule.
      description: str, a textual description of the rule to expect.
      action: str, 'ALLOW' or 'DENY' action expected on rule.
      mask: str, a comma separated list of included fields to expect.
    """
    rule = self.MakeFirewallRule(priority, source_range, description, action)
    request = self.messages.AppengineAppsFirewallIngressRulesPatchRequest(
        name=self._FormatFirewallRule(rule.priority),
        firewallRule=rule,
        updateMask=mask)
    self.mock_client.AppsFirewallIngressRulesService.Patch.Expect(
        request, response=rule)

  def testUpdateFirewallRule(self):
    self.ExpectUpdateFirewallRule('1000', '192.0.2.1', 'descrip', 'allow',
                                  'action,sourceRange,description')
    self.Run("""app firewall-rules update 1000
                --source-range=192.0.2.1
                --description=descrip
                --action=allow""")

  def testUpdateFirewallRule_defaultAction(self):
    self.ExpectUpdateFirewallRule('2147483647', None, None, 'allow', 'action')
    self.Run("""app firewall-rules update default --action=allow""")

  def testUpdateFirewallRule_invalidAction(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""app firewall-rules update 1000
                  --source-range=192.0.2.1
                  --description=descrip
                  --action=invalid""")
    self.AssertErrContains('--action: Invalid choice')

  def testUpdateFirewallRule_invalidPriority(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app firewall-rules update invalid
                  --source-range=192.0.2.1
                  --description=descrip
                  --action=allow""")
    self.AssertErrContains('Invalid value for [priority]')

  def testUpdateFirewallRule_noFields(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run("""app firewall-rules update 1000""")
    self.AssertErrContains('Please specify at least one attribute')

  def testUpdateDefaultRule(self):
    self.ExpectUpdateFirewallRule(2147483647, None, None, 'deny', 'action')
    self.Run("""app firewall-rules update default
                --action=deny""")


class FirewallUpdateTestBeta(FirewallUpdateTest):
  """Exercises the test against the Beta command track and API."""

  APPENGINE_API_VERSION = 'v1beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
