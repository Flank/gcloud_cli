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

"""Tests for gcloud search-help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SearchHelpTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
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

  def testResults_ZeroTermsRaisesError(self):
    """Test searching with zero args raises an error."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument TERM: Must be specified.'):
      self.Run('search-help')

  def testResults_OneTermNotFound(self):
    """Test running help search returns empty list if no results match."""
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run('search-help chandler')
    self.assertEqual([], list(results))

  def testResults(self):
    """Test that results return as expected."""
    properties.VALUES.core.user_output_enabled.Set(False)
    expected_result = copy.deepcopy(self.long_help)
    expected_result.update(
        {lookup.COMMANDS: [],
         lookup.RESULTS: {'mittens': 'sections.DESCRIPTION'},
         lookup.RELEVANCE: 0.25})
    actual = self.Run('search-help mittens')
    self.assertIn(expected_result, actual)
    self.assertEqual(3, len(actual))

  def testOutput_MatchesDescription(self):
    """Test the command output when the description matches the term."""
    self.Run('search-help mittens')
    self.AssertOutputEquals("""\
+----------------------------+-------------------------------------------------+
|          COMMAND           |                     SUMMARY                     |
+----------------------------+-------------------------------------------------+
| gcloud sdk long-help       | A test command with a long help section.        |
|                            | DESCRIPTION                                     |
|                            | ...aren't so close to the other terms in the    |
|                            | next paragraph. On the other hand if they       |
|                            | aren't looking for scary bugs and are searching |
|                            | the word MITTENS, the excerpt should center     |
|                            | around this part.                               |
+----------------------------+-------------------------------------------------+
| gcloud beta sdk long-help  | (BETA) A test command with a long help section. |
|                            | DESCRIPTION                                     |
|                            | ...aren't so close to the other terms in the    |
|                            | next paragraph. On the other hand if they       |
|                            | aren't looking for scary bugs and are searching |
|                            | the word MITTENS, the excerpt should center     |
|                            | around this part.                               |
+----------------------------+-------------------------------------------------+
| gcloud alpha sdk long-help | (ALPHA) A test command with a long help         |
|                            | section.                                        |
|                            | DESCRIPTION                                     |
|                            | ...aren't so close to the other terms in the    |
|                            | next paragraph. On the other hand if they       |
|                            | aren't looking for scary bugs and are searching |
|                            | the word MITTENS, the excerpt should center     |
|                            | around this part.                               |
+----------------------------+-------------------------------------------------+
""")

  def testOutput_MatchesMultipleCommands(self):
    """Test the command output when multiple commands match."""
    self.Run('search-help zero')
    # Matching flag name is more important than matching capsule.
    self.AssertOutputEquals("""\
+----------------------------------------+-------------------------------------+
|                COMMAND                 |               SUMMARY               |
+----------------------------------------+-------------------------------------+
| gcloud sdk xyzzy                       | Brief description of what Nothing   |
|                                        | Happens means.                      |
|                                        | FLAGS                               |
|                                        | --ZERO-or-more                      |
|                                        | ZERO or more description.           |
+----------------------------------------+-------------------------------------+
| gcloud sdk second-level-command-1      | gcloud sdk tests command, matches   |
|                                        | for ZERO.                           |
+----------------------------------------+-------------------------------------+
| gcloud beta sdk xyzzy                  | (BETA) Brief description of what    |
|                                        | Nothing Happens means.              |
|                                        | FLAGS                               |
|                                        | --ZERO-or-more                      |
|                                        | ZERO or more description.           |
+----------------------------------------+-------------------------------------+
| gcloud beta sdk second-level-command-1 | (BETA) gcloud sdk tests command,    |
|                                        | matches for ZERO.                   |
+----------------------------------------+-------------------------------------+
| gcloud alpha sdk xyzzy                 | (ALPHA) Brief description of what   |
|                                        | Nothing Happens means.              |
|                                        | FLAGS                               |
|                                        | --ZERO-or-more                      |
|                                        | ZERO or more description.           |
+----------------------------------------+-------------------------------------+
""")

  def testOutput_MatchesFlag(self):
    """Test the command output when a flag description matches the term."""
    self.Run('search-help phoebe')
    self.AssertOutputEquals("""\
+------------------------+-----------------------------------------------------+
|        COMMAND         |                       SUMMARY                       |
+------------------------+-----------------------------------------------------+
| gcloud sdk xyzzy       | Brief description of what Nothing Happens means.    |
|                        | FLAGS                                               |
|                        | --three-choices                                     |
|                        | Choices description. FRIENDS must be one of:        |
|                        | rachel, PHOEBE, monica.                             |
+------------------------+-----------------------------------------------------+
| gcloud beta sdk xyzzy  | (BETA) Brief description of what Nothing Happens    |
|                        | means.                                              |
|                        | FLAGS                                               |
|                        | --three-choices                                     |
|                        | Choices description. FRIENDS must be one of:        |
|                        | rachel, PHOEBE, monica.                             |
+------------------------+-----------------------------------------------------+
| gcloud alpha sdk xyzzy | (ALPHA) Brief description of what Nothing Happens   |
|                        | means.                                              |
|                        | FLAGS                                               |
|                        | --three-choices                                     |
|                        | Choices description. FRIENDS must be one of:        |
|                        | rachel, PHOEBE, monica.                             |
+------------------------+-----------------------------------------------------+
""")

  def testOutput_MatchesPositional(self):
    """Test the command output when a positional matches the term."""
    self.Run('search-help pdq')
    self.AssertOutputEquals("""\
+------------------------+-----------------------------------------------------+
|        COMMAND         |                       SUMMARY                       |
+------------------------+-----------------------------------------------------+
| gcloud sdk xyzzy       | Brief description of what Nothing Happens means.    |
|                        | POSITIONALS                                         |
|                        | PDQ                                                 |
|                        | PDQ the PDQ.                                        |
+------------------------+-----------------------------------------------------+
| gcloud beta sdk xyzzy  | (BETA) Brief description of what Nothing Happens    |
|                        | means.                                              |
|                        | POSITIONALS                                         |
|                        | PDQ                                                 |
|                        | PDQ the PDQ.                                        |
+------------------------+-----------------------------------------------------+
| gcloud alpha sdk xyzzy | (ALPHA) Brief description of what Nothing Happens   |
|                        | means.                                              |
|                        | POSITIONALS                                         |
|                        | PDQ                                                 |
|                        | PDQ the PDQ.                                        |
+------------------------+-----------------------------------------------------+
""")

  def testOutput_MatchesPath(self):
    """Test the command output when a positional matches the term."""
    self.Run('search-help xyzzy')
    self.AssertOutputEquals("""\
+------------------------+-----------------------------------------------------+
|        COMMAND         |                       SUMMARY                       |
+------------------------+-----------------------------------------------------+
| gcloud sdk XYZZY       | Brief description of what Nothing Happens means.    |
+------------------------+-----------------------------------------------------+
| gcloud sdk             | gcloud sdk tests second level group.                |
|                        | COMMANDS                                            |
|                        | long-help, second-level-command-1,                  |
|                        | second-level-command-b, subgroup, XYZZY             |
+------------------------+-----------------------------------------------------+
| gcloud beta sdk XYZZY  | (BETA) Brief description of what Nothing Happens    |
|                        | means.                                              |
+------------------------+-----------------------------------------------------+
| gcloud beta sdk        | (BETA) gcloud sdk tests second level group.         |
|                        | COMMANDS                                            |
|                        | betagroup, long-help, second-level-command-1,       |
|                        | second-level-command-b, subgroup, XYZZY             |
+------------------------+-----------------------------------------------------+
| gcloud alpha sdk XYZZY | (ALPHA) Brief description of what Nothing Happens   |
|                        | means.                                              |
+------------------------+-----------------------------------------------------+
""")


class TableBundleTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):
  """Bundle tests to make sure help search runs in bundled SDK."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testTableExistsAndUsedBySearchHelp(self):
    """Test that in bundled SDK, table already exists and help search runs."""
    self.assertTrue(os.path.exists(cli_tree.CliTreePath()))
    # Make basic assertion that we can run search and find results.
    results = self.Run('search-help project')
    self.assertTrue(results)


if __name__ == '__main__':
  calliope_test_base.main()
