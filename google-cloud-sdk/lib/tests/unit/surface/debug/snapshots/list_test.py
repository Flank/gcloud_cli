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


class ListTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self._fake_now = times.Now(times.UTC)

  def testListWhenEmpty(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    result = self.RunDebug(['snapshots', 'list'])

    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=False, include_inactive=True,
        restrict_to_type=debug.Debugger.SNAPSHOT_TYPE)
    self.assertEqual([], list(result))

  def testList(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    self.StartObjectPatch(times, 'Now', return_value=self._fake_now)
    now = self._fake_now
    snapshots[1].isFinalState = True
    snapshots[1].finalTime = (now - datetime.timedelta(seconds=299)).isoformat()
    snapshots[9].isFinalState = True
    snapshots[9].finalTime = (now - datetime.timedelta(seconds=301)).isoformat()
    self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                          return_value=snapshots)
    self.RunDebug(['snapshots', 'list'])
    for l in snapshots[0:8]:
      self.AssertOutputContains(l.id)
    self.AssertOutputNotContains(snapshots[9].id)
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testListNoInactive(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=snapshots)
    self.RunDebug(['snapshots', 'list', '--include-inactive=0'])
    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=False, include_inactive=False,
        restrict_to_type=debug.DebugObject.SNAPSHOT_TYPE)

  def testListAllInactive(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    self.StartObjectPatch(times, 'Now', return_value=self._fake_now)
    now = self._fake_now
    snapshots[1].isFinalState = True
    snapshots[1].finalTime = (now - datetime.timedelta(seconds=299)).isoformat()
    snapshots[9].isFinalState = True
    snapshots[9].finalTime = (now - datetime.timedelta(seconds=301)).isoformat()
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=snapshots)
    self.RunDebug(['snapshots', 'list', '--include-inactive=unlimited'])
    list_mock.assert_called_once_with(
        None, resource_ids=[], include_all_users=False, include_inactive=True,
        restrict_to_type=debug.DebugObject.SNAPSHOT_TYPE)
    for l in snapshots:
      self.AssertOutputContains(l.id)
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testListByLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['snapshots', 'list', '--location=.*:[0156789]'])
    list_mock.assert_called_once_with(
        ['.*:[0156789]'], resource_ids=[], include_all_users=False,
        include_inactive=True, restrict_to_type=debug.Debugger.SNAPSHOT_TYPE)

  def testListByMultiLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['snapshots', 'list', '--location=.*:[01]',
                   '--location=.*:[23]'])
    list_mock.assert_called_once_with(
        ['.*:[01]', '.*:[23]'], resource_ids=[], include_all_users=False,
        include_inactive=True, restrict_to_type=debug.Debugger.SNAPSHOT_TYPE)


if __name__ == '__main__':
  test_case.main()
