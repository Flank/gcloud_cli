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
"""Tests for the parser used by gcloud interactive."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import lexer
from googlecloudsdk.command_lib.interactive import parser
from tests.lib import subtests
from tests.unit.command_lib.interactive import testdata


class ParseCommandTests(subtests.Base):

  @classmethod
  def SetUpClass(cls):
    path = os.path.join(os.path.dirname(testdata.__file__), 'gcloud.json')
    cls.tree = cli_tree.Load(path=path)
    cls.compute_tree = cls.tree[parser.LOOKUP_COMMANDS]['compute']
    cls.compute_instances_tree = (
        cls.compute_tree[parser.LOOKUP_COMMANDS]['instances'])
    cls.compute_instances_create_tree = (
        cls.compute_instances_tree[parser.LOOKUP_COMMANDS]['create'])
    cls.compute_instances_delete_tree = (
        cls.compute_instances_tree[parser.LOOKUP_COMMANDS]['delete'])
    cls.compute_instances_describe_tree = (
        cls.compute_instances_tree[parser.LOOKUP_COMMANDS]['describe'])
    cls.compute_instances_create_preemptible_flag = (
        cls.compute_instances_create_tree[parser.LOOKUP_FLAGS]['--preemptible'])
    cls.compute_instances_create_image_flag = (
        cls.compute_instances_create_tree[parser.LOOKUP_FLAGS]['--image'])
    cls.project_flag = cls.tree[parser.LOOKUP_FLAGS]['--project']
    cls.quiet_flag = cls.tree[parser.LOOKUP_FLAGS]['--quiet']

  def SetUp(self):
    self.parser = parser.Parser(self.tree)

  def RunSubTest(self, line):
    """Parses all subcommands in line and preserves original line indices."""
    commands = []
    offset = 0
    while line:
      command = self.parser.ParseCommand(line)
      if not command:
        break
      if offset:
        for arg in command:
          arg.start += offset
          arg.end += offset
      offset = command[-1].end + 1
      line = line[offset:]
      commands.append(command)
    return commands

  def testParse(self):
    T = parser.ArgToken      # pylint: disable=invalid-name
    L = parser.ArgTokenType  # pylint: disable=invalid-name

    self.Run([[T('compute', L.GROUP, self.compute_tree, 0, 7)]],
             'compute')
    self.Run([[T('compute', L.GROUP, self.compute_tree, 0, 7),
               T(';', L.SPECIAL, self.tree, 7, 8),
               T('compute', L.GROUP, self.compute_tree, 8, 15)]],
             'compute;compute')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17)]],
        'compute instances')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('create', L.COMMAND, self.compute_instances_create_tree, 18, 24),
          T('--preemptible', L.FLAG,
            self.compute_instances_create_preemptible_flag, 25, 38)]],
        'compute instances create --preemptible')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('create', L.COMMAND, self.compute_instances_create_tree, 18, 24),
          T('--image', L.FLAG, self.compute_instances_create_image_flag, 25,
            32),
          T('foo', L.FLAG_ARG, None, 33, 36)]],
        'compute instances create --image foo')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('create', L.COMMAND, self.compute_instances_create_tree, 18, 24),
          T('--image', L.FLAG, self.compute_instances_create_image_flag, 25,
            32),
          T('foo', L.FLAG_ARG, None, 33, 36)]],
        'compute instances create --image=foo')
    self.Run(
        [[T('--project', L.FLAG, self.project_flag, 0, 9),
          T('foo', L.FLAG_ARG, None, 10, 13),
          T('--quiet', L.FLAG, self.quiet_flag, 14, 21)]],
        '--project=foo --quiet')
    self.Run(
        [[T('--project', L.FLAG, self.project_flag, 0, 9),
          T('', L.FLAG_ARG, None, 10, 10),
          T('--quiet', L.FLAG, self.quiet_flag, 11, 18)]],
        '--project= --quiet')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('describe', L.COMMAND, self.compute_instances_describe_tree, 18,
            26),
          T('foo', L.POSITIONAL,
            self.compute_instances_describe_tree[parser.LOOKUP_POSITIONALS][0],
            27, 30)]],
        'compute instances describe foo')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('delete', L.COMMAND, self.compute_instances_delete_tree, 18, 24),
          T('foo', L.POSITIONAL,
            self.compute_instances_delete_tree[parser.LOOKUP_POSITIONALS][0],
            25, 28)]],
        'compute instances delete foo')
    self.Run(
        [[T('compute', L.GROUP, self.compute_tree, 0, 7),
          T('instances', L.GROUP, self.compute_instances_tree, 8, 17),
          T('delete', L.COMMAND, self.compute_instances_delete_tree, 18, 24),
          T('foo', L.POSITIONAL,
            self.compute_instances_delete_tree[parser.LOOKUP_POSITIONALS][0],
            25, 28),
          T('bar', L.POSITIONAL,
            self.compute_instances_delete_tree[parser.LOOKUP_POSITIONALS][0],
            29, 32)]],
        'compute instances delete foo bar')


class ParseArgsTests(subtests.Base):

  def RunSubTest(self, ts):
    return parser.ParseArgs(ts)

  def testParse(self):
    # Lexer tokens not of type ARG passed to the ParseArgs() function should
    # raise a ValueError exception.
    self.Run(None, [lexer.ShellToken('non_arg',
                                     lexer.ShellTokenType.TERMINATOR, 0, 7)],
             exception=ValueError())
    self.Run(None, [lexer.ShellToken('non_arg', lexer.ShellTokenType.IO, 0, 7)],
             exception=ValueError())
    self.Run(None, [lexer.ShellToken('non_arg',
                                     lexer.ShellTokenType.REDIRECTION, 0, 7)],
             exception=ValueError())
    self.Run(None, [lexer.ShellToken('non_arg',
                                     lexer.ShellTokenType.FILE, 0, 7)],
             exception=ValueError())
    self.Run(None, [lexer.ShellToken('non_arg',
                                     lexer.ShellTokenType.TRAILING_BACKSLASH,
                                     0, 7)], exception=ValueError())
