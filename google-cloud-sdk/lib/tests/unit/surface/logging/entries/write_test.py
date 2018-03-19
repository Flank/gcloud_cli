# Copyright 2014 Google Inc. All Rights Reserved.
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

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base
from tests.lib.surface.logging import fixture

v2 = core_apis.GetMessagesModule('logging', 'v2')


class EntriesWriteTest(base.LoggingTestBase):

  def _setExpect(self, log_entry):
    if not log_entry.logName:
      log_entry.logName = 'projects/my-project/logs/my-log'
    self.mock_client_v2.entries.Write.Expect(
        v2.WriteLogEntriesRequest(entries=[log_entry]),
        v2.Empty())

  def testWriteWithDefaults(self):
    self._setExpect(fixture.CreateLogEntry('my-payload'))
    self.RunLogging('write my-log my-payload')
    self.AssertErrContains('Created log entry.')

  def testWriteSeverity(self):
    self._setExpect(fixture.CreateLogEntry('my-payload', severity='critical'))
    self.RunLogging('write my-log my-payload --severity=CRITICAL')
    self.AssertErrContains('Created log entry.')

  def testWriteInvalidSeverity(self):
    expected = (r"argument --severity: Invalid choice: '100'\." '\n\n'
                r'Valid choices are \[.*INFO.*\]')
    with self.AssertRaisesArgumentErrorRegexp(expected):
      self.RunLogging('write my-log my-payload --severity=100')

  def testWriteStructuredLog(self):
    self._setExpect(fixture.CreateLogEntry('my-payload', payload_type='struct'))
    self.RunLogging('write my-log \'{"message": "my-payload"}\' '
                    '--payload-type=json')
    self.AssertErrContains('Created log entry.')

  def testWriteInvalidJson(self):
    expected = r'Invalid JSON value: .*'
    with self.assertRaisesRegexp(util.InvalidJSONValueError, expected):
      # Missing closing bracket.
      self.RunLogging('write my-log \'{"message": "my-payload"\' '
                      '--payload-type=json')

  def testWriteNestedLogName(self):
    entry = fixture.CreateLogEntry('my-payload')
    entry.logName = 'projects/my-project/logs/my-log%2Fnested'
    self._setExpect(entry)
    self.RunLogging('write my-log/nested my-payload')

  def testWriteLogResourceName(self):
    self._setExpect(fixture.CreateLogEntry('my-payload'))
    self.RunLogging('write projects/my-project/logs/my-log my-payload')

  def testWriteNoPerms(self):
    entry = fixture.CreateLogEntry('my-payload')
    entry.logName = 'projects/my-project/logs/my-log'

    self.mock_client_v2.entries.Write.Expect(
        v2.WriteLogEntriesRequest(entries=[entry]),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('write my-log my-payload')

  def testWriteNoProject(self):
    self.RunWithoutProject('write my-log my-payload')

  def testWriteNoAuth(self):
    self.RunWithoutAuth('write my-log my-payload')


if __name__ == '__main__':
  test_case.main()
