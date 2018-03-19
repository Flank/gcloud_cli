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
from tests.lib.surface.app import firewall_rules_base


class FirewallDescribeTest(firewall_rules_base.FirewallRulesBase):

  def ExpectGetFirewallRule(self, priority, source_range, description, action):
    """Adds expected firewall-rules describe request and response.

    Args:
      priority: str, the priority of the rule to expect.
      source_range: str, the ip address or range to expect for the rule.
      description: str, a textual description of the rule to expect.
      action: str, 'ALLOW' or 'DENY' action expected on rule.
    """
    request = self.messages.AppengineAppsFirewallIngressRulesGetRequest(
        name=self._FormatFirewallRule(priority))
    response = self.MakeFirewallRule(priority, source_range, description,
                                     action)
    self.mock_client.AppsFirewallIngressRulesService.Get.Expect(
        request, response=response)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribeFirewallRule(self):
    self.ExpectGetFirewallRule('1000', '192.0.2.1', 'descrip', 'allow')
    result = self.Run('app firewall-rules describe 1000 --format=disable')
    self.assertEquals('ALLOW', result.action.name)

  def testDescribeFirewallRule_defaultRule(self):
    self.ExpectGetFirewallRule('2147483647', '192.0.2.1', 'descrip', 'allow')
    result = self.Run('app firewall-rules describe default --format=disable')
    self.assertEquals('ALLOW', result.action.name)

  def testDescribeFirewallRule_priorityInvalidTooSmall(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('app firewall-rules describe 0 --format=disable')
    self.AssertErrContains('Invalid value for [priority]')

  def testDescribeFirewallRule_priorityInvalidTooLarge(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('app firewall-rules describe 5678912345 --format=disable')
    self.AssertErrContains('Invalid value for [priority]')

  def testDescribeFirewallRule_priorityInvalidNonInteger(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('app firewall-rules describe invalid --format=disable')
    self.AssertErrContains('Invalid value for [priority]')


class FirewallDescribeTestBeta(FirewallDescribeTest):
  """Exercises the test against the Beta command track and API."""

  APPENGINE_API_VERSION = 'v1beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
