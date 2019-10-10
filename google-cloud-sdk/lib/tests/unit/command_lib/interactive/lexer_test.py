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
"""Tests for the gcloud interactive lexer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.interactive import lexer
from tests.lib import subtests


class GetShellTokensTests(subtests.Base):

  def RunSubTest(self, s):
    return lexer.GetShellTokens(s)

  def testParse(self):
    T = lexer.ShellToken      # pylint: disable=invalid-name
    L = lexer.ShellTokenType  # pylint: disable=invalid-name

    # Args
    self.Run([T('compute', L.ARG, 0, 7)], 'compute')
    self.Run([T('compute', L.ARG, 0, 7), T('ssh', L.ARG, 8, 11)], 'compute ssh')
    self.Run([T('"&"', L.ARG, 0, 3)], '"&"')
    self.Run([T('"with spaces"', L.ARG, 0, 13)], '"with spaces"')
    self.Run([T('"mixed"\'quotes\'', L.ARG, 0, 15)], '"mixed"\'quotes\'')

    # Flags
    self.Run([T('-q', L.FLAG, 0, 2)], '-q')
    self.Run([T('--quiet', L.FLAG, 0, 7)], '--quiet')
    self.Run(
        [T('--project', L.FLAG, 0, 9), T('foo', L.ARG, 10, 13),
         T('-q', L.FLAG, 14, 16)],
        '--project foo -q')
    self.Run([T('compute', L.ARG, 0, 7), T('ssh', L.ARG, 8, 11),
              T('--zone', L.FLAG, 12, 18)],
             'compute ssh --zone')

    # Flags with values
    self.Run([T('--foo=', L.FLAG, 0, 6)], '--foo=')
    self.Run([T('--foo=bar', L.FLAG, 0, 9)], '--foo=bar')

    # Terminators
    self.Run([T('&', L.TERMINATOR, 0, 1)], '&')
    self.Run([T(';', L.TERMINATOR, 0, 1)], ';')
    self.Run([T('|', L.TERMINATOR, 0, 1)], '|')
    self.Run([T('foo', L.ARG, 0, 3), T('&', L.TERMINATOR, 3, 4),
              T('bar', L.ARG, 4, 7)],
             'foo&bar')

    # Trailing backslash
    self.Run([T('\\', L.TRAILING_BACKSLASH, 0, 1)], '\\')
    self.Run([T('foo', L.ARG, 0, 3),
              T('\\', L.TRAILING_BACKSLASH, 3, 4)],
             'foo\\')

    # TODO(b/36002926): test IO, REDIRECTION, and FILE
