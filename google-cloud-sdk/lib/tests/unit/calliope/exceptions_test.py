# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import os
import socket
import ssl
import sys

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr_os
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.calliope import util

import six


class ExceptionsTest(util.Base, sdk_test_base.WithOutputCapture):
  """Tests basic exception handling behavior."""

  def SetUp(self):
    self.InitLogging()

  def TearDown(self):
    log.Reset()

  def testUnknownToolException(self):
    if six.PY2:
      # In PY2 sys.exc_info() remains set outside of try:except scope, in PY3
      # it's unset outside try:except. The unit tests throw multiple exceptions
      # and get confused if one is laying around from a previous test.
      sys.exc_clear()
    unknown = exceptions.ToolException.FromCurrent()
    self.assertEqual(six.text_type(unknown), 'An unknown error has occurred')
    unknown = exceptions.ToolException.FromCurrent('some', 'args')
    self.assertEqual(unknown.args, ('some', 'args'))
    content = self.GetLogFileContents()
    self.assertNotIn('Traceback', content)

  def testToolExceptionWrapper(self):
    try:
      raise ValueError('original')
    except ValueError as e:
      original = e
      tool = exceptions.ToolException.FromCurrent()
      tool_args = exceptions.ToolException.FromCurrent('new message')

    # Make sure the wrapper exception was constructed correctly
    self.assertEqual(original.args, tool.args)
    self.assertEqual(tool_args.args, ('new message',))
    self.assertEqual(six.text_type(tool_args), 'new message')

    # Make sure the inner exception is logged only to the file with traceback
    content = self.GetLogFileContents()
    self.assertIn('original', content)
    self.assertIn('Traceback', content)
    self.assertNotIn('original', self.stdout)
    self.assertNotIn('original', self.stderr)

  def testConvertKnownError(self):
    err = http_error.MakeHttpError(400)
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, exceptions.HttpException)
    self.assertTrue(print_exc)

  def testConvertKnownErrorNetworkIssue(self):
    err = socket.error(errno.ECONNREFUSED, 'error')
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, core_exceptions.NetworkIssueError)
    self.assertTrue(print_exc)

    err = socket.timeout('timed out')
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, core_exceptions.NetworkIssueError)
    self.assertTrue(print_exc)

  def testConvertKnownErrorNonAscii(self):
    err = socket.error(errno.ECONNREFUSED, b'\xce\x94')
    try:
      new_err, print_exc = exceptions.ConvertKnownError(err)
    except UnicodeError as e:
      self.fail(e)
    self.assertIsInstance(new_err, core_exceptions.NetworkIssueError)
    self.assertTrue(print_exc)

  def testConvertUnknownError(self):
    err = ValueError()
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsNone(new_err)
    self.assertTrue(print_exc)

  def testConvertKnownErrorFromSubclass(self):
    class SSLErrorExt(ssl.SSLError):
      pass

    err = SSLErrorExt('Test SSL Error Extension')
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, core_exceptions.NetworkIssueError)
    self.assertTrue(print_exc)

  def testConvertKnownErrorFromClassHierarchy(self):
    class SSLErrorExt1(ssl.SSLError):
      pass

    class SSLErrorExt2(SSLErrorExt1):
      pass

    err = SSLErrorExt2('Test SSL Error Sub-Extension')
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, core_exceptions.NetworkIssueError)
    self.assertTrue(print_exc)

  def testConvertNoPrint(self):
    err = exceptions.ExitCodeNoError('Error')
    new_err, print_exc = exceptions.ConvertKnownError(err)
    self.assertIsInstance(new_err, exceptions.ExitCodeNoError)
    self.assertFalse(print_exc)


class TruncateToLineWidthTest(test_case.TestCase):

  def SetUp(self):
    self.width = 10
    self.string = '0123456789abcdef'
    self.beginning_idx = 0
    self.middle_idx = 12  # to the right of center because we right-align
    self.end_idx = len(self.string)

  def testTruncate_NoTruncationNeeded(self):
    """Test that a string shorter than the terminal width is not truncated."""
    self.assertEqual(exceptions._TruncateToLineWidth('foo', 0, self.width),
                     'foo')

  def testTruncate_AlignBeginning(self):
    """Test that a string aligned to the beginning has its end truncated."""
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.beginning_idx,
                                        self.width),
        '0123456789')

  def testTruncate_AlignBeginningFill(self):
    """Test that string aligned to the beginning has its end filled in."""
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.beginning_idx,
                                        self.width, fill='...'),
        '0123456...')

  def testTruncate_AlignEnd(self):
    """Test that a string aligned to the end has its beginning truncated."""
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.end_idx, self.width),
        '6789abcdef')

  def testTruncate_AlignEndFill(self):
    """Test that string aligned to the end has its beginning filled in."""
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.end_idx, self.width,
                                        fill='...'),
        '...9abcdef')

  def testTruncate_AlignMiddle(self):
    """Test that a string aligned to the end has its beginning truncated."""
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.middle_idx,
                                        self.width),
        '23456789ab')

  def testTruncate_AlignMiddleFill(self):
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string, self.middle_idx,
                                        self.width, fill='...'),
        '...5678...')

  def testTruncate_LongFill(self):
    self.assertEqual(
        exceptions._TruncateToLineWidth(self.string,
                                        self.middle_idx,
                                        self.width,
                                        fill='.' * int(self.width / 2)),
        self.string)


