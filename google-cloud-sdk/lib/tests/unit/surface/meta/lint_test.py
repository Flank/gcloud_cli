# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for gcloud internal list-commands."""

import collections
import os

from googlecloudsdk.calliope import cli as calliope
from surface.meta import lint
from tests.lib import cli_test_base


class LintTest(cli_test_base.CliTestBase):

  def GetCLI(self, name):
    loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=os.path.join(os.path.dirname(__file__), name))
    return loader.Generate()

  @staticmethod
  def _BuildIssueMap(issues):
    issue_map = collections.defaultdict(list)
    for issue in issues:
      issue_map[issue.name].append(issue)
    return issue_map

  def LoadGroupTree(self, name):
    root_group = self.GetCLI(name)._TopElement()
    root_group.LoadAllSubElements(recursive=True)
    return root_group

  def testLinterClean(self):
    linter = lint.Linter()
    linter.AddCheck(lint.NameChecker)
    issues = linter.Run(self.LoadGroupTree('testdata/lint/sdk1'))
    self.assertFalse(issues)

  def testLinterFailsFlagUnderscoreCheck(self):
    linter = lint.Linter()
    linter.AddCheck(lint.NameChecker)
    issues = self._BuildIssueMap(
        linter.Run(self.LoadGroupTree('testdata/lint/sdk2')))

    self.assertEqual(1, len(issues))
    self.assertIn('NameCheck', issues)
    self.assertEqual(4, len(issues['NameCheck']))

  def testLinterFailsFlagUnderscoreCheckViaArgs(self):
    issues = self._BuildIssueMap(lint.Lint._SetupAndRun(
        self.LoadGroupTree('testdata/lint/sdk2'), ['NameCheck']))
    self.assertEqual(1, len(issues))
    self.assertIn('NameCheck', issues)
    self.assertEqual(
        set(['[gcloud.internal.xyzzy]: flag [--input_param] has underscores',
             '[gcloud]: flag [--sdk_root_override] has underscores',
             '[gcloud]: flag [-i] has no long form',
             '[gcloud]: long flag [--camelCase] has upper case characters']),
        set(issue.msg for issue in issues['NameCheck']))

  def testLinterFailsFlagListCheckViaArgs(self):
    issues = lint.Lint._SetupAndRun(
        self.LoadGroupTree('testdata/lint/sdk2'), ['BadLists'])
    expected = """\
BadLists: [gcloud.internal.xyzzy]: dict flag [--mediocre-dict] has no metavar and type.spec (at least one needed)
BadLists: [gcloud.internal.xyzzy]: flag [--bad-list] has nargs='*'
BadLists: [gcloud.internal.xyzzy]: list flag [--mediocre-list] has no metavar
BadLists: [gcloud]: flag [--user-output-enabled] has nargs='?'
"""
    msgs = []
    for issue in issues:
      msgs.append('%s: %s' % (issue.name, issue.msg))
    actual = '\n'.join(sorted(msgs)) + '\n'
    self.maxDiff = None
    self.assertMultiLineEqual(expected, actual)
    self.assertEqual(4, len(issues))

  def testLinterWhitelistedCommands(self):
    mock = self.StartObjectPatch(lint, '_GetWhitelistedCommandVocabulary')
    mock.return_value = set(['second-level-command-1',
                             'subgroup-command-a',
                             'second-level-command-b',
                             'subgroup-command-2'])
    issues = lint.Lint._SetupAndRun(
        self.LoadGroupTree('testdata/lint/sdk2'), ['WhitelistedNameCheck'])
    self.assertEqual(
        set(['[gcloud.internal.xyzzy]: command name [xyzzy] '
             'is not whitelisted']),
        set(issue.msg for issue in issues))

  def testUnknownCheck(self):
    with self.assertRaises(lint.UnknownCheckException):
      lint.Lint._SetupAndRun(
          self.LoadGroupTree('testdata/lint/sdk2'), ['UnknownChecker'])


if __name__ == '__main__':
  cli_test_base.main()
