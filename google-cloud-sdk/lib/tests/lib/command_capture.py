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

"""A base class for capturing child process I/O in the Cloud SDK.

NOTE: Use the alias `test_base.WithCommandCapture` rather than this module.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os
import subprocess
import sys

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms
from tests.lib import test_case

from six.moves import StringIO


class _PopenCapture(subprocess.Popen):
  """Wrapper for `subprocess.Popen` that intercepts I/O.

  This is an attempt at minimal side-effect subprocess command capture. It wraps
  the `Popen` constructor and intercepts I/O from and to the child process,
  while preserving the contract with the Popen user.

  NOTE: When using `stderr=subprocess.STDOUT`, `stdout_capture` will contain
  both the stdout and stderr captures (and `stderr_capture` will be empty).

  Not supported yet:
  - Async I/O (when `std*`-arguments refer to files or file descriptors).
  - Direct access to `self.std*` objects (discouraged by Python).

  Attributes:
    _orig_in: Original `stdin` parameter passed to constructor.
    _orig_out: Original `stdout` parameter passed to constructor.
    _orig_err: Original `stderr` parameter passed to constructor.
    _communicate_called: bool, True if communicate has been called.
  """

  # The I/O capture buffers
  stdin_capture = StringIO()
  stdout_capture = StringIO()
  stderr_capture = StringIO()

  def __init__(self, *args, **kwargs):
    """Override the `Popen` parent constructor, to intercept I/O.

    Args:
      *args: See `subprocess.Popen`.
      **kwargs: See `subprocess.Popen`.
    """
    # Be careful to not override any attributes used by the actual `Popen`.

    # Original arguments.
    self._orig_in = kwargs.get('stdin')
    self._orig_out = kwargs.get('stdout')
    self._orig_err = kwargs.get('stderr')

    # Needed because `Popen.communciate()` calls `Popen.wait()` under the hood.
    self._communicate_called = False
    kwargs['stdin'] = subprocess.PIPE
    kwargs['stdout'] = subprocess.PIPE
    if self._orig_err == subprocess.STDOUT:
      kwargs['stderr'] = subprocess.STDOUT
    else:
      kwargs['stderr'] = subprocess.PIPE
    if platforms.OperatingSystem.IsWindows():
      kwargs['close_fds'] = False
    # While in the Python process, we should always hold newlines as \n. This
    # converts \r\n from Windows processes into \n. When we write them out to
    # file Python will convert them back to the correct line endings for the
    # platform. If we don't do this, files we write on Windows end up with
    # \r\r\n because write() leaves \r alone and converts \n to \r\n.
    kwargs['universal_newlines'] = True

    # Call the real `Popen`, storing all relevant hidden and public state on
    # this very same object.
    super(_PopenCapture, self).__init__(*args, **kwargs)

  def _rewire(self, orig, captured):
    """Write to original output fd (if exists) and return user facing output.

    This is useful *after* the real process has executed. We have the captured
    output, and we have the original intent. Now we "rewire" such that (1) the
    user supplied file (or file descriptor) gets the output we captured, and (2)
    that the original intent is respected, so the (stdout, stderr) tuple is
    populated with the captured output *only if* the original file was
    `subprocess.PIPE`.

    Args:
      orig: None, subprocess.PIPE, fd or file object. The original stderr/stdout
        as given by the parameter to `Popen`.
      captured: str, Captured output from the actual command.

    Returns:
      str if orig is PIPE, else None. This corresponds to the string
        the user gets back from `communicate`, independent of what was actually
        captured by this class.
    """
    if orig == subprocess.PIPE:  # PIPE -> user wants output
      return captured
    elif orig == subprocess.STDOUT:
      # This means orig refers to stderr which is always None
      pass
    elif orig is None:  # Goes straight to stdout/stderr
      pass
    elif isinstance(orig, int):  # File descriptor
      os.write(orig, captured)
    else:  # Must be file object. Inspired from cPython implementation
      orig.write(captured)
    return None

  # pylint: disable=redefined-builtin
  def communicate(self, input=None):

    # Rumor has it that if you call communicate multiple times there is no
    # telling what monsters are brought to life. Since we call communicate
    # ourselves, this is intended as a safeguard for such undefined behavior.
    if self._communicate_called:
      raise RuntimeError('Popen.communicate() called multiple times.')
    self._communicate_called = True

    # Determine stdin contents to send to actual process
    in_str = None  # Default: don't relay to Popen
    if self._orig_in == subprocess.PIPE:
      in_str = input  # Only time `input` param has significance, relay
      # pylint: enable=redefined-builtin
    elif self._orig_in is None:
      pass  # Popen(stdin=None) and communicate(input) means don't relay
    elif isinstance(self._orig_in, int):
      in_str = os.read(self._orig_in, 2 ** 16)  # Buffer size required
    else:
      in_str = self._orig_in.read()

    # Capture the input
    self.stdin_capture.write(in_str)

    # Run the real communicate
    out, err = super(_PopenCapture, self).communicate(in_str)
    out = encoding.Decode(out)
    err = encoding.Decode(err)

    # Capture the output
    self.stdout_capture.write(out)
    self.stderr_capture.write(err)

    # For stdout and stderr respectively, potentially write and return output
    return self._rewire(self._orig_out, out), self._rewire(self._orig_err, err)

  def wait(self, *args, **kwargs):
    # If user uses wait instead of communicate, we hijack this and send it to
    # communicate, and then discard the output. Multiple calls to wait are ok.
    if not self._communicate_called:
      self.communicate()
    return super(_PopenCapture, self).wait(*args, **kwargs)


class WithCommandCapture(test_case.WithContentAssertions):
  """A base class for tests that need to capture command I/O.

  Attributes:
    orig_popen: Constructor, the original `subprocess.Popen`, can be used by
      tests.
  """
  COMMAND_IN = 'command.stdin'
  COMMAND_OUT = 'command.stdout'
  COMMAND_ERR = 'command.stderr'
  OUTPUT_MSG = 'Captured {name}: <<<{output}>>>\n'

  def SetUp(self):
    """Sets up global command capture to buffers."""
    self._cmd_in = _PopenCapture.stdin_capture
    self._cmd_out = _PopenCapture.stdout_capture
    self._cmd_err = _PopenCapture.stderr_capture
    self.orig_popen = subprocess.Popen  # Reference to original Popen for tests
    self.StartObjectPatch(subprocess, 'Popen', new=_PopenCapture)
    self._show_command_output = False
    sys.exc_clear()

  def ShowCommandOutput(self):
    """Force that test's command I/O to be displayed."""
    self._show_command_output = True

  def TearDown(self):
    """Potentially dumps captured I/O and cleans up."""
    if self._show_contents_on_failure:
      if sys.exc_info()[0] is not None or self._show_command_output:
        # Dump all captured data to original stderr
        sys.__stderr__.write(WithCommandCapture.OUTPUT_MSG.format(
            name=WithCommandCapture.COMMAND_IN,
            output=self.GetCommandInput()))
        sys.__stderr__.write(WithCommandCapture.OUTPUT_MSG.format(
            name=WithCommandCapture.COMMAND_OUT,
            output=self.GetCommandOutput()))
        sys.__stderr__.write(WithCommandCapture.OUTPUT_MSG.format(
            name=WithCommandCapture.COMMAND_ERR,
            output=self.GetCommandErr()))

    # Flush command buffers
    self.ClearCommandInput()
    self.ClearCommandOutput()
    self.ClearCommandErr()

  def GetCommandInput(self):
    """Gets the text that was sent to stdin."""
    return self._cmd_in.getvalue()

  def GetCommandOutput(self):
    """Gets the text that was sent to stdout."""
    return self._cmd_out.getvalue()

  def GetCommandErr(self):
    """Gets the text that was sent to stderr."""
    return self._cmd_err.getvalue()

  def ClearCommandInput(self):
    """Resets the standard input capture."""
    self._cmd_in.truncate(0)

  def ClearCommandOutput(self):
    """Resets the standard output capture."""
    self._cmd_out.truncate(0)

  def ClearCommandErr(self):
    """Resets the standard error capture."""
    self._cmd_err.truncate(0)

  def AssertCommandOutputContains(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertContains(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandOutputNotContains(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertContains(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandOutputEquals(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertEquals(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandOutputNotEquals(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertEquals(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandOutputMatches(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertMatches(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandOutputNotMatches(
      self, expected, name=COMMAND_OUT, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertMatches(
        expected, self.GetCommandOutput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrContains(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertContains(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrNotContains(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertContains(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrEquals(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertEquals(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrNotEquals(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertEquals(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrMatches(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertMatches(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandErrNotMatches(
      self, expected, name=COMMAND_ERR, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertMatches(
        expected, self.GetCommandErr(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputContains(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertContains(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputNotContains(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertContains(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputEquals(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertEquals(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputNotEquals(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertEquals(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputMatches(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=True):
    self._AssertMatches(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)

  def AssertCommandInputNotMatches(
      self, expected, name=COMMAND_IN, normalize_space=False,
      actual_filter=None, success=False):
    self._AssertMatches(
        expected, self.GetCommandInput(), name,
        normalize_space=normalize_space,
        actual_filter=actual_filter, success=success)
