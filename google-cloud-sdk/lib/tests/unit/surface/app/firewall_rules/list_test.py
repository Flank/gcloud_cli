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
from tests.lib.surface.app import firewall_rules_base


class FirewallListTest(firewall_rules_base.FirewallRulesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testListFirewallRules(self):
    rules = [
        self.MakeFirewallRule('1000', '192.0.2.1', 'descrip1', 'ALLOW'),
        self.MakeFirewallRule('2000', '192.0.2.2', 'descrip2', 'DENY')
    ]

    self.ExpectListFirewallRule(rules)
    self.Run('app firewall-rules list')
    self.AssertOutputEquals(
        """\
        PRIORITY ACTION SOURCE_RANGE DESCRIPTION
        1000     ALLOW  192.0.2.1    descrip1
        2000     DENY   192.0.2.2    descrip2
        """,
        normalize_space=True)


class FirewallListTestBeta(FirewallListTest):
  """Exercises the test against the Beta command track and API."""

  APPENGINE_API_VERSION = 'v1beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
