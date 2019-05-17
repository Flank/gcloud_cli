# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

# Tests for the console_io module.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import subprocess
import sys
import textwrap

from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import console_pager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class StdinTests(sdk_test_base.SdkBase, test_case.WithInput):

  def testFileRead(self):
    filename = self.Touch(self.temp_path, contents='abc123')
    contents = console_io.ReadFromFileOrStdin(filename, binary=False)
    self.assertEqual(contents, 'abc123')

  def testFileReadBinary(self):
    filename = self.Touch(
        self.temp_path,
        contents=b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')
    contents = console_io.ReadFromFileOrStdin(filename, binary=True)
    self.assertEqual(
        contents,
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')

  def testStdinRead(self):
    self.WriteInput('abc123')
    self.assertEqual(
        console_io.ReadFromFileOrStdin('-', binary=False), 'abc123\n')

  def testStdinReadBinary(self):
    self.WriteBinaryInput(
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')
    self.assertEqual(
        console_io.ReadFromFileOrStdin('-', binary=True),
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')


class PrompterTests(test_case.WithOutputCapture, test_case.WithInput):

  def SetAnswers(self, *lines):
    """Writes lines to input and returns number of entries."""
    self.WriteInput(*lines)
    return len(lines)

  def SetUp(self):
    """Disables prompts."""
    properties.VALUES.core.disable_prompts.Set(False)
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)

  def testNoPrompt(self):
    properties.VALUES.core.disable_prompts.Set(True)
    result = console_io.PromptContinue(message='prompt')
    self.assertEqual('', self.GetErr())
    self.assertTrue(result)
    result = console_io.PromptContinue(default=False)
    self.assertFalse(result)
    result = console_io.PromptResponse(message='prompt')
    self.assertEqual('', self.GetErr())
    self.assertEqual(result, None)
    result = console_io.PromptWithDefault(message='prompt')
    self.assertEqual('', self.GetErr())
    self.assertEqual(result, None)
    result = console_io.PromptChoice(['a', 'b', 'c'])
    self.assertEqual('', self.GetErr())
    self.assertEqual(result, None)

  def testEOF(self):
    result = console_io.PromptContinue()
    self.assertTrue(result)
    result = console_io.PromptContinue(default=False)
    self.assertFalse(result)
    with self.assertRaisesRegex(console_io.UnattendedPromptError,
                                'This prompt could not be answered'):
      result = console_io.PromptContinue(throw_if_unattended=True)
    result = console_io.PromptResponse(message='')
    self.assertEqual(result, None)
    result = console_io.PromptWithDefault(message='')
    self.assertEqual(result, None)
    result = console_io.PromptChoice(['a', 'b', 'c'])
    self.assertEqual(result, None)
    result = console_io.PromptChoice(['a', 'b', 'c'], default=2)
    self.assertEqual(result, 2)

  def testIsInteractiveOutput(self):
    self.StartObjectPatch(sys.stdin, 'isatty').return_value = True
    stdout_mock = self.StartObjectPatch(sys.stdout, 'isatty')
    stdout_mock.return_value = False
    self.assertFalse(console_io.IsInteractive(output=True))
    stdout_mock.return_value = True
    self.assertTrue(console_io.IsInteractive(output=True))

  def testIsInteractiveErr(self):
    self.StartObjectPatch(sys.stdin, 'isatty').return_value = True
    stderr_mock = self.StartObjectPatch(sys.stderr, 'isatty')
    stderr_mock.return_value = False
    self.assertFalse(console_io.IsInteractive(output=True))
    stderr_mock.return_value = True
    self.assertTrue(console_io.IsInteractive(error=True))

  @test_case.Filters.DoNotRunOnWindows
  def testIsFromShellScript(self):
    self.StartObjectPatch(
        platforms.OperatingSystem,
        'Current').return_value = platforms.OperatingSystem.LINUX
    self.StartObjectPatch(os, 'getppid').return_value = 12345
    self.StartObjectPatch(os, 'getpgrp').return_value = 12345
    self.assertTrue(console_io.IsRunFromShellScript())
    self.StartObjectPatch(os, 'getpgrp').return_value = 12346
    self.assertFalse(console_io.IsRunFromShellScript())
    self.StartObjectPatch(
        platforms.OperatingSystem,
        'Current').return_value = platforms.OperatingSystem.WINDOWS
    self.assertFalse(console_io.IsRunFromShellScript())

  def testEOFInteractive(self):
    self.StartObjectPatch(console_io, 'IsInteractive').return_value = True
    result = console_io.PromptContinue()
    self.assertTrue(result)

  def testPromptYes(self):
    num = self.SetAnswers('y', 'Y', 'yes', 'YES', 'yEs', 'y ', 'Y ', ' y', '')
    for _ in range(num):
      result = console_io.PromptContinue(message='prompt', cancel_on_no=False)
      self.assertIn('prompt', self.GetErr())
      self.assertTrue(result)
    num = self.SetAnswers('y', 'Y', 'yes', 'YES', 'yEs', 'y ', 'Y ', ' y', '')
    for _ in range(num):
      result = console_io.PromptContinue(message='prompt', cancel_on_no=True)
      self.assertIn('prompt', self.GetErr())
      self.assertTrue(result)

  def testPromptNo(self):
    num = self.SetAnswers('n', 'N', 'no', 'NO', 'No', 'n ', 'N ', ' n')
    for _ in range(num):
      result = console_io.PromptContinue(message='prompt', cancel_on_no=False)
      self.assertIn('prompt', self.GetErr())
      self.assertFalse(result)
    num = self.SetAnswers('n', 'N', 'no', 'NO', 'No', 'n ', 'N ', ' n')
    for _ in range(num):
      with self.assertRaisesRegex(
          console_io.OperationCancelledError, 'Aborted by user.'):
        console_io.PromptContinue(message='prompt', cancel_on_no=True)
      self.assertIn('prompt', self.GetErr())

  def testPromptCancelMessage(self):
    self.SetAnswers('n')
    with self.assertRaisesRegex(
        console_io.OperationCancelledError,
        "I'm sorry Dave, I'm afraid I can't do that"):
      console_io.PromptContinue(
          message='prompt', cancel_on_no=True,
          cancel_string="I'm sorry Dave, I'm afraid I can't do that")
      self.assertIn('prompt', self.GetErr())

  def testRepeatPrompt(self):
    self.SetAnswers('junk', 'y')
    result = console_io.PromptContinue(message='prompt', prompt_string='y/n')
    self.assertIn('prompt', self.GetErr())
    self.assertIn('y/n (Y/n)?  '
                  "Please enter 'y' or 'n':  ", self.GetErr())
    self.assertTrue(result)

  def testPromptWrapping(self):
    self.SetAnswers('y')
    result = console_io.PromptContinue(
        message='this is a long prompt that would have to wrap\nbut it has a '
        'line break in the middle.',
        prompt_string='this is another really long prompt that would have to '
        'wrap but it also has a line\nbreak in the middle')
    self.assertIn(
        'this is a long prompt that would have to wrap\n'
        'but it has a line break in the middle.\n\n'
        'this is another really long prompt that would have to wrap but it '
        'also\n'
        ' has a line\n'
        'break in the middle (Y/n)?  ', self.GetErr())
    self.assertTrue(result)

  def testPromptResponse(self):
    self.SetAnswers('a string', 'a sentence.', '')
    result = console_io.PromptResponse(message='message')
    self.assertIn('message', self.GetErr())
    self.assertEqual(result, 'a string')
    result = console_io.PromptResponse(message='message')
    self.assertEqual(result, 'a sentence.')
    result = console_io.PromptResponse(message='message')
    self.assertEqual(result, '')

  def testPromptWithDefault(self):
    self.SetAnswers('', 'user value')
    result = console_io.PromptWithDefault(message='message',
                                          default='default value')
    self.assertIn('message (default value):  ', self.GetErr())
    self.assertEqual(result, 'default value')
    result = console_io.PromptWithDefault(message='message',
                                          default='default value')
    self.assertEqual(result, 'user value')

    # Test without a default.
    self.SetAnswers('', 'user value')
    result = console_io.PromptWithDefault(message='message')
    self.assertIn('message:  ', self.GetErr())
    self.assertEqual(result, None)
    result = console_io.PromptWithDefault(message='message')
    self.assertEqual(result, 'user value')

  def testPromptAbortIfPromptsDisabledAndDefaultNoAndCancelOnNo(self):
    properties.VALUES.core.disable_prompts.Set(True)
    with self.assertRaises(console_io.OperationCancelledError):
      console_io.PromptContinue(message='msg', default=False, cancel_on_no=True)

    result = console_io.PromptContinue(message='msg',
                                       default=True,
                                       cancel_on_no=True)
    self.assertTrue(result)

  def testTextSelection(self):
    self.SetAnswers('1', 'a', '2', 'b', '3', 'c', 'd')
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(textwrap.dedent("""\
        message
         [1] a
         [2] b
         [3] c
        prompt:  \n\
        """), self.GetErr())
    self.assertEqual(result, 0)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, 0)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, 1)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, 1)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, 2)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, 2)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True)
    self.assertEqual(result, None)

  def testTextSelectionWithCancelOption(self):
    self.SetAnswers('1', 'a', '4', 'cancel')

    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True,
                                     cancel_option=True)
    self.assertIn(textwrap.dedent("""\
        message
         [1] a
         [2] b
         [3] c
         [4] cancel
        """), self.GetErr())
    self.assertIn('prompt:  \n', self.GetErr())
    self.assertEqual(result, 0)
    result = console_io.PromptChoice(['a', 'b', 'c'],
                                     message='message',
                                     prompt_string='prompt',
                                     allow_freeform=True,
                                     cancel_option=True)
    self.assertEqual(result, 0)

    with self.assertRaises(console_io.OperationCancelledError):
      console_io.PromptChoice(['a', 'b', 'c'],
                              message='message',
                              prompt_string='prompt',
                              allow_freeform=True,
                              cancel_option=True)
    with self.assertRaises(console_io.OperationCancelledError):
      console_io.PromptChoice(['a', 'b', 'c'],
                              message='message',
                              prompt_string='prompt',
                              allow_freeform=True,
                              cancel_option=True)

  def testLongPrompt(self):
    self.SetAnswers('list', '1', 'value10', '1', '2', '3', '1', '101')

    indices = list(range(1, 101))
    values = ['value{x}'.format(x=x) for x in indices]

    options_lines = [' [{index}] {value}'.format(index=index, value=value)
                     for (index, value) in zip(indices, values)]

    result = console_io.PromptChoice(values, allow_freeform=True)

    expected = '\n'.join(options_lines[:console_io.PROMPT_OPTIONS_OVERFLOW])

    remaining = len(options_lines) - console_io.PROMPT_OPTIONS_OVERFLOW

    self.assertIn(expected, self.GetErr())

    self.assertIn(('Did not print [{remaining}] options.\n'
                   'Too many options [{total}]. Enter "list" at prompt to '
                   'print choices fully.\nPlease enter numeric choice or '
                   'text value (must exactly match list \nitem):').format(
                       remaining=remaining,
                       total=len(options_lines)
                   ),
                  self.GetErr())

    options_lines = [' [{index}] {value}'.format(index=index, value=value)
                     for (index, value) in zip(indices, values)]

    expected = '\n'.join(options_lines)

    self.assertIn(expected, self.GetErr())

    self.assertEqual(result, 0)

    result = console_io.PromptChoice(values, allow_freeform=True)
    self.assertEqual(result, 9)

    result = console_io.PromptChoice(values, allow_freeform=True)
    self.assertEqual(result, 0)

    result = console_io.PromptChoice(values, allow_freeform=True)
    self.assertEqual(result, 1)

    result = console_io.PromptChoice(values, allow_freeform=True)
    self.assertEqual(result, 2)

    result = console_io.PromptChoice(values, allow_freeform=True,
                                     cancel_option=True)
    self.assertEqual(result, 0)

    with self.assertRaises(console_io.OperationCancelledError):
      result = console_io.PromptChoice(values,
                                       allow_freeform=True,
                                       cancel_option=True)

  def testChoice(self):
    self.SetAnswers('2', '1', '', '', '')
    result = console_io.PromptChoice(
        ['a', 'b', 'c'], default=2, message='message', prompt_string='prompt')
    self.assertIn(textwrap.dedent("""\
        message
         [1] a
         [2] b
         [3] c
        """), self.GetErr())
    self.assertIn('prompt (3):  \n', self.GetErr())
    self.assertEqual(result, 1)
    result = console_io.PromptChoice(['a', 'b', 'c'], default=2)
    self.assertEqual(result, 0)
    result = console_io.PromptChoice(['a', 'b', 'c'], default=2)
    self.assertEqual(result, 2)
    with self.assertRaises(console_io.OperationCancelledError):
      console_io.PromptChoice(['a', 'b', 'c'], default=3, cancel_option=True)

  def testRepeatChoice(self):
    self.SetAnswers('junk', '1.5', '', '-1', '4', '2')
    result = console_io.PromptChoice(
        ['a', 'b', 'c'], message='message', prompt_string='prompt')
    self.assertIn(textwrap.dedent("""\
        message
         [1] a
         [2] b
         [3] c
        """), self.GetErr())
    self.assertIn('prompt:  '
                  'Please enter a value between 1 and 3:  '
                  'Please enter a value between 1 and 3:  '
                  'Please enter a value between 1 and 3:  '
                  'Please enter a value between 1 and 3:  ',
                  self.GetErr())
    self.assertIn('prompt:  ', self.GetErr())
    self.assertEqual(result, 1)

  def testChoiceErrors(self):
    with self.assertRaisesRegex(ValueError, r'at least one option'):
      console_io.PromptChoice([])
    with self.assertRaisesRegex(ValueError, r'at least one option'):
      console_io.PromptChoice(None)
    with self.assertRaisesRegex(
        ValueError, r'Default option \[-1\] is not a valid index '):
      console_io.PromptChoice(['a', 'b', 'c'], default=-1)
    with self.assertRaisesRegex(
        ValueError, r'Default option \[3\] is not a valid index'):
      console_io.PromptChoice(['a', 'b', 'c'], default=3)

  def testCanPrompt(self):
    self.StartObjectPatch(console_io, 'IsInteractive').return_value = True
    self.assertTrue(console_io.CanPrompt())

    properties.VALUES.core.disable_prompts.Set(True)
    self.assertFalse(console_io.CanPrompt())

  def testCantPrompt(self):
    self.StartObjectPatch(console_io, 'IsInteractive').return_value = False
    self.assertFalse(console_io.CanPrompt())

  def testPromptWithValidator(self):
    def simple_validator(s):
      return len(s) > 3
    self.SetAnswers('1', '1234')
    result = console_io.PromptWithValidator(simple_validator,
                                            'error', 'prompt', 'message')
    self.assertIn('message', self.GetErr())
    self.assertIn('prompt', self.GetErr())
    self.assertIn('error', self.GetErr())
    self.assertEqual(result, '1234')


