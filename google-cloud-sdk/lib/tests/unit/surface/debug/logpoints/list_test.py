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

"""Tests for the 'debug targets list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base
from six.moves import range


class ListTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testListWhenEmpty(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    result = self.RunDebug(['logpoints', 'list'])

    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=True, include_inactive=True,
        restrict_to_type=debug.Debugger.LOGPOINT_TYPE)
    self.assertEqual([], list(result))

  def testList(self):
    logpoints = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                          return_value=logpoints)
    self.RunDebug(['logpoints', 'list'])
    for l in logpoints:
      self.AssertOutputContains(l.id)
    self.AssertOutputContains(
        'USER_EMAIL LOCATION CONDITION LOG_LEVEL LOG_MESSAGE_FORMAT ID STATUS',
        normalize_space=True)

  def testListIncludesExpiredUnlimited(self):
    now = times.Now(times.UTC)
    self.StartObjectPatch(times, 'Now', return_value=now)
    create_time = now - datetime.timedelta(days=2)
    logpoints = [
        self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), createTime=create_time.isoformat(),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            isFinalState=True, logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i))
        for i in range(0, 10)]
    # Set logpoint 0 to a final time before well in the past.
    logpoints[0].finalTime = (
        now - datetime.timedelta(days=1, minutes=1)).isoformat()
    logpoints = [self.debuggee.AddTargetInfo(lp) for lp in logpoints]

    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=logpoints)
    self.RunDebug(['logpoints', 'list', '--include-inactive=unlimited'])
    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=True, include_inactive=True,
        restrict_to_type=debug.Debugger.LOGPOINT_TYPE)

    for l in logpoints:
      self.AssertOutputContains(l.id)
    self.AssertOutputContains(
        'USER_EMAIL LOCATION CONDITION LOG_LEVEL LOG_MESSAGE_FORMAT ID STATUS',
        normalize_space=True)

  def testListIncludeExclude(self):
    now = times.Now(times.UTC)
    self.StartObjectPatch(times, 'Now', return_value=now)
    create_time = now - datetime.timedelta(hours=1, minutes=1)
    logpoints = [
        self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), createTime=create_time.isoformat(),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            isFinalState=True, logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i))
        for i in range(0, 10)]
    exclude_indices = [0, 2, 4, 5, 7, 9]
    include_indices = [1, 3, 6, 8]
    for e in exclude_indices:
      # Set to a time before the default cutoff (so it will be excluded).
      logpoints[e].finalTime = (
          now - datetime.timedelta(seconds=301)).isoformat()
    for i in include_indices:
      # Set to a time after the default cutoff (so it will be included).
      logpoints[i].finalTime = (
          now - datetime.timedelta(seconds=299)).isoformat()
    included_ids = [logpoints[i].id for i in include_indices]
    excluded_ids = [logpoints[e].id for e in exclude_indices]
    logpoints = [self.debuggee.AddTargetInfo(lp) for lp in logpoints]

    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=logpoints)
    self.RunDebug(['logpoints', 'list'])
    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=True, include_inactive=True,
        restrict_to_type=debug.Debugger.LOGPOINT_TYPE)

    for i in included_ids:
      self.AssertOutputContains(i)
    for e in excluded_ids:
      self.AssertOutputNotContains(e)

  def testListDefaultSort(self):
    # Verify that list is sorted by default with active logpoints first,
    # inactive logpoints next, and both groups sorted by creation time.
    logpoints = [
        self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i))
        for i in range(0, 10)]
    active_order = [7, 9, 0, 4, 2, 5]
    inactive_order = [1, 8, 6, 3]
    now = times.Now(times.UTC)
    self.StartObjectPatch(times, 'Now', return_value=now)
    base_time = now - datetime.timedelta(hours=1, minutes=1)
    offset_sec = 0
    for i in active_order:
      logpoints[i].createTime = (
          base_time + datetime.timedelta(seconds=offset_sec)).isoformat()
      offset_sec += 1
    offset_sec = 0
    for i in inactive_order:
      logpoints[i].isFinalState = True
      logpoints[i].createTime = (
          base_time + datetime.timedelta(seconds=offset_sec)).isoformat()
      logpoints[i].finalTime = now.isoformat()
      offset_sec += 1

    logpoints = [self.debuggee.AddTargetInfo(lp) for lp in logpoints]

    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=logpoints)
    self.RunDebug(['logpoints', 'list'])
    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=True, include_inactive=True,
        restrict_to_type=debug.Debugger.LOGPOINT_TYPE)

    # Look for all the IDs in the expected order. Remove '\n' characters
    # from the output because '.' doesn't match newline, and '(.|\s)' causes
    # the Python re.search function to time out.
    self.AssertOutputMatches(
        '.*'.join(logpoints[i].id for i in active_order + inactive_order),
        actual_filter=lambda s: s.replace('\n', ' '))

  def testListWithFormat(self):
    logpoints = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message $0 $1',
            expressions=['expr1-{0}'.format(i), 'expr2-{0}'.format(i)],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                          return_value=logpoints)
    self.RunDebug(['logpoints', 'list', '--format=value(logMessageFormat)'])
    for l in logpoints:
      self.AssertOutputContains(
          'message {{{0}}} {{{1}}}'.format(*l.expressions))

  def testListByOneLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['logpoints', 'list', '--location=.*:[0156789]'])
    list_mock.assert_called_once_with(
        ['.*:[0156789]'], resource_ids=[], include_all_users=True,
        include_inactive=True, restrict_to_type=debug.Debugger.LOGPOINT_TYPE)

  def testListByMultiLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['logpoints', 'list', '--location=.*:[01]',
                   '--location=.*:[23]'])
    list_mock.assert_called_once_with(
        ['.*:[01]', '.*:[23]'], resource_ids=[], include_all_users=True,
        include_inactive=True, restrict_to_type=debug.Debugger.LOGPOINT_TYPE)


if __name__ == '__main__':
  test_case.main()
