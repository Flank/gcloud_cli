# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import extra_types
from dateutil import tz

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.logs import stream
from tests.lib import test_case
from tests.lib.surface.app import logs_base
from tests.lib.surface.app.logs_base import PROJECT


messages = apis.GetMessagesModule('logging', 'v2')


_UNIX_ZERO = '1970-01-01T01:00:00.000000000Z'
_LAST_YEAR = '2016-04-07T00:43:30Z'
_TWO_YEARS_AGO = '2016-04-07T00:43:30Z'
_NOW = '2017-01-23T22:39:01.947825Z'


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
    timestamp=_LAST_YEAR)

# From _LAST_YEAR
STANDARD_OUTPUT = '2016-04-07 00:43:30 s1[v1]  "POST /page -" 202'


class MockLogFetcher(stream.LogFetcher):
  """Mocks the streaming library."""

  def __init__(self, filters=None, polling_interval=5, continue_func=None,
               continue_interval=None, num_prev_entries=None):
    """Sets the continue_func to return after just one poll."""
    continue_values = [True, False]
    continue_func = lambda x: continue_values.pop(0)
    super(MockLogFetcher, self).__init__(filters,
                                         polling_interval, continue_func,
                                         continue_interval,
                                         num_prev_entries)


# Streaming logic testing in tests/unit/command_lib/logs/stream_test.py
# Formatting and API call testing in tests/unit/surface/app/logs/read_test.py
class StreamLogsTest(logs_base.LogsTestBase):
  """Tests 'app logs tail' command."""

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.util.times.LOCAL', tz.tzutc())
    self.StartPatch('time.sleep')
    self.StartPatch('googlecloudsdk.command_lib.logs.stream.LogFetcher',
                    MockLogFetcher)
    self.lower_bound = self.StartObjectPatch(
        stream.LogPosition, 'GetFilterLowerBound',
        return_value='timestamp>="{}"'.format(_UNIX_ZERO))
    self.upper_bound = self.StartObjectPatch(
        stream.LogPosition, 'GetFilterUpperBound',
        return_value='timestamp<"{}"'.format(_NOW))
    self.unix_zero_filter = self._FilterWithTimestamp(_UNIX_ZERO, _NOW)
    self.last_year_filter = self._FilterWithTimestamp(_LAST_YEAR, _NOW)
    self.empty_response = messages.ListLogEntriesResponse(entries=[])

  def _FilterWithTimestamp(self, start, end):
    return '{f} AND timestamp>="{start}" AND timestamp<"{end}"'.format(
        f=self.default_filter, start=_UNIX_ZERO, end=_NOW)

  def testTailLogsFlex(self):
    """Tests reading logs from a Flex app."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[FLEX_LOG])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.default_filter, page_size=100,
                            order_by='timestamp desc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        self.empty_response)
    self.Run('app logs tail')
    self.AssertErrContains('Waiting for new log entries')
    self.AssertOutputContains(FLEX_OUTPUT)

  def testTailLogsStandard(self):
    """Tests reading logs from a Standard app."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[STANDARD_LOG])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.default_filter, page_size=100,
                            order_by='timestamp desc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        self.empty_response)
    self.Run('app logs tail')
    self.AssertErrContains('Waiting for new log entries')
    self.AssertOutputContains(STANDARD_OUTPUT)

  def testTailLogsWithOffset(self):
    """Tests with 100 entries, so that the asc query starts at the 100:th."""
    entries = [STANDARD_LOG] * 99  # from 'last year'
    oldest_entry = copy.deepcopy(STANDARD_LOG)
    oldest_entry.timestamp = _TWO_YEARS_AGO
    entries.append(oldest_entry)

    response_entries = messages.ListLogEntriesResponse(
        entries=entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.default_filter, page_size=100,
                            order_by='timestamp desc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        response_entries)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=self.unix_zero_filter, page_size=1000,
                            order_by='timestamp asc'),
        self.empty_response)
    self.Run('app logs tail')
    self.AssertErrContains('Waiting for new log entries')
    self.AssertOutputContains(STANDARD_OUTPUT)


if __name__ == '__main__':
  test_case.main()
