# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.command_lib.help_search import search
from googlecloudsdk.command_lib.static_completion import lookup as find
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


import mock


class HelpTest(cli_test_base.CliTestBase):

  def testHelpGroupHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('-h')
    self.AssertOutputContains('Usage: gcloud [optional flags]')

  def testHelpCommandHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info -h')
    self.AssertOutputContains('Usage: gcloud info [optional flags]')

  def testHelpGroupHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('--help')
    self.AssertOutputContains('gcloud - manage Google Cloud Platform resources '
                              'and developer workflow')

  def testHelpCommandHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info --help')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')

  def testHelpBadCommandUnknownHFlag(self):
    self.StartObjectPatch(find, 'LoadCompletionCliTree',
                          return_value={})
    with self.AssertRaisesArgumentErrorRegexp(
        r"Invalid choice: 'junk'."):
      self.Run('junk -h')

  def testHelpBadSecondCommandUnknownHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info junk -h')
    self.AssertOutputContains('Usage: gcloud info [optional flags]')

  def testHelpBadCommandUnknownHelpFlag(self):
    self.StartObjectPatch(find, 'LoadCompletionCliTree',
                          return_value={})
    with self.AssertRaisesArgumentErrorRegexp(
        r"Invalid choice: 'junk'."):
      self.Run('junk --help')

  def testHelpBadSecondCommandUnknownHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info junk --help')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')


class HelpCommandTest(cli_test_base.CliTestBase):
  """Test `gcloud help` command functionality."""

  def testHelpGroupHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help')
    self.AssertOutputContains('gcloud - manage Google Cloud Platform resources '
                              'and developer workflow')

  def testHelpCommandHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help info')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')

  def testHelpBadSecondCommandUnknownHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help info junk')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')


