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

"""Tests for the table module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.search_help import lookup
from googlecloudsdk.core import config
from googlecloudsdk.core.util import files as file_utils
from tests.lib import calliope_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class TableTests(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(cli_tree, '_IsRunningUnderTest', return_value=True)
    sdk_root_dir = self.CreateTempDir('fake_root_dir')
    self.table_dir_path = os.path.join(sdk_root_dir, 'data', 'cli')
    file_utils.MakeDir(self.table_dir_path)

    self.sdk_root_mock = self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value=sdk_root_dir)
    self.table_file_path = os.path.join(self.table_dir_path, 'gcloud.json')

    # Load the mock CLI.
    self.test_cli = self.LoadTestCli('sdk4')

  def testTableProperties(self):
    """Ensure gcloud tree statisfies table properties."""

    # Generate the help text table
    help_index = cli_tree._GenerateRoot(self.test_cli)

    # Command nodes (including alpha/beta) should have children commands.
    sdk_node = help_index.commands['sdk']
    self.assertTrue('xyzzy' in sdk_node.commands)
    alpha_node = help_index.commands['alpha']
    alpha_sdk_node = alpha_node.commands['sdk']
    self.assertTrue('alphagroup' in alpha_sdk_node.commands)
    beta_node = help_index.commands['beta']
    beta_sdk_node = beta_node.commands['sdk']
    self.assertTrue('betagroup' in beta_sdk_node.commands)

    # Hidden commands are included in the index but not in search results.
    sdk_root = help_index.commands.get('sdk')
    self.assertTrue('hidden-command' in sdk_root.commands)
    # Hidden groups are included in the index but not in search results.
    self.assertTrue('hiddengroup' in sdk_root.commands)

    # Assert the root node has the global flags
    root_flags = help_index.flags
    self.assertTrue('--help' in root_flags)

    # Assert that other nodes have global flags
    xyzzy = sdk_root.commands.get('xyzzy')
    self.assertTrue('--help' in xyzzy.flags)

    # Non-global flags should be included in command nodes.
    self.assertTrue('--zero-or-one' in xyzzy.flags)

    # Hidden flags are included in the index but not in search results.
    self.assertTrue('--hidden' in xyzzy.flags)

    # Check that flags contain help information.
    self.assertEqual(xyzzy.flags['--exactly-three'].name, '--exactly-three')
    self.assertEqual(xyzzy.flags['--exactly-three'].default,
                     ['Moe', 'Larry', 'Shemp'])
    self.assertEqual(xyzzy.flags['--exactly-three'].description,
                     'Exactly three description.')

    # Positionals should be included in command nodes.
    self.assertEqual([p.name for p in xyzzy.positionals], ['pdq'])

    # Check that positionals contain help information.
    self.assertEqual([p.description for p in xyzzy.positionals],
                     ['pdq the PDQ.'])

    # Check that command contains help information.
    self.assertEqual(
        xyzzy.sections,
        {
            'DESCRIPTION': 'Nothing Happens.',
            'EXAMPLES': textwrap.dedent(
                """\
                Try these:
                $ echo one
                $ gcloud components list
                """),
            'NOTES': textwrap.dedent(
                """\
                These variants are also available:

                  $ gcloud alpha sdk xyzzy
                  $ gcloud beta sdk xyzzy"""),
        }
    )
    self.assertEqual(xyzzy.capsule,
                     'Brief description of what Nothing Happens means.')

  def testFirstUpdate(self):
    # Ensure table file does not exist
    table_path = cli_tree.CliTreePath()
    self.assertEqual(self.table_file_path, table_path)

    # Update the table
    cli_tree.Dump(self.test_cli)

    # Ensure table exists
    self.assertTrue(os.path.isfile(self.table_file_path))

  def testOverridingUpdate(self):
    # Create table file
    with open(self.table_file_path, 'w') as table_file:
      table_contents = 'I am a help table.\n'
      table_file.write(table_contents)
    with open(self.table_file_path) as table_file:
      self.assertEqual(table_contents, table_file.readline())

    # Update the table
    cli_tree.Dump(self.test_cli)

    # Ensure table files exist
    self.assertTrue(os.path.isfile(self.table_file_path))

    # Ensure table files contents have been updated
    with open(self.table_file_path) as table_file:
      self.assertNotEquals(table_contents, table_file.readline())

  def testTableContentsAndLoading(self):
    # Update the table
    cli_tree.Dump(self.test_cli)

    # Check contents
    self.AssertFileIsGolden(self.table_file_path, __file__, 'gcloud.json')

    # Load table
    table_contents = cli_tree.Load()

    # Basic check of table contents
    self.assertTrue('beta' in table_contents[lookup.COMMANDS])
    self.assertTrue('--help' in table_contents[lookup.FLAGS])

  def testNoSdkRootRaisesError(self):
    self.sdk_root_mock.return_value = None
    with self.AssertRaisesExceptionMatches(
        cli_tree.SdkRootNotFoundError,
        'SDK root not found for this installation. '
        'CLI tree cannot be loaded or generated.'):
      cli_tree.CliTreePath()


class TableBundleTests(sdk_test_base.BundledBase,
                       calliope_test_base.CalliopeTestBase):
  """Bundle tests to ensure help table location has not changed."""

  def SetUp(self):
    self.StartObjectPatch(cli_tree, '_IsRunningUnderTest', return_value=True)

  def testTableExists(self):
    # The table should already exist
    path = cli_tree.CliTreePath()
    self.AssertFileExists(path)

  def testTableCanBeLoaded(self):
    # Load table, it should already exist
    help_table = cli_tree.Load()

    # Make basic assertions against table contents
    self.assertTrue('beta' in help_table[lookup.COMMANDS])
    self.assertTrue('--help' in help_table[lookup.FLAGS])


if __name__ == '__main__':
  test_case.main()
