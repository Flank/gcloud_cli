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

"""Tests of the 'logs read' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.functions import base
from tests.lib.surface.functions import util as testutil


class FunctionsGetLogsTest(base.FunctionsTestBase):

  def SetUp(self):
    self.logging_msgs = core_apis.GetMessagesModule('logging', 'v2')
    self.mock_logging_client = mock.Client(
        core_apis.GetClientClass('logging', 'v2'))
    self.mock_logging_client.Mock()
    self.addCleanup(self.mock_logging_client.Unmock)
    self.log_entries = [
        self._createLogEntry('ERROR', 'f-1', 'e-1',
                             '2015-10-01T12:34:56.789012345Z', 'one'),
        self._createLogEntry('INFO', 'f-2', 'e-2',
                             '2015-10-02T12:34:56.789012345Z', 'two'),
        self._createLogEntry('DEBUG', 'f-3', 'e-3',
                             '2015-10-03T12:34:56.789012345Z', 'three'),
    ]
    self.output_log_lines = [
        self._createOutputLogLine('E', 'f-1', 'e-1', '2015-10-01 12:34:56.789',
                                  'one'),
        self._createOutputLogLine('I', 'f-2', 'e-2', '2015-10-02 12:34:56.789',
                                  'two'),
        self._createOutputLogLine('D', 'f-3', 'e-3', '2015-10-03 12:34:56.789',
                                  'three'),
    ]
    properties.VALUES.core.user_output_enabled.Set(False)

  def _createLogEntry(self, severity, function_name, execution_id, timestamp,
                      text, json_message=None):
    if (text is None) == (json_message is None):
      self.fail('Exactly one of text and jsonMessage should be None')
    resource_labels = self.logging_msgs.MonitoredResource.LabelsValue(
        additionalProperties=[
            self.logging_msgs.MonitoredResource.LabelsValue.AdditionalProperty(
                key='function_name', value=function_name)])
    resource = self.logging_msgs.MonitoredResource(
        type='cloud_function', labels=resource_labels)
    labels = self.logging_msgs.LogEntry.LabelsValue(
        additionalProperties=[
            self.logging_msgs.LogEntry.LabelsValue.AdditionalProperty(
                key='execution_id', value=execution_id)])
    json_payload = None
    if json_message is not None:
      json_payload = self.logging_msgs.LogEntry.JsonPayloadValue()
      json_payload.additionalProperties = [
          self.logging_msgs.LogEntry.JsonPayloadValue.AdditionalProperty(
              key='message',
              value=extra_types.JsonValue(string_value=json_message))
      ]

    return self.logging_msgs.LogEntry(
        severity=self.logging_msgs.LogEntry.SeverityValueValuesEnum(severity),
        resource=resource, labels=labels, timestamp=timestamp, textPayload=text,
        jsonPayload=json_payload)

  def _createLogFilter(self, function_name=None, execution_id=None,
                       min_severity=None, start_time=None, end_time=None,
                       region=None):
    if region is None:
      region = 'us-central1'
    log_filter = ('resource.type="cloud_function" '
                  'resource.labels.region="{0}" '
                  'logName:"cloud-functions"'.format(region))
    if function_name:
      log_filter += ' resource.labels.function_name="{0}"'.format(function_name)
    if execution_id:
      log_filter += ' labels.execution_id="{0}"'.format(execution_id)
    if min_severity:
      log_filter += ' severity>={0}'.format(min_severity)
    if start_time:
      log_filter += ' timestamp>="{0}"'.format(start_time)
    if end_time:
      log_filter += ' timestamp<="{0}"'.format(end_time)
    return log_filter

  def _createOutputLogLine(self, level, name, execution_id, time_utc, log):
    return dict(
        level=level,
        name=name,
        execution_id=execution_id,
        time_utc=time_utc,
        log=log,
    )

  def _setListLogEntriesResponse(self, log_filter, order, limit, log_entries):
    self.mock_logging_client.entries.List.Expect(
        self.logging_msgs.ListLogEntriesRequest(
            resourceNames=['projects/{0}'.format(self.Project())],
            filter=log_filter,
            orderBy='timestamp {0}'.format(order),
            pageSize=limit),
        self.logging_msgs.ListLogEntriesResponse(entries=log_entries))

  def _setListLogEntriesResponseWithException(self, log_filter, order, limit):
    self.mock_logging_client.entries.List.Expect(
        self.logging_msgs.ListLogEntriesRequest(
            resourceNames=['projects/{0}'.format(self.Project())],
            filter=log_filter,
            orderBy='timestamp {0}'.format(order),
            pageSize=limit),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))

  def _checkResult(self, actual, expected):
    for log in actual:
      self.assertEqual(log, expected.pop(0))
    self.assertFalse(expected)

  def testNoAuth(self):
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_AUTH_REGEXP):
      self.Run('functions logs read')

  def testNoEntries(self):
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 20, [])
    result = self.Run('functions logs read')
    self._checkResult(result, [])

  def testAllFunctions(self):
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    list(reversed(self.log_entries)))
    result = self.Run('functions logs read')
    self._checkResult(result, self.output_log_lines)

  def testSingleFunction(self):
    log_filter = self._createLogFilter(function_name='f-1')
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read f-1')
    self._checkResult(result, self.output_log_lines[0:1])

  def testSingleExecutionId(self):
    log_filter = self._createLogFilter(execution_id='e-1')
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read --execution-id=e-1')
    self._checkResult(result, self.output_log_lines[0:1])

  def testLimit(self):
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 1,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read --limit=1')
    self._checkResult(result, self.output_log_lines[0:1])

  def testMinLogLevel(self):
    log_filter = self._createLogFilter(min_severity='ERROR')
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read --min-log-level=ERROR')
    self._checkResult(result, self.output_log_lines[0:1])

  def testStartTime(self):
    log_filter = self._createLogFilter(start_time='2015-10-03T00:00:00.000000Z')
    self._setListLogEntriesResponse(log_filter, 'asc', 20,
                                    self.log_entries[-1:])
    result = self.Run('functions logs read --start-time="2015-10-03 00:00:00"')
    self._checkResult(result, self.output_log_lines[-1:])

  def testYendTime(self):
    log_filter = self._createLogFilter(end_time='2015-10-02T00:00:00.000000Z')
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read --end-time="2015-10-02 00:00:00"')
    self._checkResult(result, self.output_log_lines[0:1])

  def testStartAndEndTime(self):
    log_filter = self._createLogFilter(start_time='2015-10-01T00:00:00.000000Z',
                                       end_time='2015-10-02T00:00:00.000000Z')
    self._setListLogEntriesResponse(log_filter, 'asc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read '
                      '--start-time="2015-10-01 00:00:00" '
                      '--end-time="2015-10-02 00:00:00"')
    self._checkResult(result, self.output_log_lines[0:1])

  def testStartAndEndTimeAndLimit(self):
    log_filter = self._createLogFilter(start_time='2015-10-01T00:00:00.000000Z',
                                       end_time='2015-10-03T00:00:00.000000Z')
    self._setListLogEntriesResponse(log_filter, 'asc', 1, self.log_entries[0:1])
    result = self.Run('functions logs read '
                      '--start-time="2015-10-01 00:00:00" '
                      '--end-time="2015-10-03 00:00:00" '
                      '--limit=1')
    self._checkResult(result, self.output_log_lines[0:1])

  def testMissingData(self):
    log_entries = [
        self.logging_msgs.LogEntry(
            severity=None,
            labels=None,
            resource=None,
            timestamp=None,
            textPayload=None)
    ]
    output_log_lines = [dict(log=None)]
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 20, log_entries)
    result = self.Run('functions logs read')
    self._checkResult(result, output_log_lines)

  def testUnexpectedSeverity(self):
    log_entries = [
        self._createLogEntry('CRITICAL', 'f-1', 'e-1',
                             '2015-10-01T12:34:56.789012345Z', 'one')
    ]
    output_log_lines = [
        self._createOutputLogLine('CRITICAL', 'f-1', 'e-1',
                                  '2015-10-01 12:34:56.789', 'one')
    ]
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 20, log_entries)
    result = self.Run('functions logs read')
    self._checkResult(result, output_log_lines)

  def testRegions(self):
    log_filter = self._createLogFilter(function_name='f-1',
                                       region='asia-east1-a')
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    self.log_entries[0:1])
    result = self.Run('functions logs read f-1 --region asia-east1-a')
    self._checkResult(result, self.output_log_lines[0:1])

  def testShowExecutionIds(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    log_filter = self._createLogFilter()
    self._setListLogEntriesResponse(log_filter, 'desc', 20,
                                    list(reversed(self.log_entries)))
    self.Run('functions logs read')

    self.AssertOutputMatches(r'^LEVEL\s+NAME\s+EXECUTION_ID\s+TIME_UTC\s+LOG$')
    self.AssertOutputMatches(
        r'^E\s+f-1\s+e-1\s+2015-10-01\s+12:34:56.789\s+one$')
    self.AssertOutputMatches(
        r'^I\s+f-2\s+e-2\s+2015-10-02\s+12:34:56.789\s+two$')
    self.AssertOutputMatches(
        r'^D\s+f-3\s+e-3\s+2015-10-03\s+12:34:56.789\s+three$')

  def testJsonLogEntry(self):
    log_entries = [
        self._createLogEntry('CRITICAL', 'f-1', 'e-1',
                             '2015-10-01T12:34:56.789012345Z', text=None,
                             json_message='one')
    ]
    output_log_lines = [
        self._createOutputLogLine('CRITICAL', 'f-1', 'e-1',
                                  '2015-10-01 12:34:56.789', 'one')
    ]
    log_filter = self._createLogFilter(region='us-central1')
    self._setListLogEntriesResponse(log_filter, 'desc', 20, log_entries)
    result = self.Run('functions logs read')
    self._checkResult(result, output_log_lines)


class FunctionsGetLogsWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testNoProject(self):
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_PROJECT_REGEXP):
      self.Run('functions logs read')

if __name__ == '__main__':
  test_case.main()