class HelpSearchTest(cli_test_base.CliTestBase):
  """Test `gcloud help -- ...` runs search properly."""

  def SetUp(self):
    self.mock_commands = [
        {lookup.NAME: 'command',
         lookup.PATH: ['gcloud', 'example'],
         lookup.RELEVANCE: 0.25,
         lookup.RELEASE: lookup.GA,
         lookup.CAPSULE: 'capsule',
         lookup.DESCRIPTION: 'foo description',
         lookup.RESULTS: {'foo': lookup.DESCRIPTION}}]
    self.mock_search = self.StartObjectPatch(
        search, 'RunSearch', return_value=self.mock_commands)

  def testHelpNotACommand(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('help junk')
    self.mock_search.assert_called_once_with(
        ['junk'],
        mock.ANY)
    self.assertEqual(self.mock_commands, list(results))

  def testHelpRemainderArgs(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('help -- junk')
    self.mock_search.assert_called_once_with(
        ['junk'],
        mock.ANY)
    self.assertEqual(self.mock_commands, list(results))

  def testHelpNotACommandWithRemainderArgs(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('help junk -- term --search-flag')
    self.mock_search.assert_called_once_with(
        ['junk', 'term', '--search-flag'],
        mock.ANY)
    self.assertEqual(self.mock_commands, list(results))

  def testHelpExistingCommandWithRemainderArgs(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('help info -- term')
    self.mock_search.assert_called_once_with(
        ['info', 'term'],
        mock.ANY)
    self.assertEqual(self.mock_commands, list(results))


class HelpSearchCommandTest(calliope_test_base.CalliopeTestBase):
  """Test gcloud help with a test CLI."""

  def SetUp(self):
    self.table_dir_path = self.CreateTempDir('help_text')
    self.StartObjectPatch(
        cli_tree, 'CliTreeDir', return_value=self.table_dir_path)
    # Mock the console width.
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize', return_value=(80, 100))
    self.SetEncoding('ascii')

    self.table_file_path = cli_tree.CliTreePath()

    # Load the mock CLI and write the help table.
    self.test_cli = self.LoadTestCli('sdk8')
    self.parent = cli_tree.Load(cli=self.test_cli)

    self.sdk = self.parent.get(lookup.COMMANDS, {}).get('sdk', {})
    self.long_help = self.sdk.get(lookup.COMMANDS, {}).get('long-help', {})
    self.xyzzy = self.sdk.get(lookup.COMMANDS, {}).get('xyzzy', {})

  def testResults_OneTermNotFound(self):
    """Test running help search returns empty list if no results match."""
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('help -- chandler')
    self.assertEqual([], list(results))

  def testResults(self):
    """Test that results return as expected."""
    properties.VALUES.core.user_output_enabled.Set(False)
    expected_result = copy.deepcopy(self.long_help)
    expected_result.update(
        {lookup.COMMANDS: [],
         lookup.RESULTS: {'mittens': 'sections.DESCRIPTION'},
         lookup.RELEVANCE: 0.25})
    actual = self.Run('help -- mittens')
    self.assertIn(expected_result, actual)
    self.assertEqual(1, len(actual))

  def testOutput_MatchesDescription(self):
    """Test the command output when the description matches the term."""
    self.Run('help -- mittens')
    self.AssertOutputEquals("""\
+----------------------+-------------------------------------------------------+
|       COMMAND        |                        SUMMARY                        |
+----------------------+-------------------------------------------------------+
| gcloud sdk long-help | A test command with a long help section.              |
|                      | DESCRIPTION                                           |
|                      | ...aren't so close to the other terms in the next     |
|                      | paragraph. On the other hand if they aren't looking   |
|                      | for scary bugs and are searching the word MITTENS,    |
|                      | the excerpt should center around this part.           |
+----------------------+-------------------------------------------------------+
""")
    self.AssertErrContains('Listed 1 of 1 items.')

  def testOutput_MatchesMultipleCommands(self):
    """Test the command output when multiple commands match."""
    self.Run('help -- zero')
    # Matching flag name is more important than matching capsule.
    self.AssertOutputEquals("""\
+-----------------------------------+------------------------------------------+
|              COMMAND              |                 SUMMARY                  |
+-----------------------------------+------------------------------------------+
| gcloud sdk xyzzy                  | Brief description of what Nothing        |
|                                   | Happens means.                           |
|                                   | FLAGS                                    |
|                                   | --ZERO-or-more                           |
|                                   | ZERO or more description.                |
+-----------------------------------+------------------------------------------+
| gcloud sdk second-level-command-1 | gcloud sdk tests command, matches for    |
|                                   | ZERO.                                    |
+-----------------------------------+------------------------------------------+
""")
    self.AssertErrContains('Listed 2 of 2 items.')

  def testOutput_MatchesFlag(self):
    """Test the command output when a flag description matches the term."""
    self.Run('help -- phoebe')
    self.AssertOutputEquals("""\
+------------------+-----------------------------------------------------------+
|     COMMAND      |                          SUMMARY                          |
+------------------+-----------------------------------------------------------+
| gcloud sdk xyzzy | Brief description of what Nothing Happens means.          |
|                  | FLAGS                                                     |
|                  | --three-choices                                           |
|                  | Choices description. FRIENDS must be one of: rachel,      |
|                  | PHOEBE, monica.                                           |
+------------------+-----------------------------------------------------------+
""")
    self.AssertErrContains('Listed 1 of 1 items.')

  def testOutput_MatchesPositional(self):
    """Test the command output when a positional matches the term."""
    self.Run('help -- pdq')
    self.AssertOutputEquals("""\
+------------------+--------------------------------------------------+
|     COMMAND      |                     SUMMARY                      |
+------------------+--------------------------------------------------+
| gcloud sdk xyzzy | Brief description of what Nothing Happens means. |
|                  | POSITIONALS                                      |
|                  | PDQ                                              |
|                  | PDQ the PDQ.                                     |
+------------------+--------------------------------------------------+
""")
    self.AssertErrContains('Listed 1 of 1 items.')

  def testOutput_TwoTerms(self):
    """Test command output with two terms."""
    self.Run('help -- three happens')
    self.AssertOutputEquals("""\
+-----------------------------------------+------------------------------------+
|                 COMMAND                 |              SUMMARY               |
+-----------------------------------------+------------------------------------+
| gcloud sdk xyzzy                        | Brief description of what Nothing  |
|                                         | HAPPENS means.                     |
|                                         | FLAGS                              |
|                                         | --exactly-THREE                    |
|                                         | Exactly THREE description.         |
+-----------------------------------------+------------------------------------+
| gcloud beta sdk betagroup sub-command-a | (BETA) gcloud sdk tests command.   |
|                                         | FLAGS                              |
|                                         | --one-two-THREE                    |
|                                         | ...four!. ONE_TWO_THREE must be    |
|                                         | one of: 1, 2, 3.                   |
+-----------------------------------------+------------------------------------+
""")
    self.AssertErrContains('Listed 2 of 2 items.')

  def testOutput_MatchesPath(self):
    """Test the command output when a positional matches the term."""
    self.Run('help xyzzy')
    self.AssertOutputEquals("""\
+------------------+-----------------------------------------------------------+
|     COMMAND      |                          SUMMARY                          |
+------------------+-----------------------------------------------------------+
| gcloud sdk XYZZY | Brief description of what Nothing Happens means.          |
+------------------+-----------------------------------------------------------+
| gcloud sdk       | gcloud sdk tests second level group.                      |
|                  | COMMANDS                                                  |
|                  | long-help, second-level-command-1,                        |
|                  | second-level-command-b, subgroup, XYZZY                   |
+------------------+-----------------------------------------------------------+
""")
    self.AssertErrContains('Listed 2 of 2 items.')


class TableBundleTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):
  """Bundle tests to make sure help search runs in bundled SDK."""

  def testTableExistsAndUsedBySearchHelp(self):
    """Test that in bundled SDK, table already exists and help search runs."""
    self.assertTrue(os.path.exists(cli_tree.CliTreePath()))
    # Make basic assertion that we can run search and find results.
    results = self.Run('help -- project')
    self.assertTrue(results)


if __name__ == '__main__':
  cli_test_base.main()
