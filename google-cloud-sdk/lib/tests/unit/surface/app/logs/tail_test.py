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
"""app logs tail tests."""
from apitools.base.py import extra_types
from dateutil import tz

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.logs import stream
from tests.lib import test_case
from tests.lib.surface.app import logs_base
from tests.lib.surface.app.logs_base import PROJECT


messages = apis.GetMessagesModule('logging', 'v2')

FLEX_LOG = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstdout'
             .format(PROJECT)),
    insertId='ID001',
    resource=messages.MonitoredResource(
        type='gae_app',
        labels=messages.MonitoredResource.LabelsValue(additionalProperties=[
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='module_id', value='s1'),
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='version_id', value='v1'),
            ])),
    textPayload='Message 1.',
    timestamp='2016-04-06T00:42:05Z')

FLEX_OUTPUT = '2016-04-06 00:42:05 s1[v1]  Message 1.'

STANDARD_LOG = messages.LogEntry(
    logName='projects/1234567/logs/appengine.googleapis.com%2Frequest_log',
    insertId='ID005',
    resource=messages.MonitoredResource(
        type='gae_app',
        labels=messages.MonitoredResource.LabelsValue(additionalProperties=[
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='module_id', value='s1'),
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='version_id', value='v1'),
            ])),
    protoPayload=messages.LogEntry.ProtoPayloadValue(additionalProperties=[
        messages.LogEntry.ProtoPayloadValue.AdditionalProperty(
            key='method',
            value=extra_types.JsonValue(string_value='POST')),
        messages.LogEntry.ProtoPayloadValue.AdditionalProperty(
            key='resource',
            value=extra_types.JsonValue(string_value='/page')),
        messages.LogEntry.ProtoPayloadValue.AdditionalProperty(
            key='status',
            value=extra_types.JsonValue(integer_value=202)),
    ]),
    timestamp='2016-04-07T00:43:30Z')

STANDARD_OUTPUT = '2016-04-07 00:43:30 s1[v1]  "POST /page -" 202'


class MockLogFetcher(stream.LogFetcher):
  """Mocks the streaming library."""

  def __init__(self, filters=None, polling_interval=5, continue_func=None):
    """Sets the continue_func to return after just one poll."""
    continue_values = [True, False]
    continue_func = lambda x: continue_values.pop(0)
    super(MockLogFetcher, self).__init__(filters,
                                         polling_interval, continue_func)


# Streaming logic testing in tests/unit/command_lib/logs/stream_test.py
# Formatting and API call testing in tests/unit/surface/app/logs/read_test.py
class StreamLogsTest(logs_base.LogsTestBase):
  """Tests 'app logs tail' command."""

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.util.times.LOCAL', tz.tzutc())
    self.StartPatch('time.sleep')
    self.StartPatch('googlecloudsdk.command_lib.logs.stream.LogFetcher',
                    MockLogFetcher)
    self.StartPatch('googlecloudsdk.command_lib.logs.stream.'
                    'LogPosition.GetFilterLowerBound',
                    return_value='timestamp>="1970-01-01T01:00:00.000000000Z"')
    self.StartPatch('googlecloudsdk.command_lib.logs.stream.'
                    'LogPosition.GetFilterUpperBound',
                    return_value='timestamp<"2017-01-23T22:39:01.947825Z"')
    self.timestamp_filter = 'timestamp>="{0}" AND timestamp<"{1}"'.format(
        '1970-01-01T01:00:00.000000000Z',
        '2017-01-23T22:39:01.947825Z')
    self.log_filter = self.default_filter + ' AND ' + self.timestamp_filter
    self.empty_response = messages.ListLogEntriesResponse(entries=[])

  def testTailLogsFlex(self):
    """Tests reading logs from a Flex app."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[FLEX_LOG])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.log_filter, page_size=1000,
                            order_by=u'timestamp asc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.log_filter, page_size=1000,
                            order_by=u'timestamp asc'),
        self.empty_response)
    self.Run('app logs tail')
    self.AssertErrContains('Waiting for new log entries')
    self.AssertOutputContains(FLEX_OUTPUT)

  def testTailLogsStandard(self):
    """Tests reading logs from a Standard app."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[STANDARD_LOG])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.log_filter, page_size=1000,
                            order_by=u'timestamp asc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.log_filter, page_size=1000,
                            order_by=u'timestamp asc'),
        self.empty_response)
    self.Run('app logs tail')
    self.AssertErrContains('Waiting for new log entries')
    self.AssertOutputContains(STANDARD_OUTPUT)


if __name__ == '__main__':
  test_case.main()
