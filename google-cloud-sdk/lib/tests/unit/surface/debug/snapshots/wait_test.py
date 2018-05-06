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

"""Tests for the 'debug targets wait' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.debug import debug
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base


class WaitTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testWaitForNothing(self):
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[])
    wait_mock = self.StartObjectPatch(debug.Debuggee,
                                      'WaitForMultipleBreakpoints')
    result = self.RunDebug(['snapshots', 'wait', '--location=.*'])

    self.assertFalse(wait_mock.called)
    self.assertEqual([], list(result))
    self.AssertErrContains('No snapshots')

  def testWaitForAnythingAndFail(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [s.id for s in snapshots]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(debug.Debuggee,
                                      'WaitForMultipleBreakpoints',
                                      return_value=[])
    result = self.RunDebug(['snapshots', 'wait', '--location=.*'])

    wait_mock.assert_called_once_with(ids, wait_all=False, timeout=None)
    self.assertEqual([], list(result))
    self.AssertErrContains('No snapshots')

  def testWaitOne(self):
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id-0', condition='cond',
        expressions=['expr1', 'expr2'],
        location=self.messages.SourceLocation(path='myfile', line=123)))
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[snapshot])
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints', return_value=[snapshot])
    self.RunDebug(['snapshots', 'wait', snapshot.id])
    wait_mock.assert_called_once_with([snapshot.id], wait_all=False,
                                      timeout=None)
    self.AssertErrContains('Waiting for 1 snapshot.')
    self.AssertOutputContains(snapshot.id)
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitAnyExplicit(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [s.id for s in snapshots]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints', return_value=snapshots)
    self.RunDebug(['snapshots', 'wait'] + ids)
    wait_mock.assert_called_once_with(ids, wait_all=False, timeout=None)
    self.AssertErrContains('Waiting for 10 snapshots.')
    for s in snapshots:
      self.AssertOutputContains(s.id)
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitAllUsers(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            userEmail='dummy{0}@nohost.google.com'.format(i),
            isFinalState=True, expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [s.id for s in snapshots]
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints', return_value=snapshots)
    self.RunDebug(['snapshots', 'wait', '--all-users', '--location=myfile'])
    wait_mock.assert_called_once_with(ids, wait_all=False, timeout=None)
    list_mock.assert_called_once_with(['myfile'], resource_ids=[],
                                      include_all_users=True)
    self.AssertErrContains('Waiting for 10 snapshots.')
    for s in snapshots:
      self.AssertOutputContains(s.id)
    self.AssertOutputContains(
        'STATUS USER_EMAIL LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitAll(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'], isFinalState=True,
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [s.id for s in snapshots]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints',
        return_value=snapshots)
    self.RunDebug(['snapshots', 'wait', '--all', '--location=myfile'])
    wait_mock.assert_called_once_with(ids, wait_all=True, timeout=None)
    self.AssertErrContains('Waiting for 10 snapshots.')
    for s in snapshots:
      self.AssertOutputContains(s.id)
    self.AssertErrNotContains('Partial results')
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitAllById(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'], isFinalState=True,
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [s.id for s in snapshots]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints',
        return_value=snapshots)
    self.RunDebug(['snapshots', 'wait', '--all'] + ids)
    wait_mock.assert_called_once_with(ids, wait_all=True, timeout=None)
    self.AssertErrContains('Waiting for 10 snapshots.')
    for s in snapshots:
      self.AssertOutputContains(s.id)
    self.AssertErrNotContains('Partial results')
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitAllPartialSuccess(self):
    snapshots = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i), condition='cond',
            expressions=['expr1', 'expr2'],
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    snapshots[0].isFinalState = True
    ids = [s.id for s in snapshots]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=snapshots)
    wait_mock = self.StartObjectPatch(
        debug.Debuggee, 'WaitForMultipleBreakpoints',
        return_value=[snapshots[0]])
    self.RunDebug(['snapshots', 'wait', '--all', '--location=myfile'])
    wait_mock.assert_called_once_with(ids, wait_all=True, timeout=None)
    self.AssertErrContains('Waiting for 10 snapshots.')
    self.AssertOutputContains(snapshots[0].id)
    for s in snapshots[1:]:
      self.AssertOutputNotContains(s.id)
    self.AssertErrContains('Partial results')
    self.AssertOutputContains(
        'STATUS LOCATION CONDITION COMPLETED_TIME ID VIEW',
        normalize_space=True)

  def testWaitByMultiLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['snapshots', 'wait', '--location=.*:[01]',
                   '--location=.*:[23]'])
    list_mock.assert_called_once_with(
        ['.*:[01]', '.*:[23]'], resource_ids=[], include_all_users=False)

if __name__ == '__main__':
  test_case.main()
