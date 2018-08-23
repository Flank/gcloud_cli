# -*- coding: utf-8 -*- #
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

"""Tests for gcloud search-help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.search_help import lookup
from googlecloudsdk.core.console import console_attr
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SearchHelpTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.table_dir_path = self.CreateTempDir('help_text')
    self.StartObjectPatch(
        cli_tree, 'CliTreeDir', return_value=self.table_dir_path)
    # Mock the console width.
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize', return_value=(80, 100))

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
    results = self.Run('search-help chandler')
    self.assertEqual(results, [])

  def testResults(self):
    """Test that results return as expected."""
    expected_summary = (
        'SUMMARY DESCRIPTION\n'
        'A test command with a long help section.\n'
        'DESCRIPTION\n'
        '...aren\'t so close to the other terms in the next '
        'paragraph. On the other hand if they aren\'t looking for '
        'scary bugs and are searching the word mittens, the excerpt '
        'should center around this part.')
    expected_result = copy.deepcopy(self.long_help)
    expected_result.update({lookup.COMMANDS: [],
                            lookup.SUMMARY: expected_summary})
    results = self.Run('search-help mittens')
    self.assertEqual(results, [expected_result])

  def testOutput_MatchesDescription(self):
    """Test the command output when the description matches the term."""
    self.Run('search-help mittens')
    self.AssertOutputEquals(textwrap.dedent("""\
    COMMAND               HELP
    gcloud sdk long-help  SUMMARY DESCRIPTION
                          A test command with a long help section.
                          DESCRIPTION
                          ...aren't so close to the other terms in the next
                          paragraph. On the other hand if they aren't looking for
                          scary bugs and are searching the word mittens, the excerpt
                          should center around this part.
    """))

  def testOutput_MatchesMultipleLocations(self):
    """Test the command output when multiple locations in command match."""
    # Return the examples section for xyzzy, rather than the flags.
    self.Run('search-help one')
    self.AssertOutputEquals(textwrap.dedent("""\
    COMMAND           HELP
    gcloud            SUMMARY DESCRIPTION
                      gcloud sdk tests super-group.
                      FLAGS
                      --format
                      ...are: config, csv, default, diff, disable, flattened, get,
                      json, list, multi, none, object, table, text, value, yaml. For
                      more details run $ gcloud topic formats.
    gcloud sdk xyzzy  SUMMARY DESCRIPTION
                      Brief description of what Nothing Happens means.
                      EXAMPLES
                      Try these: $ echo one $ gcloud components list
    """))

  def testOutput_MatchesFlag(self):
    """Test the command output when a flag description matches the term."""
    self.Run('search-help phoebe')
    self.AssertOutputEquals(textwrap.dedent("""\
    COMMAND           HELP
    gcloud sdk xyzzy  SUMMARY DESCRIPTION
                      Brief description of what Nothing Happens means.
                      FLAGS
                      --three-choices
                      Choices description. FRIENDS must be one of: rachel, phoebe,
                      monica.
    """))

  def testOutput_MatchesPositional(self):
    """Test the command output when a positional matches the term."""
    self.Run('search-help pdq')
    self.AssertOutputEquals(textwrap.dedent("""\
    COMMAND           HELP
    gcloud sdk xyzzy  SUMMARY DESCRIPTION
                      Brief description of what Nothing Happens means.
                      POSITIONALS
                      pdq
                      pdq the PDQ.
    """))


class TableBundleTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):
  """Bundle tests to make sure help search runs in bundled SDK."""

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  def testTableExistsAndUsedBySearchHelp(self):
    """Test that in bundled SDK, table already exists and help search runs."""
    self.assertTrue(os.path.exists(cli_tree.CliTreePath()))
    # Make basic assertion that we can run search and find results.
    results = self.Run('search-help project')
    self.assertTrue(results)


if __name__ == '__main__':
  calliope_test_base.main()
