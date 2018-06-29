# -*- coding: utf-8 -*-
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

"""Tests for error Deprecation Manager."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import command_loading
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class DeprecationUtilsTests(cli_test_base.CliTestBase,
                            sdk_test_base.WithLogCapture):

  def _CreateCLI(self):
    pkg_root = self.Resource('tests', 'unit', 'command_lib',
                             'deprecation_manager', 'test_data')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(pkg_root, 'alpha'))
    return loader.Generate()

  def testDeprecateAtVersion(self):
    self.cli.Execute(['dep-command-withnoalt'])
    self.AssertLogContains('Test Command Complete\n')
    self.AssertErrContains("""\
WARNING: This command is deprecated and will be removed in version 1.3.0.
Test Command Complete
""")

  def testDeprecateAtVersionHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['dep-command-withnoalt', '--help'])
    self.AssertOutputContains('(DEPRECATED)')

  def testRemoveAtVersion(self):
    with self.assertRaisesRegex(calliope_base.DeprecationException,
                                'This command has been removed.'):
      self.cli.Execute(['remove-command-withnoalt'])
    self.AssertLogNotContains('Test Command Complete')

  def testRemoveAtVersionHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['remove-command-withnoalt', '--help'])
    self.AssertOutputContains('(REMOVED)')

  def testDeprecateWithVersionAndReplacement(self):
    self.cli.Execute(['dep-command-withalt'])
    self.AssertLogContains('Test Command Complete\n')
    self.AssertErrContains("""\
WARNING: This command is deprecated and will be removed in version 1.3.0. Use `alt-command` instead.
Test Command Complete
""")

  def testDeprecateWithVersionAndReplacementHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['dep-command-withalt', '--help'])
    self.AssertOutputContains('(DEPRECATED)')

  def testRemoveWithVersionAndReplacement(self):
    with self.assertRaisesRegex(calliope_base.DeprecationException,
                                'This command has been removed.'):
      self.cli.Execute(['remove-command-withalt'])
    self.AssertLogNotContains('Test Command Complete')

  def testRemoveWithVersionAndReplacementHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['remove-command-withalt', '--help'])
    self.AssertOutputContains('(REMOVED)')
    self.AssertOutputContains(('This command is an internal '
                               'implementation detail'))

  def testDeprecateWithInvalidVersion(self):
    with self.assertRaisesRegex(command_loading.CommandLoadFailure,
                                'Valid remove version is required'):
      self.cli.Execute(['command-withbadversion'])
    self.AssertLogNotContains('Test Command Complete\n')


if __name__ == '__main__':
  test_case.main()

