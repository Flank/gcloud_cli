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

"""Tests for the calliope.cli_tree module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.core import config
from googlecloudsdk.core.resource import resource_printer
from tests.lib import calliope_test_base
from tests.lib import test_case
from tests.lib.calliope import util as calliope_test_util

import mock


class CliTreeTest(test_case.TestCase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

  def testCliTreeNoScrubFlag(self):
    name = '--value'
    default = 'Original unscrubbed value.'
    description_without_default = 'The value.'
    description = '{} The default is "{}".'.format(
        description_without_default, default)
    flag = self.parser.add_argument(name, help=description, default=default)
    tree_flag = cli_tree.Flag(flag, name)
    self.assertEqual(description, tree_flag.description)
    self.assertEqual(default, tree_flag.default)

  def testCliTreeScrubFlagUnix(self):
    name = '--path'
    default = '/home/bozo'
    description_without_default = 'The Path.'
    description = '{} The default value is "{}".'.format(
        description_without_default, default)
    flag = self.parser.add_argument(name, help=description, default=default)
    tree_flag = cli_tree.Flag(flag, name)
    self.assertEqual(description_without_default, tree_flag.description)
    self.assertIsNone(tree_flag.default)

  def testCliTreeScrubFlagWindows(self):
    name = '--path'
    default = r'c:\home\bozo'
    description_without_default = 'The Path.'
    description = '{} The default is "{}".'.format(
        description_without_default, default)
    flag = self.parser.add_argument(name, help=description, default=default)
    tree_flag = cli_tree.Flag(flag, name)
    self.assertEqual(description_without_default, tree_flag.description)
    self.assertIsNone(tree_flag.default)

  def testCliTreeNoScrubPositional(self):
    name = 'value'
    default = 'Original unscrubbed value.'
    description_without_default = 'The value.'
    description = '{} The default is "{}".'.format(
        description_without_default, default)
    positional = self.parser.add_argument(
        name, help=description, default=default)
    tree_positional = cli_tree.Positional(positional, name)
    self.assertEqual(description, tree_positional.description)
    self.assertEqual(default, tree_positional.default)

  def testCliTreeScrubPositionalUnix(self):
    name = 'path'
    default = '/home/bozo'
    description_without_default = 'The Path.'
    description = '{} The default value is "{}".'.format(
        description_without_default, default)
    positional = self.parser.add_argument(
        name, help=description, default=default)
    tree_positional = cli_tree.Positional(positional, name)
    self.assertEqual(description_without_default, tree_positional.description)
    self.assertIsNone(tree_positional.default)

  def testCliTreeScrubPositionalWindows(self):
    name = 'path'
    default = r'c:\home\bozo'
    description_without_default = 'The Path.'
    description = '{} The default is "{}".'.format(
        description_without_default, default)
    positional = self.parser.add_argument(
        name, help=description, default=default)
    tree_positional = cli_tree.Positional(positional, name)
    self.assertEqual(description_without_default, tree_positional.description)
    self.assertIsNone(tree_positional.default)


class CliTreeVersionTest(calliope_test_base.CalliopeTestBase):

  CLI_VERSION = '1.2.3'
  INVALID_CLI_VERSION = '4.5.6'
  INVALID_VERSION = 'NaN'
  PATH = '/gcloud/data/cli/gcloud.json'

  def SetUp(self):
    self.StartObjectPatch(
        cli_tree, '_GetDefaultCliCommandVersion', return_value='1.2.3')

  def testIsUpToDate(self):
    tree = {
        cli_tree.LOOKUP_VERSION: cli_tree.VERSION,
        cli_tree.LOOKUP_CLI_VERSION: self.CLI_VERSION,
    }

    self.assertTrue(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=False))
    self.AssertErrEquals('')

    self.ClearErr()
    self.assertTrue(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=True))
    self.AssertErrEquals('[gcloud] CLI tree version [1.2.3] is up to date.\n')

  def testIsUpToDateCliVersionTest(self):
    tree = {
        cli_tree.LOOKUP_VERSION: cli_tree.VERSION,
        cli_tree.LOOKUP_CLI_VERSION: 'TEST',
    }

    self.assertTrue(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=True))
    self.AssertErrEquals('[gcloud] CLI tree version [1.2.3] is up to date.\n')

  def testIsUpToDateCliVersionHead(self):
    tree = {
        cli_tree.LOOKUP_VERSION: cli_tree.VERSION,
        cli_tree.LOOKUP_CLI_VERSION: 'HEAD',
    }

    self.assertTrue(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=True))
    self.AssertErrEquals('[gcloud] CLI tree version [1.2.3] is up to date.\n')

  def testIsUpToDateVersionDiff(self):
    tree = {
        cli_tree.LOOKUP_VERSION: self.INVALID_VERSION,
        cli_tree.LOOKUP_CLI_VERSION: self.CLI_VERSION,
    }

    self.assertFalse(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=True))
    self.AssertErrEquals('')

    with self.AssertRaisesExceptionMatches(
        cli_tree.CliCommandVersionError,
        'CLI tree [/gcloud/data/cli/gcloud.json] version is [NaN], '
        'expected [1]'):
      cli_tree._IsUpToDate(
          tree, path=self.PATH, ignore_errors=False, verbose=True)

  def testIsUpToDateCliVersionDiff(self):
    tree = {
        cli_tree.LOOKUP_VERSION: cli_tree.VERSION,
        cli_tree.LOOKUP_CLI_VERSION: self.INVALID_CLI_VERSION,
    }

    self.assertFalse(cli_tree._IsUpToDate(
        tree, path=self.PATH, ignore_errors=True, verbose=True))
    self.AssertErrEquals('')

    with self.AssertRaisesExceptionMatches(
        cli_tree.CliCommandVersionError,
        'CLI tree [/gcloud/data/cli/gcloud.json] command version is '
        '[4.5.6], expected [1.2.3]'):
      cli_tree._IsUpToDate(
          tree, path=self.PATH, ignore_errors=False, verbose=True)


class DumpLoadTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(cli_tree, '_IsRunningUnderTest', return_value=True)
    self.WalkTestCli('sdk4')

  def testDumpNoSdkRoot(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=None)
    with self.assertRaises(cli_tree.SdkRootNotFoundError):
      cli_tree.Dump(cli=self.test_cli)

  def testLoadNoSdkRootOneTimeUseOK(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=None)
    tree = cli_tree.Load(cli=self.test_cli, one_time_use_ok=True)
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud-deserialized.json')

  def testDumpToStdout(self):
    cli_tree.Dump(self.test_cli, path='-')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud.json')

  def testDumpBranchToStdout(self):
    cli_tree.Dump(self.test_cli, path='-', branch=['sdk', 'subgroup'])
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud-branch.json')

  def testDumpToPathAndLoad(self):

    # Check generation to stdout.
    temp = os.path.join(self.temp_path, 'gcloud.json')
    cli_tree.Dump(cli=self.test_cli, path=temp)
    self.AssertFileIsGolden(temp, self.test_data_dir, 'gcloud.json')
    self.AssertErrContains('Generating the gcloud CLI and caching in')
    self.ClearErr()

    # The remaining subtests are about this helper.
    generate_root = self.StartObjectPatch(
        cli_tree,
        '_GenerateRoot',
        side_effect=cli_tree._GenerateRoot,
    )

    # Check generation to path.
    tree = cli_tree.Load(path=temp)
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud-deserialized.json')
    generate_root.assert_not_called()
    self.AssertErrEquals('')

    # Check force regeneration on load.
    cli_tree.Load(cli=self.test_cli, path=temp, force=True, verbose=True)
    generate_root.assert_called_once_with(
        cli=mock.ANY,
        path=temp,
        name=cli_tree.DEFAULT_CLI_NAME,
        branch=None,
    )
    self.AssertErrContains('Generating the gcloud CLI and caching in')

  def testDumpToPathChangeVersionAndLoad(self):
    # Generate to path with current version.
    temp = os.path.join(self.temp_path, 'gcloud.json')
    tree = cli_tree.Load(cli=self.test_cli, path=temp)
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud-deserialized.json')
    self.ClearOutput()

    # Verify the current version was loaded.
    self.assertEqual(cli_tree.VERSION, tree[cli_tree.LOOKUP_VERSION])

    # Change the current version, reload the tree, verify it was regenerated
    # with the new version.
    old_version = cli_tree.VERSION
    new_version = '0'  # The first VERSION was 1.
    try:
      cli_tree.VERSION = new_version
      tree = cli_tree.Load(cli=self.test_cli, path=temp)
    finally:
      cli_tree.VERSION = old_version

    # The regenerated tree should have the new version.
    self.assertEqual(new_version, tree[cli_tree.LOOKUP_VERSION])


if __name__ == '__main__':
  test_case.main()
