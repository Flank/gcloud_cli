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

"""Tests for `gcloud app logs` command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types

from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.app import logs_base
from tests.lib.surface.app.logs_base import PROJECT

messages = apis.GetMessagesModule('logging', 'v2')
APP_ENTRY_1 = messages.LogEntry(
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

APP_ENTRY_1_FORMATTED = '2016-04-06 00:42:05 s1[v1]  Message 1.'

APP_ENTRY_2 = messages.LogEntry(
    logName=('projects/{0}/logs/stderr'
             .format(PROJECT)),
    insertId='ID002',
    resource=messages.MonitoredResource(
        type='gae_app',
        labels=messages.MonitoredResource.LabelsValue(additionalProperties=[
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='module_id', value='s1'),
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='version_id', value='v1'),
            ])),
    textPayload='Message 2.',
    timestamp='2016-04-06T00:43:30Z')

APP_ENTRY_2_FORMATTED = '2016-04-06 00:43:30 s1[v1]  Message 2.'

TEXT_ENTRY_1 = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID003',
    textPayload='Random msg.',
    timestamp='2016-04-06T00:44:30Z')

TEXT_ENTRY_1_FORMATTED = '2016-04-06 00:44:30 Random msg.'

UNFORMATTABLE_ENTRY_1 = messages.LogEntry(
    insertId='ID004',
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fcrash.log'
             .format(PROJECT)),
    timestamp='2016-04-07T00:44:30Z')

UNFORMATTABLE_ENTRY_1_FORMATTED = ('2016-04-07 00:44:30 < UNREADABLE LOG ENTRY '
                                   'ID004. OPEN THE DEVELOPER CONSOLE TO '
                                   'INSPECT. >')

UNICODE_ENTRY_1 = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID005',
    textPayload='Ṳᾔḯ¢◎ⅾℯ',
    timestamp='2016-04-06T00:44:30Z')

UNICODE_ENTRY_1_FORMATTED = '2016-04-06 00:44:30 Ṳᾔḯ¢◎ⅾℯ'

# Request log sometimes had project number instead of project ID, so mimic that
REQUEST_LOG_ENTRY_1 = messages.LogEntry(
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

REQUEST_LOG_ENTRY_1_FORMATTED = '2016-04-07 00:43:30 s1[v1]  "POST /page -" 202'

TIMESTAMP_ENTRY_MICROSECONDS = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID006',
    textPayload='Random msg.',
    timestamp='2016-04-06T00:44:30.000Z')

TIMESTAMP_ENTRY_MICROSECONDS_FORMATTED = '2016-04-06 00:44:30 Random msg.'

TIMESTAMP_ENTRY_MISMATCH = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID007',
    textPayload='Random msg.',
    timestamp='BAD-04-06T00:44:30.000Z')

TIMESTAMP_ENTRY_MISMATCH_FORMATTED = '????-??-?? ??:??:?? Random msg.'

TIMESTAMP_ENTRY_NANOSECONDS = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID008',
    textPayload='Random msg.',
    timestamp='2016-04-06T00:44:30.123456789Z')

TIMESTAMP_ENTRY_NANOSECONDS_FORMATTED = '2016-04-06 00:44:30 Random msg.'

TIMESTAMP_ENTRY_SECONDS = messages.LogEntry(
    logName=('projects/{0}/logs/appengine.googleapis.com%2Fstderr'
             .format(PROJECT)),
    insertId='ID009',
    textPayload='Random msg.',
    timestamp='2016-04-06T00:44:30Z')

TIMESTAMP_ENTRY_SECONDS_FORMATTED = '2016-04-06 00:44:30 Random msg.'

NGINX_LOG_ENTRY_1 = messages.LogEntry(
    logName='projects/1234567/logs/appengine.googleapis.com%2Fnginx.request',
    insertId='ID005',
    resource=messages.MonitoredResource(
        type='gae_app',
        labels=messages.MonitoredResource.LabelsValue(additionalProperties=[
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='module_id', value='s1'),
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='version_id', value='v1'),
            ])),
    jsonPayload=messages.LogEntry.JsonPayloadValue(additionalProperties=[
        messages.LogEntry.JsonPayloadValue.AdditionalProperty(
            key='key',
            value=extra_types.JsonValue(string_value='value')),
    ]),
    httpRequest=messages.HttpRequest(
        requestMethod='POST',
        requestUrl='/page',
        status=404,
    ),
    timestamp='2016-04-07T00:43:30Z')

NGINX_LOG_ENTRY_1_FORMATTED = '2016-04-07 00:43:30 s1[v1]  "POST /page" 404'

NGINX_LOG_ENTRY_2 = messages.LogEntry(
    logName='projects/1234567/logs/appengine.googleapis.com%2Fnginx.request',
    insertId='ID005',
    resource=messages.MonitoredResource(
        type='gae_app',
        labels=messages.MonitoredResource.LabelsValue(additionalProperties=[
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='module_id', value='s1'),
            messages.MonitoredResource.LabelsValue.AdditionalProperty(
                key='version_id', value='v1'),
            ])),
    jsonPayload=messages.LogEntry.JsonPayloadValue(additionalProperties=[
        messages.LogEntry.JsonPayloadValue.AdditionalProperty(
            key='key',
            value=extra_types.JsonValue(string_value='value')),
    ]),
    httpRequest=messages.HttpRequest(
        requestMethod='POST',
        status=404,
    ),
    timestamp='2016-04-07T00:43:30Z')

NGINX_LOG_ENTRY_2_FORMATTED = '2016-04-07 00:43:30 s1[v1]  "POST -" 404'


class LogsReadTest(logs_base.LogsTestBase):
  """Tests for `gcloud app logs read`."""

  def testDefaultAppEntries(self):
    """Test `gcloud app logs read` with no flags."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testDefaultUnformattableEntry(self):
    """Test command handles unformattable entries."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[UNFORMATTABLE_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    expected = '\n'.join([UNFORMATTABLE_ENTRY_1_FORMATTED])
    self.AssertOutputContains(expected)

  def testDefaultMixedEntries(self):
    """Test `gcloud app logs read` handles multiple kinds of entries."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[UNFORMATTABLE_ENTRY_1, TEXT_ENTRY_1, APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED,
                          APP_ENTRY_2_FORMATTED,
                          TEXT_ENTRY_1_FORMATTED,
                          UNFORMATTABLE_ENTRY_1_FORMATTED])
    self.AssertOutputContains(expected)

  def testDefaultWithPaging(self):
    """Test `gcloud app logs read` works with paging."""
    response_entries_1 = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2], nextPageToken='page_token_1')
    response_entries_2 = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(),
                                       response_entries_1)
    self.v2_client.entries.List.Expect(
        self._CreateRequest(page_token='page_token_1', page_size=199),
        response_entries_2)
    self.Run('app logs read')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testLimit(self):
    """Test `gcloud app logs read` with `--limit` flag.

    Limit is handled on the client side so make sure that --limit displays the
    right number of entries. In this case, we get three response entries, but
    limit is two so we should only show the two latest entries.
    """
    response_entries = messages.ListLogEntriesResponse(
        entries=[TEXT_ENTRY_1, APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(page_size=2),
                                       response_entries)
    self.Run('app logs read --limit=2')
    expected = '\n'.join([APP_ENTRY_2_FORMATTED, TEXT_ENTRY_1_FORMATTED])
    self.AssertOutputContains(expected)

  def testService(self):
    """Test command with --service flag."""
    log_filter = ('resource.type="gae_app"'
                  ' AND resource.labels.module_id="s1"'
                  ' AND ' + self.log_name_filter)
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --service=s1')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testVersion(self):
    """Test command with --version flag."""
    log_filter = ('resource.type="gae_app"'
                  ' AND resource.labels.version_id="v1"'
                  ' AND ' + self.log_name_filter)
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --version=v1')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testLevel(self):
    """Test command with --level flag."""
    log_filter = ('resource.type="gae_app"'
                  ' AND severity>=ERROR'
                  ' AND ' + self.log_name_filter)
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --level=error')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testLevelAny(self):
    """Test command with --level=any."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    # any=none for severity level, hence no extra filter
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read --level=any')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testServiceVersion(self):
    """Test command with --level and --service flags."""
    log_filter = ('resource.type="gae_app"'
                  ' AND resource.labels.module_id="s1"'
                  ' AND resource.labels.version_id="v1"'
                  ' AND ' + self.log_name_filter)
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --service=s1 --version=v1')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testServiceVersionLevel(self):
    """Test command with --service flag, --version, and --level."""
    log_filter = ('resource.type="gae_app"'
                  ' AND resource.labels.module_id="s1"'
                  ' AND resource.labels.version_id="v1"'
                  ' AND severity>=WARNING'
                  ' AND ' + self.log_name_filter)
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --service=s1 --version=v1 --level=warning')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testCustomLogs(self):
    """Test `gcloud app logs read` with --logs flag."""
    log_filter = (
        'resource.type="gae_app" AND logName=('
        '"projects/{project}/logs/appengine.googleapis.com%2Frequest_log" OR '
        '"projects/{project}/logs/appengine.googleapis.com%2Fsyslog")'
        .format(project=PROJECT))
    response_entries = messages.ListLogEntriesResponse(
        entries=[APP_ENTRY_2, APP_ENTRY_1])
    self.v2_client.entries.List.Expect(
        self._CreateRequest(log_filter=log_filter),
        response_entries)
    self.Run('app logs read --logs=request_log,syslog')
    expected = '\n'.join([APP_ENTRY_1_FORMATTED, APP_ENTRY_2_FORMATTED])
    self.AssertOutputContains(expected)

  def testRequestLogEntry(self):
    """Test that request log entries are correctly formatted."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[REQUEST_LOG_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    expected = REQUEST_LOG_ENTRY_1_FORMATTED
    self.AssertOutputContains(expected)

  def testUnicode(self):
    """Test that unicode entries are correctly formatted."""
    self.SetEncoding('utf8')
    response_entries = messages.ListLogEntriesResponse(
        entries=[UNICODE_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    expected = '\n'.join([UNICODE_ENTRY_1_FORMATTED])
    self.AssertOutputContains(expected)

  def testAcceptedTimestamp(self):
    """Test that a response with timestamps in microseconds is accepted."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[TIMESTAMP_ENTRY_MICROSECONDS])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(TIMESTAMP_ENTRY_MICROSECONDS_FORMATTED)

  def testIncorrectTimestamp(self):
    """Test that a response with an incorrect timestamp format is handled."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[TIMESTAMP_ENTRY_MISMATCH])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(TIMESTAMP_ENTRY_MISMATCH_FORMATTED)

  def testNanosecondTimestamp(self):
    """Test that a response with timestamps in microseconds is accepted."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[TIMESTAMP_ENTRY_NANOSECONDS])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(TIMESTAMP_ENTRY_NANOSECONDS_FORMATTED)

  def testSecondTimestamp(self):
    """Test that a response with timestamps in seconds is accepted."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[TIMESTAMP_ENTRY_SECONDS])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(TIMESTAMP_ENTRY_SECONDS_FORMATTED)

  def testNginx(self):
    """Response with an nginx entry."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[NGINX_LOG_ENTRY_1])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(NGINX_LOG_ENTRY_1_FORMATTED)

  def testNginxMissingField(self):
    """Response with an nginx entry with missing field."""
    response_entries = messages.ListLogEntriesResponse(
        entries=[NGINX_LOG_ENTRY_2])
    self.v2_client.entries.List.Expect(self._CreateRequest(), response_entries)
    self.Run('app logs read')
    self.AssertOutputContains(NGINX_LOG_ENTRY_2_FORMATTED)


if __name__ == '__main__':
  test_case.main()
