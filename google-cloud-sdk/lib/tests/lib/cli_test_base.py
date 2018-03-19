# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Some helper classes for testing gcloud cli commands.

Extending these classes gives you a gcloud entry point with just the modules
you want installed.  By default it will contain the top level commands from
under gcloud.  Add your module to gcloud by calling the RegisterModule() method
from within the PreSetUp() method of your class.
"""
from __future__ import absolute_import

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import argparse
import contextlib
import os
import re
import shlex
import sys

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk import gcloud_main
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.util import retry
from tests.lib import sdk_test_base
from tests.lib import test_case

import six
from six.moves import StringIO


class StopExecutionException(Exception):
  """An exception we can throw to stop execution after argcomplete.

  It's a better than using its default behavior of using sys.exit because we can
  be sure it's what we expect and not another reason it is exiting.
  """


class MockArgumentError(Exception):
  """Exception raised during mocked argparse.exit."""


def _ShlexSplit(s, comments=False, posix=True):
  """Avoids unfriendly UNICODE behavior of shlex.split()."""
  # Initialize lexer in non-posix mode. Posix mode adds ISO-8859-1 8th bit set
  # chars to the identifier set without considering UNICODE. No way they tested
  # shlex with UNICODE.
  lex = shlex.shlex(s, posix=False)

  # After initialization posix mode is OK. These statements set lex back into
  # posix mode.
  if posix:
    lex.eof = None
    lex.posix = True
  lex.whitespace_split = True
  if not comments:
    lex.commenters = ''

  return list(lex)


class WithCompletion(test_case.TestCase):
  """A base class for testing parser and CLI completion."""

  def RunParserCompletion(self, parser, command, expected):
    """Runs arcomplete.autocomplete on parser+command, avoiding CLI baggage."""
    os.environ['_ARGCOMPLETE'] = '1'
    os.environ['_ARGCOMPLETE_IFS'] = '\t'
    os.environ['_ARGCOMPLETE_TRACE'] = 'info'
    os.environ['COMP_LINE'] = command
    os.environ['COMP_POINT'] = str(len(command))
    if '_ARC_DEBUG' in os.environ:
      del os.environ['_ARC_DEBUG']

    def MockExit(*unused_args, **unused_kwargs):
      raise StopExecutionException()

    try:
      output_stream = StringIO()
      with self.assertRaises(StopExecutionException):
        # pylint: disable=protected-access
        cli._ArgComplete(
            parser,
            exit_method=MockExit,
            output_stream=output_stream)
      completions = [s.strip() for s in output_stream.getvalue().split('\t')]
      self.assertEqual(set(expected), set(completions),
                       msg='Completions did not match.')
    finally:
      del os.environ['_ARGCOMPLETE']
      del os.environ['_ARGCOMPLETE_IFS']
      del os.environ['_ARGCOMPLETE_TRACE']
      del os.environ['COMP_LINE']
      del os.environ['COMP_POINT']


class CliTestBase(sdk_test_base.WithOutputCapture,
                  test_case.WithInput, WithCompletion):
  """A base class for tests that want to test gcloud commands."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    # Allow large diffs
    self.maxDiff = None  # pylint: disable=invalid-name

  def Project(self):
    """Gets the project that should be set for tests.

    Override this method to select a project to use.

    Returns:
      str, The project to use.
    """
    return 'fake-project'

  def VersionFunc(self):
    self.cli.Execute(['version'])

  def _CreateCLI(self, surfaces=None, translator=None):
    return gcloud_main.CreateCLI(surfaces or [], translator)

  def SetUp(self):
    # When running tests under coverage, there is an import error that is
    # handled but for some reason, the exception information stays in
    # sys.exc_info().  The mock exit functions below pick up that error as if
    # it was an error in the test, when in fact it is in startup and has already
    # been handled.  This clears out the exception so that only new exceptions
    # will be intercepted by the exit functions.
    # Python 3 does not have this method, but handles exception scope as if it
    # is always used.
    if six.PY2:
      sys.exc_clear()

    self.cli = None
    properties.VALUES.core.user_output_enabled.Set(True)
    project = self.Project()
    if project:
      properties.PersistProperty(properties.VALUES.core.project, project,
                                 properties.Scope.USER)
    self.enforce_ascii_args_mock = None

    # Make sure we recover the CLI's memory
    self.addCleanup(self._DestroyCLI)

    def MockExit(exc):
      core_exceptions.reraise(exc)

    def MockArgparseExit(status=0, message=None):
      exc = sys.exc_info()[1]
      if exc:
        core_exceptions.reraise(MockArgumentError(exc))
      log.err.Print(message)
      sys.exit(status)

    self.StartObjectPatch(calliope_exceptions, '_Exit').side_effect = MockExit
    self.StartObjectPatch(
        argparse.ArgumentParser, 'exit').side_effect = MockArgparseExit

    self.cli = self._CreateCLI()
    # Ensure everything gets loaded correctly.
    self.AssertErrNotContains('ERROR')

    self.track = calliope_base.ReleaseTrack.GA

  def TearDown(self):
    # Wait for all threads to finish.
    # Classes like ProgressTracker leave threads behind so as not to block the
    # user interraction.
    self.JoinAllThreads()
    if (self.enforce_ascii_args_mock and
        not self.enforce_ascii_args_mock.call_count):
      self.fail('Delete unused self.AllowUnicode() -- either '
                'no command was run or @base.UnicodeIsSupported was set.')

  def _DestroyCLI(self):
    """Delete all attributes from the modules created by the CLI."""
    if self.cli and self.cli._TopElement():  # pylint: disable=protected-access
      construction_id = self.cli._TopElement()._construction_id  # pylint: disable=protected-access
      if isinstance(construction_id, six.string_types):
        to_remove = [(n, m) for (n, m) in sys.modules.items()
                     if construction_id in n]
        for name, module in to_remove:
          for attribute in dir(module):
            try:
              delattr(module, attribute)
            except (AttributeError, TypeError):
              pass  # Delete what we can and don't worry about the rest
          del sys.modules[name]
          del module

  def AllowUnicode(self):
    self.enforce_ascii_args_mock = self.StartObjectPatch(
        cli.CLI, '_EnforceAsciiArgs')

  @staticmethod
  def GetArgparseNamespaceDict(parsed_args):
    """Returns the dict of public args from a parsed args Namespace."""
    return {a: v for a, v in six.iteritems(parsed_args.__dict__)
            if a[0].islower()}

  def AssertArgparseNamespaceEquals(self, expected, actual):
    """Asserts that the expected argparse.Namespace equals the actual one.

    Args:
      expected: The expected argparse Namespace or dict of arg dest names and
        values.
      actual: The expected argparse Namespace.
    """
    if isinstance(expected, dict):
      expected_dict = expected
    else:
      expected_dict = self.GetArgparseNamespaceDict(expected)
    actual_dict = self.GetArgparseNamespaceDict(actual)
    self.assertEquals(expected_dict, actual_dict)

  def AssertRaisesExceptionRegexp(
      self, expected_exception, expected_regexp,
      callable_obj=None, *args, **kwargs):
    """Wrapper around assertRaisesRegexp with regexp matching.

    This functionreplicates assertRaisesRegexp() but is a namewise companion to
    AssertRaisesExceptionMatches().  Just calls
    assertRaisesRegexp(expected_exception, ...).

    Args:
      expected_exception: Exception, The expected exception type.
      expected_regexp: str, The string to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    if callable_obj is None:
      return self.assertRaisesRegexp(expected_exception, expected_regexp)
    return self.assertRaisesRegexp(
        expected_exception, expected_regexp,
        callable_obj, *args, **kwargs)

  def AssertRaisesExceptionMatches(
      self, expected_exception, expected_message,
      callable_obj=None, *args, **kwargs):
    """Wrapper around assertRaisesRegexp with regexp escaping.

    Just calls assertRaisesRegexp(expected_exception,
                                  re.escape(expected_message), ...)

    Args:
      expected_exception: Exception, The expected exception type.
      expected_message: str, The string to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    if callable_obj is None:
      return self.assertRaisesRegexp(expected_exception,
                                     re.escape(expected_message))
    return self.assertRaisesRegexp(
        expected_exception, re.escape(expected_message),
        callable_obj, *args, **kwargs)

  def AssertRaisesToolExceptionRegexp(
      self, expected_regexp, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting a ToolException since this is common.

    ToolException WILL SOON BE ELIMINATED FROM Cloud SDK.

    Just calls AssertRaisesRegexp(calliope_exceptions.ToolException, ...).
    for the type.

    Args:
      expected_regexp: str, The regex to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    return self.AssertRaisesExceptionRegexp(
        calliope_exceptions.ToolException, expected_regexp,
        callable_obj, *args, **kwargs)

  def AssertRaisesToolExceptionMatches(
      self, expected_message, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting a ToolException since this is common.

    ToolException WILL SOON BE ELIMINATED FROM Cloud SDK.

    Just calls assertRaisesRegexp() with a re.escape() on the expected_message
    and ToolException for the type. This is useful for direct comparison of
    strings that have regex characters that need to be escaped.

    Args:
      expected_message: str, The message to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    return self.AssertRaisesExceptionMatches(
        calliope_exceptions.ToolException, expected_message,
        callable_obj, *args, **kwargs)

  def AssertRaisesHttpExceptionRegexp(
      self, expected_regexp, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting an HttpException since this is common.

    Just calls AssertRaisesExceptionRegexp(expected_exception, ...).

    Args:
      expected_regexp: str, The regex to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    return self.AssertRaisesExceptionRegexp(
        exceptions.HttpException, expected_regexp,
        callable_obj, *args, **kwargs)

  def AssertRaisesHttpExceptionMatches(
      self, expected_message, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting an HttpException since this is common.

    Just calls AssertRaisesExceptionMatches(expected_exception, ...).

    Args:
      expected_message: str, The message to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of AssertRaisesExceptionMatches(exceptions.HttpException, ...).
    """
    return self.AssertRaisesExceptionMatches(
        exceptions.HttpException, expected_message,
        callable_obj, *args, **kwargs)

  def AssertRaisesHttpErrorMatchesAsHttpException(
      self, expected_message, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting that an HttpError prints correctly.

    Checks that the expected message (not a regular expresssion) matches the
    error created by converting the given HttpError to an HttpException.

    Args:
      expected_message: str, The message to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      A context manager if callable_obj is not given. None, otherwise.
    """
    @contextlib.contextmanager
    def _MatchingHttpExceptionContextManager():
      try:
        yield
        self.fail('Expected HttpError, but no exception raised.')
      except apitools_exceptions.HttpError as err:
        self.assertRegexpMatches(
            six.text_type(calliope_exceptions.HttpException(err)),
            re.escape(expected_message))
    if callable_obj is None:
      return _MatchingHttpExceptionContextManager()
    else:
      with _MatchingHttpExceptionContextManager():
        callable_obj(*args, **kwargs)

  def AssertRaisesArgumentErrorRegexp(
      self, expected_regexp, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting an ArgumentError since this is common.

    Just calls AssertRaisesExceptionRegexp(MockArgumentError, ...).

    Args:
      expected_regexp: str, The regex to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    return self.AssertRaisesExceptionRegexp(
        MockArgumentError, expected_regexp,
        callable_obj, *args, **kwargs)

  def AssertRaisesArgumentErrorMatches(
      self, expected_message, callable_obj=None, *args, **kwargs):
    """A convenience method for asserting an ArgumentError since this is common.

    Just calls AssertRaisesExceptionMatches(MockArgumentError, ...).

    Args:
      expected_message: str, The regex to match on the exception message.
      callable_obj: If given, it will be called with *args and **kwargs.
      *args: The args for the callable.
      **kwargs: The args for the callable.

    Returns:
      The result of assertRaisesRegexp() which can be used as a context manager.
    """
    return self.AssertRaisesExceptionMatches(
        MockArgumentError, expected_message,
        callable_obj, *args, **kwargs)

  def AssertRaisesArgumentError(self, callable_obj=None, *args, **kwargs):
    if callable_obj is None:
      return self.assertRaises(MockArgumentError)
    return self.assertRaises(MockArgumentError, callable_obj, *args, **kwargs)

  def Run(self, cmd, track=None):
    """Executes the given command.

    Args:
      cmd: The command to execute. This can be either a list or tuple of
        arguments or a string that represents what the user would type
        into his or her shell.
      track: specifies which version of the command to run. If not specified
             self.track will be used.

    Returns:
      The result of executing the command determined by the command
      implementation.

    Raises:
      TypeError: If cmd is a type other than a list, tuple, or string.
    """
    # pylint:disable=protected-access, Invalidate cache between commands.
    named_configs.ActivePropertiesFile.Invalidate()
    if (not isinstance(cmd, list) and not isinstance(cmd, six.string_types)
        and not isinstance(cmd, tuple)):
      raise TypeError(
          'expected list, tuple, or string for the command; received: {0}'
          .format(type(cmd)))

    if isinstance(cmd, six.string_types):
      # need to account for the fact that shlex escapes backslashes when parsing
      # in Posix mode
      if self.IsOnWindows():
        preprocessed_cmd = cmd.replace(os.sep, os.sep + os.sep)
      else:
        preprocessed_cmd = cmd
      cmd = []
      for arg in _ShlexSplit(
          StringIO(preprocessed_cmd), comments=True, posix=True):
        if isinstance(arg, six.text_type):
          try:
            # Convert ascii args back to ascii for Python < 2.7.
            arg = arg.encode('ascii')
          except UnicodeError:
            # Encoded args remain encoded.
            pass
        cmd.append(arg)
    if track is None:
      track = self.track
    if track.prefix is None:
      prefixed_command = []
    else:
      prefixed_command = [track.prefix]
    prefixed_command.extend(cmd)
    return self.cli.Execute(prefixed_command)

  def _RunUntil(self, retry_function, retry_if_function, cmd, max_retrials,
                sleep_ms, max_wait_ms, exponential_sleep_multiplier, jitter_ms):
    """Helper function. Common functionallity between RunUntil functions."""
    retryer = retry.Retryer(
        max_retrials=max_retrials, jitter_ms=jitter_ms, max_wait_ms=max_wait_ms,
        exponential_sleep_multiplier=exponential_sleep_multiplier)
    return retry_function(retryer, self.Run, (cmd,),
                          should_retry_if=retry_if_function, sleep_ms=sleep_ms)

  def ReRunUntilOutputContains(self, cmd, expected_substring,
                               max_retrials=2, sleep_ms=1000, max_wait_ms=6000,
                               exponential_sleep_multiplier=1.5,
                               jitter_ms=1000):
    """Retry a command until some string appears in the standard output.

    Please do not use this to retry expensive commands (e.g. a create command).
    Instead, run that command normally and use this on a cheaper command (e.g a
    list command) to wait until or verify that the first command succeeded.

    Arguments:
      cmd: list, tuple or string, The command to execute. See the Run function
        for more details.
      expected_substring: string, The string to watch for in the output. Try to
        keep this minimimal to prevent brittle tests.
      max_retrials: int, The maximum number of times to retry the command after
        the first call
      sleep_ms: int, The desired amount of time to sleep between the end of
        the first call and the beginning of the second
      max_wait_ms: int, The maximum amount of time to wait in total
      exponential_sleep_multiplier: float, How much longer to wait between each
        command.
      jitter_ms: int, Adds between 0 and jitter milliseconds to each sleep time.

    Returns:
      The result of executing the command determined by the command
      implementation.

    Raises:
      retry.WaitException: If the maximum time limit was exceeded
      retry.MaxRetrialsException: If the command was retried too many times
    """
    def ShouldRetryIf(unused_result, unused_state):
      return expected_substring not in self.GetOutput()
    return self._RunUntil(
        retry.Retryer.RetryOnResult, ShouldRetryIf, cmd, max_retrials,
        sleep_ms, max_wait_ms, exponential_sleep_multiplier, jitter_ms)

  def ReRunUntilErrContains(self, cmd, expected_substring,
                            max_retrials=2, sleep_ms=1000, max_wait_ms=6000,
                            exponential_sleep_multiplier=1.5,
                            jitter_ms=1000):
    """Retry a command until some string appears in the standard error.

    Please do not use this to retry expensive commands (e.g. a create command).
    Instead, run that command normally and use this on a cheaper command (e.g a
    list command) to wait until or verify that the first command succeeded.

    Arguments:
      cmd: list, tuple or string, The command to execute. See the Run function
        for more details.
      expected_substring: string, The string to watch for in the error. Try to
        keep this minimimal to prevent brittle tests.
      max_retrials: int, The maximum number of times to retry the command after
        the first call
      sleep_ms: int, The desired amount of time to sleep between the end of
        the first call and the beginning of the second
      max_wait_ms: int, The maximum amount of time to wait in total
      exponential_sleep_multiplier: float, How much longer to wait between each
        command.
      jitter_ms: int, Adds between 0 and jitter milliseconds to each sleep time.

    Returns:
      The result of executing the command determined by the command
      implementation.

    Raises:
      retry.WaitException: If the maximum time limit was exceeded
      retry.MaxRetrialsException: If the command was retried too many times
    """
    def ShouldRetryIf(unused_result, unused_state):
      return expected_substring not in self.GetErr()
    return self._RunUntil(
        retry.Retryer.RetryOnResult, ShouldRetryIf, cmd, max_retrials,
        sleep_ms, max_wait_ms, exponential_sleep_multiplier, jitter_ms)

  def ReRunWhileException(self, cmd, expected_exception,
                          max_retrials=2, sleep_ms=1000, max_wait_ms=6000,
                          exponential_sleep_multiplier=1.5,
                          jitter_ms=1000):
    """Retry a command until it does not raise a specific exception.

    Please do not use this to retry expensive commands (e.g. a create command).
    Instead, run that command normally and use this on a cheaper command (e.g a
    list command) to wait until or verify that the first command succeeded.

    Arguments:
      cmd: list, tuple or string, The command to execute. See the Run function
        for more details.
      expected_exception: class, The exception type to retry on (e.g.
        AttributeError). Try to use as specific an error as possible to avoid
        retrying commands on real failures.
      max_retrials: int, The maximum number of times to retry the command after
        the first call
      sleep_ms: int, The desired amount of time to sleep between the end of
        the first call and the beginning of the second
      max_wait_ms: int, The maximum amount of time to wait in total
      exponential_sleep_multiplier: float, How much longer to wait between each
        command.
      jitter_ms: int, Adds between 0 and jitter milliseconds to each sleep time.

    Returns:
      The result of executing the command determined by the command
      implementation.

    Raises:
      retry.WaitException: If the maximum time limit was exceeded
      retry.MaxRetrialsException: If the command was retried too many times
    """
    def ShouldRetryIf(
        exc_type, unused_exc_value, unused_exc_traceback, unused_state):
      return exc_type == expected_exception
    return self._RunUntil(
        retry.Retryer.RetryOnException, ShouldRetryIf, cmd, max_retrials,
        sleep_ms, max_wait_ms, exponential_sleep_multiplier, jitter_ms)

  def RunCompletion(self, cmd, choices):
    # pylint:disable=protected-access, Invalidate cache between commands.
    named_configs.ActivePropertiesFile.Invalidate()
    # argcomplete messes with the parser object so we need to make a new one
    # each time.
    completer_cli = self._CreateCLI()
    # argcomplete always works off the full command line
    command = completer_cli.name + ' ' + cmd
    self.RunParserCompletion(completer_cli.top_element.ai, command, choices)


def main():
  return sdk_test_base.main()
