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

import os
import ssl

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope_cli
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import metrics
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock

from oauth2client import client
import six.moves.http_client


class AlternateCommandTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.maxDiff = None
    self._loader = calliope_cli.CLILoader(
        name='test',
        command_root_directory=os.path.join(
            self.Resource('tests', 'unit', 'calliope', 'testdata', 'sdk1')),
        allow_non_existing_modules=True)
    self._loader.AddReleaseTrack(
        calliope_base.ReleaseTrack.ALPHA,
        os.path.join(self.Resource(
            'tests', 'unit', 'calliope', 'testdata', 'alpha')))
    self.cli = self._loader.Generate()

  def testGAAlternate(self):
    results = self._loader.ReplicateCommandPathForAllOtherTracks(
        ['test', 'command1'])
    expected = {calliope_base.ReleaseTrack.ALPHA: ['test', 'alpha', 'command1']}
    self.assertEqual(results, expected)

  def testAlphaAlternate(self):
    results = self._loader.ReplicateCommandPathForAllOtherTracks(
        ['test', 'alpha', 'command1'])
    expected = {calliope_base.ReleaseTrack.GA: ['test', 'command1']}
    self.assertEqual(results, expected)

  def testBetaAlternate(self):
    # Running something beta, but beta is not a track we registered.  Treat it
    # like beta is just a normal command group.
    results = self._loader.ReplicateCommandPathForAllOtherTracks(
        ['test', 'beta', 'command1'])
    expected = {
        calliope_base.ReleaseTrack.ALPHA: ['test', 'alpha', 'beta', 'command1']
    }
    self.assertEqual(results, expected)

  def testTooShort(self):
    results = self._loader.ReplicateCommandPathForAllOtherTracks(['test'])
    self.assertEqual(results, [])
    results = self._loader.ReplicateCommandPathForAllOtherTracks(
        ['test', 'alpha'])
    self.assertEqual(results, [])
    results = self._loader.ReplicateCommandPathForAllOtherTracks(
        ['test', 'beta'])
    expected = {calliope_base.ReleaseTrack.ALPHA: ['test', 'alpha', 'beta']}
    self.assertEqual(results, expected)


class FakeTopElement(object):

  def __init__(self):
    self._parser = None


class CliTests(sdk_test_base.SdkBase):

  def MakeCli(self):
    cli = calliope_cli.CLI('path', FakeTopElement(), (), (), ())
    self.StartObjectPatch(calliope_exceptions, '_Exit')
    return cli

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownError(self, log_error):
    c = self.MakeCli()
    c._HandleAllErrors(
        exceptions.Error('exception text'), 'group.command', 'LOCAL')
    log_error.assert_called_with('(group.command) exception text')

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownErrorSsl(self, log_error):
    self.DoKnownExceptionHandlingCheck(
        log_error, ssl.SSLError,
        'This may be due to network connectivity issues.')

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownErrorResponseNotReady(self, log_error):
    self.DoKnownExceptionHandlingCheck(
        log_error, six.moves.http_client.ResponseNotReady,
        'This may be due to network connectivity issues.')

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownErrorRefreshError(self, log_error):
    self.DoKnownExceptionHandlingCheck(
        log_error, client.AccessTokenRefreshError,
        'There was a problem refreshing your current auth tokens')

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownErrorFileError(self, log_error):
    self.DoKnownExceptionHandlingCheck(log_error, files.Error, '')

  def DoKnownExceptionHandlingCheck(self, log_error, exc_class, text_to_check):
    c = self.MakeCli()
    c._HandleAllErrors(exc_class('exception text'), 'path', 'LIST COMMAND')
    log_error.assert_called_once_with(mock.ANY)
    # get the first argument of the first call to log.error out of a mock.call
    message = log_error.mock_calls[0][1][0]
    # Don't assert the whole message, just the pieces we expect to be there.
    # This is due to str(ssl.SSLError()) not being stable across platforms.
    self.assertIn('path', message)
    self.assertIn('exception text', message)
    self.assertIn(text_to_check, message)

  @mock.patch('googlecloudsdk.core.log.error')
  def testHandleKnownErrorUnicode(self, log_error):
    c = self.MakeCli()
    c._HandleAllErrors(exceptions.Error('\xff'), 'path', 'GLOBAL')
    log_error.assert_called_with('(path) \\xff')

  @mock.patch.object(metrics, 'Error')
  def testDoesNotSetHttpStatusCode(self, mock_metrics_error):
    c = self.MakeCli()
    c._HandleAllErrors(exceptions.Error(''), 'path', None)
    mock_metrics_error.assert_called_once_with(
        'path', exceptions.Error, None, error_extra_info={'error_code': 1})

  @mock.patch.object(metrics, 'Error')
  def testSetsHttpStatusCode(self, mock_metrics_error):

    class TestHttpError(exceptions.Error):
      class TestHttpErrorPayload:
        status_code = 404

      def __init__(self):
        super(TestHttpError, self).__init__('')
        self.payload = self.TestHttpErrorPayload()

    c = self.MakeCli()
    c._HandleAllErrors(TestHttpError(), 'path', None)

    expected_extra_error_info = {'error_code': 1, 'http_status_code': 404}
    mock_metrics_error.assert_called_once_with(
        'path', TestHttpError, None, error_extra_info=expected_extra_error_info)


if __name__ == '__main__':
  test_case.main()
