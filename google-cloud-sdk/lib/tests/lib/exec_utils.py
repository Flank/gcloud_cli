# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Utilities for executing other processes in tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import subprocess
import sys
import threading

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms

import six


_TOOL_DIR = 'bin'


def FullPath(command):
  return os.path.join(config.Paths().sdk_root, _TOOL_DIR, command)


def _IsOnWindows():
  return (platforms.OperatingSystem.Current() ==
          platforms.OperatingSystem.WINDOWS)


def GetArgsForScript(script_name, args):
  """Returns a list of args for execution of a cloud CLI wrapper.

  This wrapper must be a sh script on non-windows, or a .cmd file, without the
  '.cmd' extension (so it has the same script_name as non-windows), on windows.

  Args:
    script_name: str, The name of the CLI wrapper. For linux, it must be the
        whole name. On windows, it is the name except for the trailing '.cmd'.
    args: [str], The arguments for the script itself.

  Returns:
    [str], A list of args for the process executor.
  """
  if _IsOnWindows():
    return execution_utils.ArgsForCMDTool(FullPath(script_name + '.cmd'), *args)
  else:
    return execution_utils.ArgsForExecutableTool(FullPath(script_name), *args)


def GetArgsForLegacyScript(script_name, args, interpreter=None):
  """Returns a list of args for execution of the given script.

  Args:
    script_name: The name of the script to run.  The extension determines which
      interpreter will be used for execution.  Python will be used for .py.
      If there is no extension it is assumed it is just a binary file and is
      executed directly.  .exe files are executed directly on Windows, or
      error raised if not on Windows. If it ends with a single dot, it sees
      what OS it is running on and either executes .cmd or .sh.
    args:  The arguments for the script itself
    interpreter: an interpreter to use rather than trying to derive it from
      the extension name.  The value is the same as an extension, right now
      only implemented for 'py'.

  Returns:
    a list of args for the process executor

  Raises:
    ValueError: if the script type cannot be determined or is invalid for OS
  """

  (_, tail) = os.path.splitext(script_name)
  # No extension, just try to execute it
  if not tail and not interpreter:
    # In our tests, users generally just refer to 'gcloud'. But in windows,
    # there is no 'gcloud' file, there is gcloud.cmd. This isn't an issue on the
    # shell because the shell, given <name>, is smart enough to detect that
    # there is a file <name>.cmd. subprocess.Popen is not smart enough to know
    # this, however, unless shell=True is given. We'd like to avoid that if
    # possible, however.
    if _IsOnWindows() and script_name == 'gcloud':
      script_name = 'gcloud.cmd'
    return execution_utils.ArgsForExecutableTool(FullPath(script_name), *args)

  # Strip the '.'
  if interpreter:
    ext = interpreter
  else:
    ext = tail[1:]

  # Python, same across platforms
  if ext == 'py':
    return execution_utils.ArgsForPythonTool(FullPath(script_name), *args)

  # .exe, windows only
  if ext == 'exe':
    if not _IsOnWindows():
      raise ValueError('Extention for {0} is only valid for WINDOWS'.format(
          script_name))
    return execution_utils.ArgsForExecutableTool(FullPath(script_name), *args)

  # ending in a '.'
  if not ext:
    if _IsOnWindows():
      return execution_utils.ArgsForCMDTool(
          FullPath(script_name + 'cmd'), *args)
    else:
      return execution_utils.ArgsForExecutableTool(
          FullPath(script_name + 'sh'), *args)
  else:
    raise ValueError('Unknown script type: {0}'.format(script_name))


class ExecutionError(Exception):
  """An exception for when an executed script fails with an error."""

  @staticmethod
  def RaiseIfError(result, check_error_string=True):
    """Raise an Execution error if the result of the process indicates failure.

    Args:
      result: ExecutionResult, The result of the process.
      check_error_string: bool, True to raise if 'ERROR' is found in stdout or
        stderr.  False to raise on non-zero exit code only.

    Raises:
      ExecutionError: If failure was detected for the process.
    """
    fail = result.return_code != 0
    if check_error_string:
      fail |= result.stdout is not None and 'ERROR' in result.stdout
      fail |= result.stderr is not None and 'ERROR' in result.stderr
    if fail:
      raise ExecutionError(result)

  def __init__(self, result, msg='Command failed:'):
    """Create a new ExecutionError object.

    Args:
      result: ExecutionResult, The result of executing the script.
      msg: str, An additional error message to display.
    """
    super(ExecutionError, self).__init__(msg)
    self.result = result
    self.msg = msg

  def __str__(self):
    return self.msg + '\n' + six.text_type(self.result)


class TimeoutError(ExecutionError):
  """An ExecutionError for when the process did not complete in time."""

  def __init__(self, result=None, msg='Command timed out:'):
    """Create a new TimeoutError object.

    Args:
      result: ExecutionResult, The result of executing the script.
      msg: str, An additional error message to display.
    """
    super(TimeoutError, self).__init__(result, msg)

  def __str__(self):
    if self.result:
      return super(TimeoutError, self).__str__()
    return self.msg


