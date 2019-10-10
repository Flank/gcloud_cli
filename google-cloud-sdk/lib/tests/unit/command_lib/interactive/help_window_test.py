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

"""Tests for the help window used by gcloud interactive."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import config
from googlecloudsdk.command_lib.interactive import help_window
from googlecloudsdk.command_lib.interactive import parser
from tests.lib import subtests
from tests.unit.command_lib.interactive import testdata
from prompt_toolkit import token

HELP_WIDTH = 10


class MockDocument(object):

  def __init__(self, text, position=0):
    self.cursor_position = position
    self.text_before_cursor = text


class MockBuffer(object):

  def __init__(self, text, position=0):
    self.document = MockDocument(text, position)


class MockCli(object):

  def __init__(self, root, text, position=None):
    self.root = root
    if position is None:
      position = text.rfind(' ') + 1
    self.parser = parser.Parser(root)
    self.current_buffer = MockBuffer(text, position)
    self.config = config.Config()


class GenerateHelpContentTest(subtests.Base):

  @classmethod
  def SetUpClass(cls):
    path = os.path.join(os.path.dirname(testdata.__file__), 'gcloud.json')
    cls.tree = cli_tree.Load(path=path)

  def RunSubTest(self, text):
    cli = MockCli(self.tree, text)
    return help_window.GenerateHelpContent(cli, HELP_WIDTH)

  def testCorrectHelpIsGenerated(self):
    expected = [
        [(token.Token.Markdown.Bold, 'gcloud')],
        [(token.Token.Markdown.Bold, 'compute')],
        [(token.Token.Markdown.Bold, 'instances')],
        [(token.Token.Markdown.Bold, 'create'),
         (token.Token.Markdown.Normal, ' '),
         (token.Token.Markdown.Truncated, '...')],
        [],
        [(token.Token.Markdown.Section, 'SYNOPSIS')],
        [],
        [(token.Token.Markdown.Normal, '        '),
         (token.Token.Markdown.Code, 'gcloud')],
        [(token.Token.Markdown.Code, '        compute')],
        [(token.Token.Markdown.Code, '        instances'),
         (token.Token.Markdown.Truncated, '...')],
    ]
    self.Run(expected, 'compute instances create')

    expected = [
        [(token.Token.Markdown.Normal, ' '),
         (token.Token.Markdown.Definition, '--project'),
         (token.Token.Markdown.Normal, '='),
         (token.Token.Markdown.Value, 'PROJECT_ID')],
        [(token.Token.Markdown.Normal, '    The')],
        [(token.Token.Markdown.Normal, '    Google')],
        [(token.Token.Markdown.Normal, '    Cloud')],
        [(token.Token.Markdown.Normal, '    Platform')],
        [(token.Token.Markdown.Normal, '    project')],
        [(token.Token.Markdown.Normal, '    name')],
        [(token.Token.Markdown.Normal, '    to')],
        [(token.Token.Markdown.Normal, '    use')],
        [(token.Token.Markdown.Normal, '    for'),
         (token.Token.Markdown.Truncated, '...')],
    ]
    self.Run(expected, '--project')
    self.Run(expected, '--project=')
    self.Run(expected, '--project=arg')
    self.Run(expected, '--project ')
    self.Run(expected, '--project arg')
    self.Run(expected, '--project\t')
    self.Run(expected, '--project\targ')
