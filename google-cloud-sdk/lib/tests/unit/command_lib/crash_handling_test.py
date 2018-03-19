# -*- coding: utf-8 -*-
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

"""Tests for error reporting."""


import traceback
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.command_lib import crash_handling
from googlecloudsdk.core import config
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case


EXAMPLE_TRACEBACK = """\
Traceback (most recent call last):
  File "/fake/file/path/google-cloud-sdk/hello.py", line 3, in <module>
    main()
  File "/fake/file/path/google-cloud-sdk/hello.py", line 2, in main
    some.method()
  File "/fake/file/path/google-cloud-sdk/hello.py", line 1, in method
    raise Exception('some exception')
Exception: some exception
"""

EXAMPLE_TRACEBACK_SERIALIZED = (
    r'Traceback (most recent call last):\n'
    r'  File \"google-cloud-sdk/hello.py\", line 3, in <module>\n'
    r'    main()\n'
    r'  File \"google-cloud-sdk/hello.py\", line 2, in main\n'
    r'    some.method()\n'
    r'  File \"google-cloud-sdk/hello.py\", line 1, in method\n'
    r"    raise Exception('some exception')\n"
    r'Exception\n')


CID = 'randomly-generated-id-adsfad'
COMMAND = 'command'


class LogAndExceptionsAndMessages(cli_test_base.CliTestBase):

  def SetUp(self):
    self.report_error_mock = self.StartObjectPatch(
        crash_handling, 'ReportError')

  def testExceptionImportErrorRunCommand(self):
    # We want to suggest reinstall here and skip error reporting
    msg = 'Example exception message text'
    exception = command_loading.CommandLoadFailure('gcloud version',
                                                   ImportError(msg))
    crash_handling.HandleGcloudCrash(exception)
    self.report_error_mock.assert_not_called()
    self.AssertErrContains('gcloud failed to load')
    self.AssertErrContains('gcloud components reinstall')
    self.AssertErrContains('https://cloud.google.com/sdk/')
    self.AssertErrNotContains(r'gcloud feedback')

  def testHandleGcloudCrashUsageFalseProperty(self):
    # disable_usage_reporting is set to False
    msg = 'Example exception message text'
    exception = Exception(msg)
    properties.VALUES.core.disable_usage_reporting.Set(False)
    crash_handling.HandleGcloudCrash(exception)
    self.report_error_mock.assert_called_with(exception, is_crash=True)
    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')

  def testHandleGcloudCrashUsageFalsePropertyWithUnicodeMessage(self):
    # disable_usage_reporting is set to False
    self.SetEncoding('utf8')
    msg = u'Example Ṳᾔḯ¢◎ⅾℯ exception message text'
    exception = Exception(msg)
    properties.VALUES.core.disable_usage_reporting.Set(False)
    crash_handling.HandleGcloudCrash(exception)
    self.report_error_mock.assert_called_with(exception, is_crash=True)
    self.AssertErrContains(msg)
    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')


class TestingErrorReporting(cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartObjectPatch(traceback, 'format_exc',
                          return_value=EXAMPLE_TRACEBACK)
    self.report_event_mock = self.StartObjectPatch(
        metrics, 'CustomBeacon')

  def testHandleGcloudCrashUsageTrueProperty(self):
    # disable_usage_reporting is set to True
    msg = 'Example exception message text'
    exception = Exception(msg)
    crash_handling.HandleGcloudCrash(exception)
    self.report_event_mock.assert_not_called()
    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')

  def testCraReportCrashWithCorrectException(self):
    properties.VALUES.core.disable_usage_reporting.Set(False)
    properties.VALUES.metrics.command_name.Set(COMMAND)
    self.StartObjectPatch(metrics, 'GetCIDIfMetricsEnabled', return_value=CID)

    crash_handling.HandleGcloudCrash(Exception())

    self.assertTrue(self.report_event_mock.called)
    args, _ = self.report_event_mock.call_args_list[0]
    self.assertTrue(args[0].startswith(
        'https://clouderrorreporting.googleapis.com/v1beta1/projects/cloud-sdk'
        '-crashes/events:report?'))
    self.assertEqual(args[1], 'POST')
    self.assertEqual(
        args[2],
        '{"context": {"httpRequest": {"url": "command"}, "user": '
        '"randomly-generated-id-adsfad"}, "message": "%s", "serviceContext": {'
        '"service": "gcloud", "version": "%s"}}'
        % (EXAMPLE_TRACEBACK_SERIALIZED, config.CLOUD_SDK_VERSION))
    content_length = str(447 + len(config.CLOUD_SDK_VERSION))
    self.assertEqual(
        args[3],
        {'content-length': content_length, 'content-type': 'application/json',
         'accept-encoding': 'gzip, deflate', 'accept': 'application/json',
         'user-agent': 'x_Tw5K8nnjoRAqULM9PFAC2b'})

    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')

  def testReportErrorWithCorrectException(self):
    properties.VALUES.core.disable_usage_reporting.Set(False)
    properties.VALUES.metrics.command_name.Set(COMMAND)
    self.StartObjectPatch(metrics, 'GetCIDIfMetricsEnabled', return_value=CID)

    crash_handling.ReportError(Exception(), is_crash=False)

    self.assertTrue(self.report_event_mock.called)
    args, _ = self.report_event_mock.call_args_list[0]
    self.assertTrue(args[0].startswith(
        'https://clouderrorreporting.googleapis.com/v1beta1/projects/cloud-sdk'
        '-user-errors/events:report?'))
    self.assertEqual(args[1], 'POST')
    self.assertEqual(
        args[2],
        '{"context": {"httpRequest": {"url": "command"}, "user": '
        '"randomly-generated-id-adsfad"}, "message": "%s", "serviceContext": {'
        '"service": "gcloud", "version": "%s"}}'
        % (EXAMPLE_TRACEBACK_SERIALIZED, config.CLOUD_SDK_VERSION))
    content_length = str(447 + len(config.CLOUD_SDK_VERSION))
    self.assertEqual(
        args[3],
        {'content-length': content_length, 'content-type': 'application/json',
         'accept-encoding': 'gzip, deflate', 'accept': 'application/json',
         'user-agent': 'x_Tw5K8nnjoRAqULM9PFAC2b'})

  def testDisableMetricsDontSendErrorReport(self):
    crash_handling.HandleGcloudCrash(Exception())

    self.report_event_mock.assert_not_called()

    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')

  def testMetricsError(self):
    self.report_event_mock.side_effect = apitools_exceptions.Error
    properties.VALUES.core.disable_usage_reporting.Set(False)
    properties.VALUES.metrics.command_name.Set(COMMAND)
    self.StartObjectPatch(metrics, 'GetCIDIfMetricsEnabled', return_value=CID)

    crash_handling.HandleGcloudCrash(Exception())

    self.report_event_mock.assert_called_once()

    self.AssertErrContains('gcloud crashed')
    self.AssertErrContains('If you would like to report this issue, please run '
                           'the following command:')
    self.AssertErrContains('gcloud feedback')
    self.AssertErrContains('To check gcloud for common problems, please run '
                           'the following command:')
    self.AssertErrContains('gcloud info --run-diagnostics')


if __name__ == '__main__':
  test_case.main()
