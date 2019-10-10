# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.app import firewall_rules_base


class FirewallDeleteTest(firewall_rules_base.FirewallRulesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectDeleteFirewallRule(self, priority):
    """Adds expected firewall-rules delete request and response.

    Args:
     priority: str, the priority of the rule to expect.
    """
    request = self.messages.AppengineAppsFirewallIngressRulesDeleteRequest(
        name=self._FormatFirewallRule(priority))
    response = self.messages.Empty()
    self.mock_client.AppsFirewallIngressRulesService.Delete.Expect(
        request, response=response)

  def testDeleteFirewallRule(self):
    self.ExpectDeleteFirewallRule('1000')
    self.Run('app firewall-rules delete 1000')

    self.AssertErrEquals(
        '{"ux": "PROMPT_CONTINUE", "prompt_string": "You are about to delete '
        'rule [1000]."}\n'
        'Deleted [1000].\n')

  def testCreateFirewallRule_defaultRuleFails(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app firewall-rules delete default""")
    self.AssertErrContains('Invalid value for [priority]')


class FirewallDeleteTestBeta(FirewallDeleteTest):
  """Exercises the test against the Beta command track and API."""

  APPENGINE_API_VERSION = 'v1beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
