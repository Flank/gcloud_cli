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

"""Tests for gcloud meta update-cli-trees."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.meta import generate_cli_trees
from tests.lib import calliope_test_base

import mock


class UpdateCliTreesTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.update_cli_trees = self.StartObjectPatch(
        generate_cli_trees, 'UpdateCliTrees')

  def testUpdateCliTrees(self):
    self.Run(['meta', 'cli-trees', 'update'])
    self.update_cli_trees.assert_called_once_with(
        cli=mock.ANY,
        commands=None,
        directory=None,
        force=False,
        tarball=None,
        verbose=True)

  def testUpdateCliTreesWithCommands(self):
    commands = ['abc', 'xyz']
    self.Run(['meta', 'cli-trees', 'update', '--commands', ','.join(commands)])
    self.update_cli_trees.assert_called_once_with(
        cli=mock.ANY,
        commands=commands,
        directory=None,
        force=False,
        tarball=None,
        verbose=True)

  def testUpdateCliTreesWithDirectory(self):
    directory = 'directory'
    self.Run(['meta', 'cli-trees', 'update', '--directory', directory])
    self.update_cli_trees.assert_called_once_with(
        cli=mock.ANY,
        commands=None,
        directory=directory,
        force=False,
        tarball=None,
        verbose=True)

  def testUpdateCliTreesGeneratorsHelp(self):
    with self.assertRaises(SystemExit):
      self.Run(['meta', 'cli-trees', 'update', '--help'])
    self.AssertOutputContains(
        'These CLIs are currently supported: bq, gcloud, gsutil, kubectl.')


if __name__ == '__main__':
  calliope_test_base.main()
