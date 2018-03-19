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

"""Unit tests for calliope argparse vs argcomplete."""

from tests.lib import cli_test_base
from tests.lib.calliope import util as calliope_test_util


class StopExecutionException(Exception):
  """argcomplete exit exception."""


def ChoicesCompleter(**_):
  return ['abc', 'ac', 'xy', 'xyz']


class ArgCompleteTest(cli_test_base.WithCompletion):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

  def testChoicesCompleter(self):
    self.parser.add_argument(
        'name', nargs=1, completer=ChoicesCompleter, help='Auxilio aliis.')
    self.RunParserCompletion(self.parser, '', ['abc', 'ac', 'xy', 'xyz'])
    self.RunParserCompletion(self.parser, 'a', ['abc', 'ac'])
    self.RunParserCompletion(self.parser, 'x', ['xy', 'xyz'])