class ProgressBarTests(sdk_test_base.WithOutputCapture):

  class BoxLine(console_attr.BoxLineCharacters):
    """ASCII Box/line drawing characters with unique corner/junction chars ."""
    dl = 'B'
    dr = 'A'
    h = '-'
    hd = '+'
    hu = '+'
    ul = 'F'
    ur = 'E'
    v = '|'
    vh = '+'
    vl = 'D'
    vr = 'C'
    d_dl = '2'
    d_dr = '1'
    d_h = '='
    d_hd = '#'
    d_hu = '#'
    d_ul = '6'
    d_ur = '5'
    d_v = '#'
    d_vh = '#'
    d_vl = '4'
    d_vr = '3'

  def SetUp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetBoxLineCharacters').side_effect = self.BoxLine
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    self._interactive_mock.return_value = True

  def testNoOp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.OFF.name)
    pb = console_io.ProgressBar('Test Action', total_ticks=40)
    pb.Start()
    pb.Finish()
    self.AssertErrEquals('')

  def testStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    pb = console_io.ProgressBar('Test Action', total_ticks=40)
    pb.Start()
    pb.Finish()
    self.AssertErrEquals('{"ux": "PROGRESS_BAR", "message": "Test Action"}\n')

  def testProgressBarSingle(self):
    pb = console_io.ProgressBar('Test Action', total_ticks=40)
    self.AssertErrNotContains('|')
    pb.Start()
    self.AssertErrContains(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5')

    pb.SetProgress(.25)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5==========')

    pb.SetProgress(.15)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5==========')

    pb.SetProgress(.26)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5==========')

    pb.SetProgress(.49)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5===================')

    pb.SetProgress(.50)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5====================')

    pb.SetProgress(1)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5========================================6\n')

    # Should just stay at 100%.
    pb.SetProgress(2)
    self.AssertErrEquals(
        '1========================================2\n'
        '3= Test Action                          =4\n'
        '5========================================6\n')

  def testProgressBarStack(self):
    actions = ['Uninstalling', 'Downloading', 'Installing']
    for index, action in enumerate(actions):
      pb = console_io.ProgressBar(action, total_ticks=40, first=index == 0,
                                  last=index == len(actions) - 1)
      pb.Start()
      pb.Finish()

    self.AssertErrEquals(
        '1========================================2\n'
        '3= Uninstalling                         =4\n'
        '5========================================6\r'
        '3========================================4\n'
        '3= Downloading                          =4\n'
        '5========================================6\r'
        '3========================================4\n'
        '3= Installing                           =4\n'
        '5========================================6\n')

  def testProgressBarStackNonInteractive(self):
    """Don't redraw when non-interactive."""
    self._interactive_mock.return_value = False
    actions = ['Uninstalling', 'Downloading', 'Installing']
    for index, action in enumerate(actions):
      pb = console_io.ProgressBar(action, total_ticks=40, first=index == 0,
                                  last=index == len(actions) - 1)
      pb.Start()
      pb.Finish()

    self.AssertErrEquals(
        '1========================================2\n'
        '3= Uninstalling                         =4\n'
        '5========================================6\n'
        '1========================================2\n'
        '3= Downloading                          =4\n'
        '5========================================6\n'
        '1========================================2\n'
        '3= Installing                           =4\n'
        '5========================================6\n')

  def testProgressBarLabel(self):
    pb = console_io.ProgressBar('Test Action', total_ticks=15)
    pb.Start()
    self.AssertErrContains('3= Test Action =4\n')

    self.ClearErr()
    pb = console_io.ProgressBar('Test Action', total_ticks=14)
    pb.Start()
    self.AssertErrContains('3= Test Ac... =4\n')

  def testProgressBarContextManager(self):
    with console_io.ProgressBar('Test Action', total_ticks=15):
      pass
    self.AssertErrEquals('1===============2\n'
                         '3= Test Action =4\n'
                         '5===============6\n')

  def testSplit(self):
    with console_io.ProgressBar('', total_ticks=10) as pb:
      callbacks = console_io.SplitProgressBar(pb.SetProgress, [.1, .4, .5])
      self.assertEqual(3, len(callbacks))
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')
      callbacks[0](.5)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')
      callbacks[0](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5=')
      callbacks[1](.5)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5===')
      callbacks[1](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5=====')
      callbacks[2](.5)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5=======')
      callbacks[2](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5==========6\n')

  def testSplitWholeNumbers(self):
    with console_io.ProgressBar('', total_ticks=12) as pb:
      callbacks = console_io.SplitProgressBar(pb.SetProgress, [1, 2, 3])
      self.assertEqual(3, len(callbacks))
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5')
      callbacks[0](.5)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5=')
      callbacks[0](1)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5==')
      callbacks[1](.5)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5====')
      callbacks[1](1)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5======')
      callbacks[2](.5)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5=========')
      callbacks[2](1)
      self.AssertErrEquals('1============2\n'
                           '3=          =4\n'
                           '5============6\n')

  def testDefault(self):
    with console_io.ProgressBar('', total_ticks=10):
      callbacks = console_io.SplitProgressBar(None, [.1, .4, .5])
      self.assertEqual(3, len(callbacks))
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')
      callbacks[0](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')
      callbacks[1](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')
      callbacks[2](1)
      self.AssertErrEquals('1==========2\n'
                           '3=        =4\n'
                           '5')


class ProgressBarAsciiArtTests(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    self._interactive_mock.return_value = True

  def testProgressBarAsciiArtSingle(self):
    pb = console_io.ProgressBar('Test Action', total_ticks=40)
    self.AssertErrNotContains('|')
    pb.Start()
    self.AssertErrContains(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#')

    pb.SetProgress(.25)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#==========')

    pb.SetProgress(.15)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#==========')

    pb.SetProgress(.26)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#==========')

    pb.SetProgress(.49)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#===================')

    pb.SetProgress(.50)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#====================')

    pb.SetProgress(1)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#========================================#\n')

    # Should just stay at 100%.
    pb.SetProgress(2)
    self.AssertErrEquals(
        '#========================================#\n'
        '#= Test Action                          =#\n'
        '#========================================#\n')

  def testProgressBarAsciiArtStack(self):
    actions = ['Uninstalling', 'Downloading', 'Installing']
    for index, action in enumerate(actions):
      pb = console_io.ProgressBar(action, total_ticks=40, first=index == 0,
                                  last=index == len(actions) - 1)
      pb.Start()
      pb.Finish()

    self.AssertErrEquals(
        '#========================================#\n'
        '#= Uninstalling                         =#\n'
        '#========================================#\n'
        '#= Downloading                          =#\n'
        '#========================================#\n'
        '#= Installing                           =#\n'
        '#========================================#\n')

  def testProgressBarAsciiArtStackNonInteractive(self):
    """Don't make double lines when the char set is ascii."""
    self._interactive_mock.return_value = False
    actions = ['Uninstalling', 'Downloading', 'Installing']
    for index, action in enumerate(actions):
      pb = console_io.ProgressBar(action, total_ticks=40, first=index == 0,
                                  last=index == len(actions) - 1)
      pb.Start()
      pb.Finish()

    self.AssertErrEquals(
        '#========================================#\n'
        '#= Uninstalling                         =#\n'
        '#========================================#\n'
        '#= Downloading                          =#\n'
        '#========================================#\n'
        '#= Installing                           =#\n'
        '#========================================#\n')

  def testProgressBarScreenReader(self):
    pb = console_io.ProgressBar('Test Action', screen_reader=True)
    pb.Start()
    self.AssertErrEquals('Test Action\n')
    pb.SetProgress(0.02)
    self.AssertErrEquals('Test Action\n')
    pb.SetProgress(0.33)
    self.AssertErrEquals('Test Action\n33%\n')
    pb.Finish()
    self.AssertErrEquals('Test Action\n33%\n100%\n')


class TickableProgressBarTests(sdk_test_base.WithOutputCapture):

  class BoxLine(console_attr.BoxLineCharacters):
    """ASCII Box/line drawing characters with unique corner/junction chars ."""
    dl = 'B'
    dr = 'A'
    h = '-'
    hd = '+'
    hu = '+'
    ul = 'F'
    ur = 'E'
    v = '|'
    vh = '+'
    vl = 'D'
    vr = 'C'
    d_dl = '2'
    d_dr = '1'
    d_h = '='
    d_hd = '#'
    d_hu = '#'
    d_ul = '6'
    d_ur = '5'
    d_v = '#'
    d_vh = '#'
    d_vl = '4'
    d_vr = '3'

  def SetUp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetBoxLineCharacters').side_effect = self.BoxLine
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive',
                                                   return_value=True)

  def testProgressBar(self):
    with console_io.TickableProgressBar(4, 'Test Action', total_ticks=40) as pb:
      self.AssertErrNotContains('|')
      self.AssertErrContains(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5')

      pb.Tick()
      self.AssertErrEquals(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5==========')

      pb.Tick()
      self.AssertErrEquals(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5====================')

      pb.Tick()
      self.AssertErrEquals(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5==============================')

      pb.Tick()
      self.AssertErrEquals(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5========================================6\n')

      # Should just stay at 100%.
      pb.Tick()
      self.AssertErrEquals(
          '1========================================2\n'
          '3= Test Action                          =4\n'
          '5========================================6\n')


class MoreThePagerTests(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.StartEnvPatch({})
    encoding.SetEncodedValue(os.environ, 'LESS', None)
    encoding.SetEncodedValue(os.environ, 'PAGER', None)
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath').side_effect = self.MockFindExecutableOnPath
    self.StartObjectPatch(
        console_io, 'IsInteractive', side_effect=self.MockIsInteractive)
    self.StartObjectPatch(
        console_pager.Pager, 'Run', side_effect=self.MockRun)
    self.popen = self.StartObjectPatch(
        subprocess, 'Popen', side_effect=self.MockPopen)
    self.executables = True
    self.interactive = True
    self.less_env = None
    self.ran = False
    self.raw_chars = None
    self.contents = 'Here\nlies\nLes\nMoore.\nNo\nLes\nno\nmore.'

  def MockRun(self):
    self.ran = True

  def MockFindExecutableOnPath(self, command):
    return self.executables

  def MockIsInteractive(self, output=False, error=False):
    return self.interactive

  def MockPopen(self, *args, **kwargs):
    self.less_env = os.environ.get('LESS')
    return mock.MagicMock()

  def SetExecutables(self, executables):
    self.executables = executables

  def SetInteractive(self, interactive):
    self.interactive = interactive

  def testNotInteractive(self):
    self.SetInteractive(False)
    console_io.More(self.contents)
    self.AssertOutputEquals(self.contents)
    self.assertFalse(self.ran)

  def testInternalPagerDefault(self):
    self.SetExecutables(False)
    console_io.More(self.contents)
    self.assertTrue(self.ran)

  def testInternalPagerEnviron(self):
    os.environ['PAGER'] = '-'
    console_io.More(self.contents)
    self.assertTrue(self.ran)

  def testInternalPagerKWarg(self):
    console_io.More(self.contents, check_pager=False)
    self.assertTrue(self.ran)

  def testExternalPagerDefaultWithNoLess(self):
    console_io.More(self.contents)
    self.popen.assert_called_once_with('less', stdin=subprocess.PIPE,
                                       shell=True)
    self.assertFalse(self.ran)
    self.assertEqual('-R', self.less_env)

  def testExternalPagerDefaultWithLess(self):
    encoding.SetEncodedValue(os.environ, 'LESS', '-Z')
    console_io.More(self.contents)
    self.popen.assert_called_once_with('less', stdin=subprocess.PIPE,
                                       shell=True)
    self.assertFalse(self.ran)
    self.assertEqual('-R-Z', self.less_env)

  def testExternalPagerEnviron(self):
    encoding.SetEncodedValue(os.environ, 'PAGER', 'more')
    console_io.More(self.contents)
    self.popen.assert_called_once_with('more', stdin=subprocess.PIPE,
                                       shell=True)
    self.assertFalse(self.ran)


class LazyFormatTests(test_case.Base):

  def testLazyFormatNoVars(self):
    fmt = 'This is a test with no vars.'
    expected = fmt
    actual = console_io.LazyFormat(fmt, test='TEST')
    self.assertEqual(expected, actual)

  def testLazyFormatOneVar(self):
    fmt = 'This is a {test} with one var.'
    expected = 'This is a TEST with one var.'
    actual = console_io.LazyFormat(fmt, test='TEST')
    self.assertEqual(expected, actual)

  def testLazyFormatOneCallable(self):
    fmt = 'This is a {test} with one var.'
    expected = 'This is a TEST with one var.'
    actual = console_io.LazyFormat(fmt, test=lambda: 'TEST')
    self.assertEqual(expected, actual)

  def testLazyFormatOneVarOneUndefined(self):
    fmt = 'This is a {test} with one var one {undefined}.'
    expected = 'This is a TEST with one var one {undefined}.'
    actual = console_io.LazyFormat(fmt, test='TEST')
    self.assertEqual(expected, actual)

  def testLazyFormatOneVarExplicitQuote(self):
    fmt = 'This is a {test} with one var and an {{explicit}} {{quote}}.'
    expected = 'This is a TEST with one var and an {explicit} {quote}.'
    actual = console_io.LazyFormat(fmt, test='TEST', explicit='EXPLICIT')
    self.assertEqual(expected, actual)

  def testLazyFormatOneVarAndImplicitBraces(self):
    fmt = 'This { : is a {test} ? } with { one } var.'
    expected = 'This { : is a TEST ? } with { one } var.'
    actual = console_io.LazyFormat(fmt, test='TEST', one='ONE')
    self.assertEqual(expected, actual)

  def testLazyFormatUnbalancedBrace(self):
    fmt = '{foo'
    expected = fmt
    actual = console_io.LazyFormat(fmt, test='TEST', one='ONE')
    self.assertEqual(expected, actual)

  def testLazyFormatLotsOfBraces(self):
    fmt = '{{}'
    expected = fmt
    actual = console_io.LazyFormat(fmt, test='TEST', one='ONE')
    self.assertEqual(expected, actual)

  def testLazyFormatExplicitDoubleQuote(self):
    fmt = '} {one} {{two}} {'
    expected = '} ONE {two} {'
    actual = console_io.LazyFormat(fmt, one='ONE', two='TWO', three='THREE')
    self.assertEqual(expected, actual)

  def testLazyFormatListExample(self):
    fmt = "--dict-flag=^:^a=b,c:d=f,g # => {'a: 'b,c', 'd': 'f,g'}"
    expected = fmt
    actual = console_io.LazyFormat(fmt, one='ONE', two='TWO', three='THREE')
    self.assertEqual(expected, actual)

  def testLazyFormatNestedExpansion(self):
    fmt = 'exp:{text} lit:{{text}} nest-exp:{nest} nest-lit:{{nest}}'
    expected = 'exp:TEXT lit:{text} nest-exp:TEXT+{text} nest-lit:{nest}'
    actual = console_io.LazyFormat(fmt, text='TEXT', nest='{text}+{{text}}')
    self.assertEqual(expected, actual)


class UxlementTests(sdk_test_base.WithOutputCapture):

  def testJsonUXStubProgressBar(self):
    stub_output = console_io.JsonUXStub(console_io.UXElementType.PROGRESS_BAR,
                                        message='foo')
    self.assertEqual(stub_output, '{"ux": "PROGRESS_BAR", "message": "foo"}')

  def testJsonUXStubProgressTracker(self):
    stub_output = console_io.JsonUXStub(
        console_io.UXElementType.PROGRESS_TRACKER, message='foo',
        aborted_message='bar', status='FAILED')
    self.assertEqual(stub_output,
                     ('{"ux": "PROGRESS_TRACKER", "message": "foo",'
                      ' "aborted_message": "bar", "status": "FAILED"}'))

  def testJsonUXStubPromptResponse(self):
    stub_output = console_io.JsonUXStub(
        console_io.UXElementType.PROMPT_RESPONSE, message='asdf')
    self.assertEqual(stub_output,
                     '{"ux": "PROMPT_RESPONSE", "message": "asdf"}')

  def testJsonUXStubPromtpContinue(self):
    stub_output = console_io.JsonUXStub(
        console_io.UXElementType.PROMPT_CONTINUE,
        message='foo', prompt_string='continue?', cancel_string='cancelled')
    self.assertEqual(
        stub_output,
        ('{"ux": "PROMPT_CONTINUE", "message": "foo",'
         ' "prompt_string": "continue?", "cancel_string": "cancelled"}'))

  def testJsonUXStubPromptChoice(self):
    stub_output = console_io.JsonUXStub(
        console_io.UXElementType.PROMPT_CHOICE,
        prompt_string='pickone', choices=['1', '2', '3'])
    self.assertEqual(stub_output, (
        '{"ux": "PROMPT_CHOICE", '
        '"prompt_string": "pickone", "choices": ["1", "2", "3"]}'))

  def testJsonUXStubExtraArgsFails(self):
    with self.assertRaisesRegex(ValueError,
                                (r"Extraneous args for Ux Element "
                                 r"PROGRESS_BAR: \['not_allowed']")):
      console_io.JsonUXStub(console_io.UXElementType.PROGRESS_BAR,
                            message='foo', not_allowed='bar')

if __name__ == '__main__':
  test_case.main()
