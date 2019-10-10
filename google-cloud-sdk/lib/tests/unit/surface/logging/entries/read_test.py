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

"""Tests of the 'logs' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.logging import util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base
from tests.lib.surface.logging import fixture
import mock


@mock.patch('datetime.datetime', new=fixture.FakeDatetime)
class EntriesReadTest(base.LoggingTestBase):

  def SetUp(self):
    self._entries = [
        self.msgs.LogEntry(logName='first-log'),
        self.msgs.LogEntry(logName='second-log')]

  def _setExpect(self, filter_spec, order_by='timestamp desc', page_size=1000):
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['projects/my-project'],
                                        filter=filter_spec,
                                        orderBy=order_by,
                                        pageSize=page_size),
        self.msgs.ListLogEntriesResponse(entries=self._entries))

  def testReadWithDefaultValues(self):
    default_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                             datetime.timedelta(days=1))
    self._setExpect('timestamp>="{0}"'.format(default_timestamp))
    generator = self.RunLogging('read --format=disable')
    self.assertEqual(list(generator), self._entries)

  def testReadLimit(self):
    default_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                             datetime.timedelta(days=1))
    self._setExpect('timestamp>="{0}"'.format(default_timestamp), page_size=1)
    generator = self.RunLogging('read --limit 1 --format=disable')
    self.assertEqual(list(generator), self._entries[:1])

  def testReadReverse(self):
    # Freshness is ignored for ASC ordering.
    self._setExpect(None, order_by='timestamp asc')
    self.RunLogging('read --order=ASC')

  def testReadTimestampFilter(self):
    # Freshness is ignored for filters with timestamps.
    self._setExpect('abla timestamp="2000-01-01T00:00:00Z"')
    self.RunLogging('read \'abla timestamp="2000-01-01T00:00:00Z"\'')

  def testReadFilters(self):
    custom_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                            datetime.timedelta(hours=10))
    self._setExpect('timestamp>="{0}" AND (severity=INFO logName=my-log)'
                    .format(custom_timestamp))
    self.RunLogging('read "severity=INFO logName=my-log" --freshness=10h')

  def testReadOrganizationEntries(self):
    default_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                             datetime.timedelta(days=1))
    default_filter = 'timestamp>="{0}"'.format(default_timestamp)
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['organizations/123'],
                                        filter=default_filter,
                                        orderBy='timestamp desc',
                                        pageSize=1000),
        self.msgs.ListLogEntriesResponse(entries=self._entries))
    generator = self.RunLogging('read --organization 123 --format=disable')
    self.assertEqual(list(generator), self._entries)

  def testReadFolderEntries(self):
    default_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                             datetime.timedelta(days=1))
    default_filter = 'timestamp>="{0}"'.format(default_timestamp)
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['folders/123'],
                                        filter=default_filter,
                                        orderBy='timestamp desc',
                                        pageSize=1000),
        self.msgs.ListLogEntriesResponse(entries=self._entries))
    generator = self.RunLogging('read --folder 123 --format=disable')
    self.assertEqual(list(generator), self._entries)

  def testReadBillingAccountEntries(self):
    default_timestamp = util.FormatTimestamp(fixture.MOCK_UTC_TIME -
                                             datetime.timedelta(days=1))
    default_filter = 'timestamp>="{0}"'.format(default_timestamp)
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['billingAccounts/123'],
                                        filter=default_filter,
                                        orderBy='timestamp desc',
                                        pageSize=1000),
        self.msgs.ListLogEntriesResponse(entries=self._entries))
    generator = self.RunLogging('read --billing-account 123 --format=disable')
    self.assertEqual(list(generator), self._entries)

  def testReadConflictingFlags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLogging('read --organization 123 --folder 456')

  def testReadNoPerms(self):
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['projects/my-project'],
                                        orderBy='timestamp asc',
                                        pageSize=3),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('read --order=ASC --limit=3')

  def testReadNoProject(self):
    self.RunWithoutProject('read')

  def testReadNoAuth(self):
    self.RunWithoutAuth('read')


if __name__ == '__main__':
  test_case.main()