class FormatNonAsciiMarkerString(test_case.TestCase):

  def SetUp(self):
    self.term_size_mock = self.StartObjectPatch(console_attr_os, 'GetTermSize')

  def testFormatNonAsciiMarkerString(self):
    self.term_size_mock.return_value = (80, 80)
    args = ['command', '--foo', b'\xce\x94']
    marker_string = exceptions._FormatNonAsciiMarkerString(args)
    self.assertEqual(marker_string,
                     ('command --foo \\u0394\n'
                      '              ^ invalid character'))

  def testFormatNonAsciiMarkerStringSmallScreen(self):
    # len('^ invalid character') < 30
    self.term_size_mock.return_value = (30, 80)
    args = ['command', '--foo', b'\xce\x94']
    marker_string = exceptions._FormatNonAsciiMarkerString(args)
    self.assertEqual(marker_string,
                     ('...d --foo \\u0394\n'
                      '           ^ invalid character'))

  def testFormatNonAsciiMarkerStringReallySmallScreen(self):
    # 10 < len('^ invalid character')
    self.term_size_mock.return_value = (10, 80)
    args = ['command', '--foo', b'\xce\x94']
    marker_string = exceptions._FormatNonAsciiMarkerString(args)
    self.assertEqual(marker_string,
                     ('command --foo \\u0394\n'
                      '              ^ invalid character'))

  def testFormatNonAsciiMarkerStringAllAscii(self):
    self.term_size_mock.return_value = (80, 80)
    args = ['command', '--foo', 'bar']
    with self.assertRaisesRegex(
        ValueError, r'The command line is composed entirely of ASCII '
        r'characters\.'):
      exceptions._FormatNonAsciiMarkerString(args)


class InvalidCharacterInArgExceptionTest(test_case.TestCase):

  def testInvalidCharacterInArgException(self):
    args = ['command', '--foo', b'\xce\x94']
    exc = exceptions.InvalidCharacterInArgException(args, args[-1])
    self.assertRegexpMatches(
        six.text_type(exc),
        'Failed to read command line argument \\[\\\\u0394\\]')
    self.assertTrue(six.text_type(exc).endswith(
        ('\n'
         'command --foo \\u0394\n'
         '              ^ invalid character')))

  def testInvalidCharacterInArgException_ComplexPath(self):
    command_path = os.path.join('path', 'to', 'command.py')
    args = [command_path, '--foo', b'\xce\x94']
    exc = exceptions.InvalidCharacterInArgException(args, args[-1])
    self.assertRegexpMatches(
        six.text_type(exc),
        'Failed to read command line argument \\[\\\\u0394\\]')
    self.assertTrue(six.text_type(exc).endswith(
        ('\n'
         'command --foo \\u0394\n'
         '              ^ invalid character')))
    self.assertNotIn('path', six.text_type(exc))


class RaiseExceptionInsteadOfTest(cli_test_base.CliTestBase):

  def testRaiseErrorInsteadOf(self):

    with self.assertRaisesRegex(core_exceptions.Error, "something's fishy"):

      @exceptions.RaiseErrorInsteadOf(
          core_exceptions.Error, AttributeError, ValueError)
      def BadFun():
        raise AttributeError("something's fishy")

      BadFun()

  def testRaiseArgumentErrorOutsideOfArgparseNoCrash(self):
    with self.assertRaisesRegex(
        parser_errors.ArgumentError,
        'argument --some-flag: Must be specified.'):
      self.Run(['meta', 'test', '--argumenterror-outside-argparse'])
    self.AssertErrEquals(
        'ERROR: (gcloud.meta.test) argument --some-flag: '
        'Must be specified.\n')


class HandleErrorTest(cli_test_base.CliTestBase):

  def testAppendMessage_MissingServicesUsePermission(self):
    error = http_error.MakeHttpError(
        403,
        message=('Grant the caller the Owner or Editor role, or a custom role '
                 'with the serviceusage.services.use permission'))
    with self.AssertRaisesExceptionRegexp(exceptions.HttpException,
                                          'Permission denied.*'):
      exceptions.HandleError(error, 'gcloud.asset.export')
    self.AssertErrContains(
        'If you want to invoke the command from a project '
        'different from the target resource project, use '
        '`--billing-project` or `billing/quota_project` property.')

  def testAppendMessage_MissingAuthScopes(self):
    error = http_error.MakeHttpError(
        403, message='Request had insufficient authentication scopes')
    with self.AssertRaisesExceptionRegexp(exceptions.HttpException,
                                          'Permission denied.*'):
      exceptions.HandleError(error, 'gcloud.asset.export')
    self.AssertErrContains(
        'If you are in a compute engine VM, it is likely that the specified '
        'scopes during VM creation are not enough to run this command.')

  def testNotAppendMessage(self):
    error = http_error.MakeHttpError(403)
    with self.AssertRaisesExceptionRegexp(exceptions.HttpException,
                                          'Permission denied.*'):
      exceptions.HandleError(error, 'gcloud.asset.export')
    self.AssertErrNotContains(
        'If you want to invoke the command from a project '
        'different from the target resource project, use '
        '`--billing-project` or `billing/quota_project` property.')


if __name__ == '__main__':
  test_case.main()
