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

"""Tests for calliope.cli_tree_markdown module."""

import difflib
import json
import os
import StringIO

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.calliope import cli_tree_markdown
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.calliope import walker_util
from googlecloudsdk.command_lib.meta import help_util
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base
from tests.lib import test_case


def GenerateMarkdownFromCliTree(command, root, directory):
  """DFS on the command subtree, markdown generated at each level."""
  path = os.path.join(
      directory, '_'.join(command[cli_tree.LOOKUP_PATH])) + '.md'
  with open(path, 'w') as f:
    md = cli_tree_markdown.Markdown(command, root)
    render_document.RenderDocument(
        style='markdown',
        title=' '.join(command[cli_tree.LOOKUP_PATH]),
        fin=StringIO.StringIO(md),
        out=f)
  for cmd in command[cli_tree.LOOKUP_COMMANDS].values():
    GenerateMarkdownFromCliTree(cmd, root, directory)


class Accumulator(help_util.DiffAccumulator):
  """A module for accumulating DirDiff() differences."""

  def AddChange(self, op, relative_file, old_contents=None, new_contents=None):
    """Called for each file difference."""
    super(Accumulator, self).AddChange(
        op, relative_file, old_contents, new_contents)
    if op == 'edit':
      old_lines = old_contents.split('\n')
      new_lines = new_contents.split('\n')
      diff_lines = difflib.unified_diff(old_lines, new_lines)
      print '<<<REGRESSION {}>>>'.format(relative_file)
      print '\n'.join(diff_lines)
    return None


def _FilterFlagNames(names):
  return [name for name in names if name.startswith('--')]


class CliTreeMarkdownTest(calliope_test_base.CalliopeTestBase,
                          test_case.WithOutputCapture):

  def SetUp(self):
    # Load the mock CLI.
    self.cli = self.LoadTestCli('sdk4')
    self.StartObjectPatch(usage_text, '_FilterFlagNames', _FilterFlagNames)

  def testMarkdownGenerators(self):
    """CommandMarkdownGenerator and CliTreeMarkdownGenerator should match."""

    # The normal help doc generation flow: generate the markdown for the loaded
    # CLI into a directory, one markdown file per command.
    command_directory = os.path.join(self.temp_path, 'command')
    walker_util.DocumentGenerator(
        self.cli, command_directory, 'markdown', '.md').Walk()

    # The help doc generation flow under test: generate the markdown for the
    # generated cli_tree into a directory, one markdown file per command using
    # the same markdown file name scheme as above.
    tree_directory = os.path.join(self.temp_path, 'tree')
    files.MakeDir(tree_directory)
    internal_tree = walker_util.GCloudTreeGenerator(self.cli).Walk()
    external_tree = StringIO.StringIO()
    resource_printer.Print(
        resources=internal_tree, print_format='json', out=external_tree)
    tree = json.loads(external_tree.getvalue())
    GenerateMarkdownFromCliTree(tree, tree, tree_directory)

    # Compare the output dir contents.
    accumulator = Accumulator()
    help_util.DirDiff(command_directory, tree_directory, accumulator)
    self.assertEqual(0, accumulator.GetChanges())


class CliTreeMarkdownFromTreeTest(test_case.TestCase):

  ROOT = {
      cli_tree.LOOKUP_CAPSULE: 'Root command with empty path.',
      cli_tree.LOOKUP_COMMANDS: {
          'exit': {
              cli_tree.LOOKUP_CAPSULE: 'Exit the shell.',
              cli_tree.LOOKUP_COMMANDS: {},
              cli_tree.LOOKUP_FLAGS: {},
              cli_tree.LOOKUP_IS_GROUP: False,
              cli_tree.LOOKUP_IS_HIDDEN: False,
              cli_tree.LOOKUP_PATH: ['exit'],
              cli_tree.LOOKUP_POSITIONALS: {},
              cli_tree.LOOKUP_RELEASE: 'GA',
              cli_tree.LOOKUP_SECTIONS: {'DESCRIPTION': 'Exit the shell.'},
          },
      },
      cli_tree.LOOKUP_FLAGS: {},
      cli_tree.LOOKUP_IS_GROUP: True,
      cli_tree.LOOKUP_IS_HIDDEN: False,
      cli_tree.LOOKUP_PATH: [],
      cli_tree.LOOKUP_POSITIONALS: {},
      cli_tree.LOOKUP_RELEASE: 'GA',
      cli_tree.LOOKUP_SECTIONS: {'DESCRIPTION': 'The gcloud shell.'},
  }

  def testRootCommandMarkdown(self):
    md = cli_tree_markdown.CliTreeMarkdownGenerator(
        self.ROOT, self.ROOT).Generate()
    expected = """\
# (1)


## NAME

 - root command with empty path


## SYNOPSIS

`` _COMMAND_


## DESCRIPTION

The gcloud shell.


## COMMANDS

`_COMMAND_` is one of the following:

*link:exit[exit]*::

Exit the shell.
"""
    self.assertEquals(expected, md)


if __name__ == '__main__':
  test_case.main()
