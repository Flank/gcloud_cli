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
"""Tests for the forwarding rules import subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import forwarding_rules_test_base
from tests.lib.surface.compute import test_resources


class ForwardingRulesImportTest(
    forwarding_rules_test_base.ForwardingRulesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.GA
    self._forwarding_rules = test_resources.GLOBAL_FORWARDING_RULES_V1

  def RunImport(self, command):
    self.Run('compute forwarding-rules import ' + command)

  def testImportFromFileGlobal(self):
    forwarding_rule_ref = self.GetForwardingRuleRef('fr-1')
    forwarding_rule = copy.deepcopy(self._forwarding_rules[0])

    # Write the modified forwarding_rule to a file.
    file_name = os.path.join(self.temp_path, 'temp-fw-rule.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=forwarding_rule, stream=stream)

    self.ExpectGetRequest(
        forwarding_rule_ref=forwarding_rule_ref,
        exception=http_error.MakeHttpError(code=404))
    self.ExpectInsertRequest(
        forwarding_rule_ref, forwarding_rule=forwarding_rule)

    self.RunImport('fr-1 --source {0} --global'.format(file_name))

  def testImportFromStdInRegion(self):
    forwarding_rule_ref = self.GetForwardingRuleRef('fr-1', region='alaska')
    forwarding_rule = copy.deepcopy(self._forwarding_rules[0])

    self.WriteInput(export_util.Export(forwarding_rule))

    self.ExpectGetRequest(forwarding_rule_ref=forwarding_rule_ref,
                          exception=http_error.MakeHttpError(code=404))
    self.ExpectInsertRequest(forwarding_rule_ref,
                             forwarding_rule=forwarding_rule)

    self.RunImport('fr-1 --region alaska')

  def testImportForwardingRuleInvalidSchema(self):
    # This test ensures that the schema files do not contain invalid fields.
    forwarding_rule = copy.deepcopy(self._forwarding_rules[0])

    # id and fingerprint fields should be removed from schema files manually.
    forwarding_rule.id = 12345

    # Write the modified forwarding_rule to a file.
    file_name = os.path.join(self.temp_path, 'temp-fw-rule.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=forwarding_rule, stream=stream)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'Additional properties are not allowed '
        "('id' was unexpected)"):
      self.RunImport('fr-1 --source {0} --global'.format(file_name))


class ForwardingRulesImportTestBeta(ForwardingRulesImportTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA
    self._forwarding_rules = test_resources.GLOBAL_FORWARDING_RULES_BETA

  def testImportExistingFromFileGlobal(self):
    # Patch is only available for Beta
    forwarding_rule_ref = self.GetForwardingRuleRef('fr-1')
    forwarding_rule = copy.deepcopy(self._forwarding_rules[0])

    forwarding_rule.description = 'changed'

    # Write the modified forwarding_rule to a file.
    file_name = os.path.join(self.temp_path, 'temp-fw-rule.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=forwarding_rule, stream=stream)

    self.ExpectGetRequest(
        forwarding_rule_ref=forwarding_rule_ref,
        forwarding_rule=self._forwarding_rules[0])
    self.ExpectPatchRequest(
        forwarding_rule_ref, forwarding_rule=forwarding_rule)

    self.WriteInput('y\n')

    self.RunImport('fr-1 --source {0} --global'.format(file_name))


class ForwardingRulesImportTestAlpha(ForwardingRulesImportTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._forwarding_rules = test_resources.GLOBAL_FORWARDING_RULES_ALPHA


if __name__ == '__main__':
  test_case.main()
