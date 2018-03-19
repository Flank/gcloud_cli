# Copyright 2016 Google Inc. All Rights Reserved.
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

from googlecloudsdk.api_lib.error_reporting import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.error_reporting import base


class ErrorReportingTest(base.ErrorReportingTestBase):
  ERROR_MESSAGE = """Traceback (most recent call last):
                    File "<stdin>", line 1, in <module>
                    TypeError: time() takes no arguments (1 given)"""
  SERVICE = 'cloudsdk'
  VERSION = '100.0.0'
  PROJECT = 'cloudsdktest'
  PROJECT_NAME = 'projects/' + PROJECT
  URL = 'something'
  USER = 'someone'

  def SetUp(self):
    self.error_report_instance = util.ErrorReporting()
    self.api_messages = self.error_report_instance.api_messages
    self.service = self.api_messages.ServiceContext(
        service=self.SERVICE, version=self.VERSION)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=self.ERROR_MESSAGE)
    properties.VALUES.core.project.Set(self.PROJECT)
    self.addCleanup(properties.VALUES.core.project.Set, None)

  def testSendErrorMessageProjectProvided(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=self.PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.error_report_instance.ReportEvent(
        self.ERROR_MESSAGE, self.SERVICE, self.VERSION, self.PROJECT)

  def testSendErrorMessageNoProject(self):
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=self.PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.error_report_instance.ReportEvent(
        self.ERROR_MESSAGE, self.SERVICE, self.VERSION)

  def testGetGcloudProject(self):
    self.assertEquals(
        self.error_report_instance._GetGcloudProject(),
        self.PROJECT)

  def testMakeProjectName(self):
    self.assertEquals(
        self.error_report_instance._MakeProjectName(self.PROJECT),
        self.PROJECT_NAME)

  def testSendErrorMessageNoVersion(self):
    self.service = self.api_messages.ServiceContext(
        service=self.SERVICE)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=self.ERROR_MESSAGE)
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=self.PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.error_report_instance.ReportEvent(
        self.ERROR_MESSAGE, self.SERVICE)

  def testSendRequestURLWithError(self):
    self.service = self.api_messages.ServiceContext(
        service=self.SERVICE)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=self.ERROR_MESSAGE)
    self.error_event.context = self.api_messages.ErrorContext()
    self.error_event.context.httpRequest = self.api_messages.HttpRequestContext(
        url=self.URL)
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=self.PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.error_report_instance.ReportEvent(
        self.ERROR_MESSAGE, self.SERVICE, request_url=self.URL)

  def testSendUserLWithError(self):
    self.service = self.api_messages.ServiceContext(
        service=self.SERVICE)
    self.error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=self.service, message=self.ERROR_MESSAGE)
    self.error_event.context = self.api_messages.ErrorContext()
    self.error_event.context.user = self.USER
    self.mock_client.projects_events.Report.Expect(
        self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
            projectName=self.PROJECT_NAME,
            reportedErrorEvent=self.error_event),
        self.api_messages.ReportErrorEventResponse())
    self.error_report_instance.ReportEvent(
        self.ERROR_MESSAGE, self.SERVICE, user=self.USER)


if __name__ == '__main__':
  test_case.main()
