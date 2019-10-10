# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for the 'report error' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.error_reporting import util
from googlecloudsdk.command_lib.error_reporting import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.error_reporting import base


ERROR_MESSAGE = 'error'
SERVICE = 'some_service'
VERSION = '1.0'
PROJECT = 'testproject'
PROJECT_NAME = 'projects/' + PROJECT
FILENAME = 'error.txt'
BASE_COMMAND = (' events report --service {0}').format(SERVICE)
COMMAND_WITH_MESSAGE = BASE_COMMAND + ' --message {0}'.format(ERROR_MESSAGE)


class ReportTest(base.ErrorReportingTestBase):

  def SetUp(self):
    self.error_report_instance = util.ErrorReporting()
    self.api_messages = self.error_report_instance.api_messages
    self.service = self.api_messages.ServiceContext(
        service=SERVICE)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=ERROR_MESSAGE)
    properties.VALUES.core.project.Set(PROJECT)
    self.addCleanup(properties.VALUES.core.project.Set, None)

  def testRunReportNoProject(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.RunCmd(COMMAND_WITH_MESSAGE)

  def testRunReportGivenProject(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.RunCmd(COMMAND_WITH_MESSAGE + ' --project '+ PROJECT)

  def testRunReportErrorFile(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    temp_path = self.CreateTempDir('testing')
    self.Touch(temp_path, FILENAME, ERROR_MESSAGE)
    file_path = temp_path + os.sep + FILENAME
    self.RunCmd(BASE_COMMAND + ' --message-file ' + file_path)

  def testRunReportFileOpenError(self):
    expected = r'Failed to open file \[{}\]:'.format(FILENAME)
    with self.AssertRaisesExceptionRegexp(
        exceptions.CannotOpenFileError, expected):
      self.RunCmd(BASE_COMMAND + ' --message-file ' + FILENAME)

  def testRunReportWithMutuallyExclusiveArgs(self):
    temp_path = self.CreateTempDir('testing')
    self.Touch(temp_path, FILENAME, ERROR_MESSAGE)
    file_path = temp_path + os.sep + FILENAME
    with self.AssertRaisesArgumentErrorMatches(
        'argument --message: Exactly one of (--message | --message-file) '
        'must be specified.'):
      self.RunCmd(COMMAND_WITH_MESSAGE + ' --message-file ' + file_path)

  def testRunReportProjectGetsSet(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.RunCmd(COMMAND_WITH_MESSAGE + ' --project '+ PROJECT)
    self.assertEqual(properties.VALUES.core.project.Get(
        required=True), PROJECT)

  def testRunReportVersionProvided(self):
    self.service = self.api_messages.ServiceContext(service=SERVICE,
                                                    version=VERSION)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=ERROR_MESSAGE)
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.RunCmd(COMMAND_WITH_MESSAGE + ' --service-version {0}'.format(VERSION))


if __name__ == '__main__':
  test_case.main()
