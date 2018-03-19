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

"""Unit tests for the gcloud interactive application module."""

from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.meta import generate_cli_trees
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

from prompt_toolkit import document
from prompt_toolkit import input as pt_input
from prompt_toolkit import interface
from prompt_toolkit.layout import screen
from prompt_toolkit.terminal import vt100_output


class Mode(object):

  def __init__(self, name):
    self.name = name

  def __enter__(self):
    pass

  def __exit__(self, *args):
    pass


class StdinInput(pt_input.Input):

  def __init__(self, stdin=None):
    self.stdin = stdin or sys.stdin

  def __repr__(self):
    return 'StdinInput(stdin=%r)' % (self.stdin,)

  def raw_mode(self):
    return Mode('raw')

  def cooked_mode(self):
    return Mode('cooked')

  def fileno(self):
    return self.stdin.fileno()

  def read(self):
    return '<INPUT>'


class Vt100Output(vt100_output.Output):

  def __init__(self, stdout, get_size, true_color=False,
               ansi_colors_only=None, term=None, write_binary=True):
    self._buffer = []
    self.stdout = sys.stdout
    self.write_binary = write_binary
    self.get_size = get_size
    self.true_color = False
    self.term = term or 'xterm'
    self.ansi_colors_only = False

  @classmethod
  def from_pty(cls, stdout, true_color=False, ansi_colors_only=None, term=None):

    def get_size():
      rows, columns = 24, 80
      return screen.Size(rows=rows, columns=columns)

    return cls(stdout, get_size, true_color=true_color,
               ansi_colors_only=ansi_colors_only, term=term)

  def fileno(self):
    return self.stdout.fileno()

  def encoding(self):
    return 'utf-8'

  def write_raw(self, data):
    self._buffer.append(data)

  def write(self, data):
    self._buffer.append(data.replace('\x1b', '?'))

  def set_title(self, title):
    self.write(u'<TITLE>{}</TITLE>'.format(
        title.replace('\x1b', '').replace('\x07', '')))

  def clear_title(self):
    self.set_title('')

  def erase_screen(self):
    self.write_raw('<ERASE_SCREEN/>')

  def enter_alternate_screen(self):
    self.write_raw('<ALTERNATE_SCREEN>')

  def quit_alternate_screen(self):
    self.write_raw('</ALTERNATE_SCREEN>')

  def enable_mouse_support(self):
    self.write_raw('<MOUSE>')

  def disable_mouse_support(self):
    self.write_raw('</MOUSE>')

  def erase_end_of_line(self):
    self.write_raw('<ERASE_END/>')

  def erase_down(self):
    self.write_raw('<ERASE_DOWN/>')

  def reset_attributes(self):
    self.write_raw('</ATTRIBUTE>')

  def set_attributes(self, attrs):
    self.write_raw('<ATTRIBUTE>')

  def disable_autowrap(self):
    self.write_raw('</AUTOWRAP>')

  def enable_autowrap(self):
    self.write_raw('<AUTOWRAP>')

  def enable_bracketed_paste(self):
    self.write_raw('<PASTE>')

  def disable_bracketed_paste(self):
    self.write_raw('</PASTE>')

  def cursor_goto(self, row=0, column=0):
    self.write_raw('<GOTO row={} column={}/>'.format(row, column))

  def cursor_up(self, amount):
    self.write_raw('<UP count={}/>'.format(amount))

  def cursor_down(self, amount):
    self.write_raw('<DOWN count={}/>'.format(amount))

  def cursor_forward(self, amount):
    self.write_raw('<RIGHT count={}/>'.format(amount))

  def cursor_backward(self, amount):
    self.write_raw('<LEFT count={}/>'.format(amount))

  def hide_cursor(self):
    self.write_raw('<HIDE>')

  def show_cursor(self):
    self.write_raw('</HIDE>')

  def flush(self):
    if not self._buffer:
      return
    self.stdout.write(''.join(self._buffer))
    self.stdout.flush()
    self._buffer = []

  def ask_for_cpr(self):
    self.write_raw('<CPR/>')

  def bell(self):
    self.write_raw('<PING/>')


@sdk_test_base.Filters.DoNotRunOnWindows  # No Windows screen mocks (yet? ever?)
class ApplicationTests(cli_test_base.CliTestBase):

  def SetInput(self, lines):
    self._input = [document.Document(line) for line in lines]

  def _ReturnValue(self):
    return self._input.pop(0) if self._input else None

  def SetUp(self):
    self._return_value_index = 0
    cli_tree_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    self.StartObjectPatch(
        cli_tree,
        'CliTreeDir',
        return_value=cli_tree_dir)
    self.StartObjectPatch(
        vt100_output.Vt100_Output,
        'from_pty',
        side_effect=Vt100Output.from_pty)
    self.StartObjectPatch(
        interface,
        'StdinInput',
        side_effect=StdinInput)
    self.StartObjectPatch(
        interface.CommandLineInterface,
        'return_value',
        side_effect=self._ReturnValue)
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'MemoizeFailures',
        return_value=None)

  def testInteractiveLayout(self):
    self.SetInput([
        'echo done',  # To prove it doesn't exit on every command.
        'exit',
        'echo should not see this',
    ])
    with self.assertRaises(SystemExit):
      self.Run(['alpha', 'interactive'])
    self.AssertOutputContains(
        'Welcome to the gcloud interactive shell environment.')
    self.AssertOutputContains("""\
<CPR/><PASTE><HIDE></AUTOWRAP></ATTRIBUTE></ATTRIBUTE><ERASE_DOWN/><ATTRIBUTE>$ <LEFT count=2/><RIGHT count=2/></ATTRIBUTE></HIDE><HIDE><LEFT count=2/></ATTRIBUTE><ERASE_DOWN/><ATTRIBUTE>$                                                                              \r<RIGHT count=79/> \r<RIGHT count=0/></ATTRIBUTE>\r
<RIGHT count=0/><ERASE_DOWN/><AUTOWRAP></ATTRIBUTE></HIDE></PASTE><CPR/><PASTE><HIDE></AUTOWRAP></ATTRIBUTE></ATTRIBUTE><ERASE_DOWN/><ATTRIBUTE>$ <LEFT count=2/><RIGHT count=2/></ATTRIBUTE></HIDE><HIDE><LEFT count=2/></ATTRIBUTE><ERASE_DOWN/><ATTRIBUTE>$                                                                              \r<RIGHT count=79/> \r<RIGHT count=0/></ATTRIBUTE>\r
<RIGHT count=0/><ERASE_DOWN/><AUTOWRAP></ATTRIBUTE></HIDE></PASTE>""")
