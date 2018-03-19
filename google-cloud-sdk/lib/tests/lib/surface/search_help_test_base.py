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
"""Unit test base for help search."""

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.search_help import lookup
from tests.lib import calliope_test_base


class SearchHelpTestBase(calliope_test_base.CalliopeTestBase):
  """Base class for running tests of gcloud help search libraries."""

  def SetUp(self):
    self.table_dir_path = self.CreateTempDir('cli')
    self.StartObjectPatch(
        cli_tree, 'CliTreeDir', return_value=self.table_dir_path)

    self.table_file_path = cli_tree.CliTreePath()

    # Load the mock CLI and write the help table.
    self.test_cli = self.LoadTestCli('sdk8', modules=['broken_sdk'])
    self.parent = cli_tree.Load(cli=self.test_cli)

    # Store names of commands to be used.
    self.sdk = self.parent.get(lookup.COMMANDS, {}).get('sdk', {})
    self.long_help = self.sdk.get(lookup.COMMANDS, {}).get('long-help', {})
    self.xyzzy = self.sdk.get(lookup.COMMANDS, {}).get('xyzzy', {})
    self.subgroup = self.sdk.get(lookup.COMMANDS, {}).get('subgroup', {})


if __name__ == '__main__':
  calliope_test_base.main()
