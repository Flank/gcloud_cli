# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the forwarding-rules export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import forwarding_rules_test_base
from tests.lib.surface.compute import test_resources


class ForwardingRulesExportTestBeta(
    forwarding_rules_test_base.ForwardingRulesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA
    self._api = 'beta'
    self._forwarding_rules = test_resources.GLOBAL_FORWARDING_RULES_BETA

  def RunExport(self, command):
    self.Run('compute forwarding-rules export ' + command)

  def testExportToStdOut(self):
    forwarding_rule_ref = self.GetForwardingRuleRef('global-forwarding-rule-1')
    self.ExpectGetRequest(forwarding_rule_ref=forwarding_rule_ref,
                          forwarding_rule=self._forwarding_rules[0])

    self.RunExport('global-forwarding-rule-1 --global')

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPAddress: 162.222.178.85
            IPProtocol: TCP
            name: global-forwarding-rule-1
            portRange: 1-65535
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/forwardingRules/global-forwarding-rule-1
            target: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/targetHttpProxies/proxy-1
            """ % {'api': self._api}))

  def testExportToFile(self):
    forwarding_rule_ref = self.GetForwardingRuleRef('global-forwarding-rule-1',
                                                    region='alaska')
    self.ExpectGetRequest(forwarding_rule_ref=forwarding_rule_ref,
                          forwarding_rule=self._forwarding_rules[0])

    file_name = os.path.join(self.temp_path, 'export.yaml')

    self.RunExport('global-forwarding-rule-1 --region alaska'
                   ' --destination {0}'.format(file_name))

    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_forwarding_rule = export_util.Import(
        message_type=self.messages.ForwardingRule, stream=data)
    self.AssertMessagesEqual(self._forwarding_rules[0],
                             exported_forwarding_rule)


class ForwardingRulesExportTestAlpha(ForwardingRulesExportTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._api = 'alpha'
    self._forwarding_rules = test_resources.GLOBAL_FORWARDING_RULES_ALPHA


if __name__ == '__main__':
  test_case.main()