class ExecutionResult(object):
  """The result of executing a script.

  Attributes:
    command: str, The command that was run.
    return_code: int, The return code of the process.
    stdout: str, The standard output of the process.
    stderr: str, The standard error of the process.
  """

  def __init__(self, command, return_code, stdout, stderr):
    """Construct a new ExecutionResult object.

    Args:
      command: str, The command that was run.
      return_code: int, The return code of the process.
      stdout: str, The standard output of the process.
      stderr: str, The standard error of the process.
    """
    self.command = command
    self.return_code = return_code
    self.stdout = stdout
    self.stderr = stderr

  def __str__(self):
    error_string = 'Command:\n\t{0}'.format(self.command)
    error_string += '\nExit Code:\n\t{0}'.format(self.return_code)
    error_string += '\nStdout:\n{0}'.format(self.stdout)
    error_string += '\nStderr:\n{0}'.format(self.stderr)
    return error_string


class _ProcessContext(object):
  """A context manager that will kill the process when it loses scope."""

  def __init__(self, runner):
    self.__runner = runner

  def __enter__(self):
    return self.__runner

  def __exit__(self, *exceptional):
    self.Close()
    if exceptional:
      # If there was an error, dump any extra output from the other thread so
      # we can try to see what's going on.
      print(self.__runner.p.stdout.read())
    # always return False so any exceptions will be re-raised
    return False

  def Close(self):
    if self.__runner and self.__runner.p:
      execution_utils.KillSubprocess(self.__runner.p)
      return True
    return False


class _ProcessRunner(object):
  """Runs a script in another thread."""
  # Time to wait after we kill a process for it's thread to exit
  fallback_timeout = 10

  def __init__(self, args, timeout=None, stdin=None, env=None):
    self.args = [encoding.Encode(a, encoding='utf-8') for a in args]
    self.timeout = timeout
    self.stdin = stdin
    self.env = encoding.EncodeEnv(env, encoding='utf-8')
    self.thread = None
    self.p = None
    self.result = None
    self.exc_info = None

  def Run(self):
    self.thread = threading.Thread(target=self._Run)
    self.thread.start()
    self.Wait()

  def RunAsync(self, match_strings=None):
    if match_strings:
      self.thread = threading.Thread(
          target=self._RunMatchOutput, args=(match_strings,))
      self.thread.start()
      self.Wait()
    else:
      self.thread = threading.Thread(target=self._Run)
      self.thread.start()

  def Wait(self):
    self.thread.join(self.timeout)
    if self.exc_info:
      exceptions.reraise(self.exc_info[1], tb=self.exc_info[2])
    if self.thread.isAlive():
      execution_utils.KillSubprocess(self.p)
      # Give the thread a chance to clean up if it can, now that we killed the
      # subprocess.
      self.thread.join(_ProcessRunner.fallback_timeout)
      timeout_message = 'The process timed out: {0}'.format(
          ' '.join(self.args))
      raise TimeoutError(result=self.result, msg=timeout_message)

  def _Run(self):
    try:
      self.p = subprocess.Popen(self.args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=self.env)
      (out, err) = self.p.communicate(self.stdin)
      self.result = ExecutionResult(
          command=' '.join(console_attr.SafeText(a)
                           for a in self.args),
          return_code=self.p.returncode,
          stdout=console_attr.Decode(out),
          stderr=console_attr.Decode(err))
      ExecutionError.RaiseIfError(self.result)
    # pylint: disable=bare-except, not catching, just saving to raise later
    except:
      self.exc_info = sys.exc_info()

  def _RunMatchOutput(self, match_strings):
    try:
      self.p = subprocess.Popen(self.args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=self.env)
      self._WaitForOutput(match_strings)
    # pylint: disable=bare-except, not catching, just saving to raise later
    except:
      self.exc_info = sys.exc_info()

  def _WaitForOutput(self, match_strings):
    """Reads stdout from process until each string in match_strings is hit."""
    idx = 0
    output = []
    def IndexInBounds():
      return idx < len(match_strings)
    while IndexInBounds():
      line = console_attr.Decode(self.p.stdout.readline())
      if not line:
        break
      output.append(line)
      # We allow that a given line may satisfy multiple required strings
      while IndexInBounds() and match_strings[idx] in line:
        idx += 1

    if idx == len(match_strings):
      # If we arrive here, this means that every line was matched
      return

    # Did not find text
    (stdout, stderr) = self.p.communicate()
    self.result = ExecutionResult(
        command=' '.join(self.args), return_code=self.p.returncode,
        stdout=''.join(output) + console_attr.Decode(stdout),
        stderr=console_attr.Decode(stderr))
    raise ExecutionError(
        self.result, msg='Could not find required string in output')
