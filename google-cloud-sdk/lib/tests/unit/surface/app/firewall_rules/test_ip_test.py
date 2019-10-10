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
from tests.lib.surface.app import firewall_rules_base


class FirewallTestIpTest(firewall_rules_base.FirewallRulesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testTestIpFirewallRules(self):
    rules = [self.MakeFirewallRule('1000', '192.0.2.1', 'descrip', 'allow')]

    self.ExpectListFirewallRule(rules, '192.0.2.1')
    self.Run('app firewall-rules test-ip 192.0.2.1')
    self.AssertErrEquals(
        """\
        The action `ALLOW` will apply to the IP address.

        Matching Rules
        """, normalize_space=True)
    self.AssertOutputEquals(
        """\
        PRIORITY ACTION SOURCE_RANGE DESCRIPTION
        1000     ALLOW  192.0.2.1    descrip
        """,
        normalize_space=True)

  def testTestIpFirewallRules_noMatches(self):
    rules = []
    self.ExpectListFirewallRule(rules, '192.0.2.1')
    self.Run('app firewall-rules test-ip 192.0.2.1')
    self.AssertErrEquals(
        """\
        No rules match the IP address.
        """, normalize_space=True)


class FirewallTestIpTestBeta(FirewallTestIpTest):
  """Exercises the test against the Beta command track and API."""

  APPENGINE_API_VERSION = 'v1beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
