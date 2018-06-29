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

"""Tests for tests.lib.command_capture."""

from __future__ import absolute_import
from __future__ import unicode_literals
import io
import os
import StringIO
import subprocess
import sys

from googlecloudsdk.core import execution_utils
from tests.lib import command_capture
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock


class CommandCaptureTestBase(command_capture.WithCommandCapture,
                             sdk_test_base.WithTempCWD):
  """Base class for command capture tests that sets up common resources."""

  def SetUp(self):
    self.testdata = self.Resource('tests', 'unit', 'tests_lib', 'testdata')
    ending = ('cmd' if test_case.Filters.IsOnWindows() else 'sh')
    self.program = os.path.join(self.testdata, 'test.' + ending)

  def AssertCaptureEquals(self, stdin='', stdout='', stderr=''):
    """Assert an exact capture from this test."""
    self.AssertCommandInputEquals(stdin)
    self.AssertCommandOutputEquals(stdout)
    self.AssertCommandErrEquals(stderr)


class CommandCaptureTest(CommandCaptureTestBase):
  """Tests a number of common ways to capture I/O."""

  def testCaptureWithPipes(self):
    """Make sure pipes are enabling regular I/O with communicate."""
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(input='test input')
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\n',
        stderr='test error\n')
    self.assertMultiLineEqual(out, 'test input\ntest output\n')
    self.assertMultiLineEqual(err, 'test error\n')

  def testCaptureWithoutPipes(self):
    """No pipes assigned means to use default I/O, but capture should work."""
    p = subprocess.Popen(self.program)
    out, err = p.communicate('discard!\n')
    self.AssertCaptureEquals(
        stdin='',  # Never captured
        stdout='\ntest output\n',  # So.. Not present here either
        stderr='test error\n')
    self.assertIsNone(out)
    self.assertIsNone(err)

  def testCaptureWithCloseFds(self):
    """The `close_fds` arg does not play well with Windows and pipes."""
    p = subprocess.Popen(self.program, close_fds=True)
    out, err = p.communicate()
    self.AssertCaptureEquals(
        stdin='',  # Never captured
        stdout='\ntest output\n',  # So.. Not present here either
        stderr='test error\n')
    self.assertIsNone(out)
    self.assertIsNone(err)

  def testCaptureWithPipesStderrRedirect(self):
    """Make sure the special case `stderr=subprocess.STDOUT` is respected."""
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = p.communicate(input='test input')
    # NOTE: The redirect directive affects both actual output and capture.
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\ntest error\n',
        stderr='')
    self.assertMultiLineEqual(out, 'test input\ntest output\ntest error\n')
    self.assertIsNone(err)

  def testOtherPopenMethods(self):
    """Makes sure other Popen methods works as they should."""
    p = subprocess.Popen(self.program)
    self.assertEqual(p.wait(), 1)
    self.assertEqual(p.returncode, 1)
    self.AssertCaptureEquals(
        stdin='',
        stdout='\ntest output\n',
        stderr='test error\n')

  def testMultipleCommunicateCalls(self):
    """Calling communicate multiple times raises a runtime error."""
    p = subprocess.Popen(self.program)
    p.communicate()
    with self.assertRaises(RuntimeError):
      p.communicate()

  def testCaptureWithFileObjects(self):
    """Make sure file object capture works properly."""
    with io.open('in', 'wt') as fp:
      fp.write('test input')
    with io.open('in', 'rt') as i_f:
      with io.open('out', 'wt') as of:
        with io.open('err', 'wt') as ef:
          p = subprocess.Popen(self.program, stdin=i_f, stdout=of, stderr=ef)
          p.communicate()
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\n',
        stderr='test error\n')
    self.AssertFileEquals('test input\ntest output\n', 'out')
    self.AssertFileEquals('test error\n', 'err')

  def testCaptureWithFileObjectsStderrRedirect(self):
    """The special case `stderr=subprocess.STDOUT` is respected with files."""
    with io.open('out', 'wt') as of:
      p = subprocess.Popen(self.program, stdin=subprocess.PIPE, stdout=of,
                           stderr=subprocess.STDOUT)
      p.communicate('test input')
    # NOTE: The redirect directive affects both actual output and capture.
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\ntest error\n',
        stderr='')
    self.AssertFileEquals('test input\ntest output\ntest error\n', 'out')

  def testCaptureWithFileDescriptors(self):
    """Make sure file descriptor capture works properly."""
    with io.open('in', 'wt') as fp:
      fp.write('test input')
    i_fd = os.open('in', os.O_RDONLY)
    o_fd = os.open('out', os.O_CREAT | os.O_WRONLY)
    e_fd = os.open('err', os.O_CREAT | os.O_WRONLY)
    p = subprocess.Popen(self.program, stdin=i_fd, stdout=o_fd, stderr=e_fd)
    p.communicate()
    for fd in (i_fd, o_fd, e_fd):
      os.close(fd)
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\n',
        stderr='test error\n')
    self.AssertFileEquals('test input\ntest output\n', 'out')
    self.AssertFileEquals('test error\n', 'err')

  def testCaptureWithExecutionUtils(self):
    """Capture with googlecloudsdk.core.execution_utils.Exec."""
    out_func = mock.Mock()
    err_func = mock.Mock()
    return_code = execution_utils.Exec(
        [self.program], no_exit=True,
        out_func=out_func, err_func=err_func, in_str='test input')
    self.assertEqual(return_code, 1)

    # Output is returned unprocessed from the call, so they will have OS
    # specific newlines.
    out_func.assert_called_once_with('test input\ntest output\n')
    err_func.assert_called_once_with('test error\n')
    self.AssertCaptureEquals(
        stdin='test input',
        stdout='test input\ntest output\n',
        stderr='test error\n')

  def testCaptureMultipleCommands(self):
    """Run multiple commands, get and clear the captures."""

    # Empty at first
    self.assertMultiLineEqual(self.GetCommandInput(), '')
    self.assertMultiLineEqual(self.GetCommandOutput(), '')
    self.assertMultiLineEqual(self.GetCommandErr(), '')

    # Run a command
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate(input='test input')

    # Make sure it's captured verbatim
    self.assertMultiLineEqual(self.GetCommandInput(), 'test input')
    self.assertMultiLineEqual(self.GetCommandOutput(),
                              'test input\ntest output\n')
    self.assertMultiLineEqual(self.GetCommandErr(), 'test error\n')

    # Run another command
    p.wait()
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate(input='other input')

    # Check that output is appended to previous output
    self.assertMultiLineEqual(self.GetCommandInput(), 'test inputother input')
    self.assertMultiLineEqual(
        self.GetCommandOutput(),
        'test input\ntest output\nother input\ntest output\n')
    self.assertMultiLineEqual(self.GetCommandErr(), 'test error\n' * 2)

    # Clear buffers
    self.ClearCommandInput()
    self.ClearCommandOutput()
    self.ClearCommandErr()

    # Make sure they were properly emptied
    self.assertMultiLineEqual(self.GetCommandInput(), '')
    self.assertMultiLineEqual(self.GetCommandOutput(), '')
    self.assertMultiLineEqual(self.GetCommandErr(), '')

  def testCaptureShowCommandOutput(self):
    """Check that displaying of command output is printed to stderr."""
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate(input='test input')
    self.ShowCommandOutput()

    # Mock out `sys.__stderr__` with string buffer
    # CAUTION: Point of no return if we lose `sys.__stderr__`
    err_cap = StringIO.StringIO()
    self.StartObjectPatch(sys, '__stderr__', new=err_cap)

    self.TearDown()  # Force output dump, will also stop object patches
    expected = (
        'Captured command.stdin: <<<test input>>>\n'
        'Captured command.stdout: <<<test input\ntest output\n>>>\n'
        'Captured command.stderr: <<<test error\n>>>\n')
    self.assertMultiLineEqual(err_cap.getvalue(), expected)

  def testOriginalPopen(self):
    """Check that original Popen still works as intended."""
    p = self.orig_popen(self.program, stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(input='test input')
    self.AssertCaptureEquals('', '', '')
    self.assertMultiLineEqual(out, 'test input\ntest output\n')
    self.assertMultiLineEqual(err, 'test error\n')


class CommandCaptureAssertionsTest(CommandCaptureTestBase):
  """Tests assertions for command I/O variants."""

  def SetUp(self):
    """Runs a program that populates the captured streams."""
    # Note that this relies on that CommandCaptureTestBase.SetUp has been
    # executed prior.
    p = subprocess.Popen(self.program, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate(input='test input')

  def testEquals(self):
    """AssertCommand*Equals variants."""
    self.AssertCommandInputEquals('test input')
    self.AssertCommandOutputEquals('test input\ntest output\n')
    self.AssertCommandErrEquals('test error\n')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputEquals('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputEquals('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrEquals('bogus')

  def testNotEquals(self):
    """AssertCommand*Equals variants."""
    self.AssertCommandInputNotEquals('bogus')
    self.AssertCommandOutputNotEquals('bogus')
    self.AssertCommandErrNotEquals('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputNotEquals('test input')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputNotEquals('test input\ntest output\n')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrNotEquals('test error\n')

  def testContains(self):
    """AssertCommand*Contains variants."""
    self.AssertCommandInputContains('st inp')
    self.AssertCommandOutputContains('st input\ntest outp')
    self.AssertCommandErrContains('st err')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputContains('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputContains('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrContains('bogus')

  def testNotContains(self):
    """AssertCommand*NotContains variants."""
    self.AssertCommandInputNotContains('bogus')
    self.AssertCommandOutputNotContains('bogus')
    self.AssertCommandErrNotContains('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputNotContains('st inp')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputNotContains('st input\ntest outp')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrNotContains('st err')

  def testMatches(self):
    """AssertCommand*Matches variants."""
    self.AssertCommandInputMatches('st.*np')
    self.AssertCommandOutputMatches('st inp.+\ntest outp')
    self.AssertCommandErrMatches(r'st\s?error')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputMatches('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputMatches('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrMatches('bogus')

  def testNotMatches(self):
    """AssertCommand*NotMatches variants."""
    self.AssertCommandInputNotMatches('bogus')
    self.AssertCommandOutputNotMatches('bogus')
    self.AssertCommandErrNotMatches('bogus')
    with self.assertRaises(AssertionError):
      self.AssertCommandInputNotMatches('st.*np')
    with self.assertRaises(AssertionError):
      self.AssertCommandOutputNotMatches('st inp.+\ntest outp')
    with self.assertRaises(AssertionError):
      self.AssertCommandErrNotMatches(r'st\s?error')

if __name__ == '__main__':
  test_case.main()
