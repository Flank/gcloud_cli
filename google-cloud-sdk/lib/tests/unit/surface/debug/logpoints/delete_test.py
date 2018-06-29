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

"""Tests for the 'debug logpoints delete' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base

import mock
from six.moves import range


class DeleteTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testDeleteOne(self):
    logpoint = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id-0',
        action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
        logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
        logMessageFormat='message',
        location=self.messages.SourceLocation(path='myfile', line=123)))
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[logpoint])
    delete_mock = self.StartObjectPatch(debug.Debuggee, 'DeleteBreakpoint')
    prompt_mock = self.StartObjectPatch(console_io, 'PromptContinue')
    self.RunDebug(['logpoints', 'delete', '--location', 'myfile'])
    delete_mock.assert_called_once_with(logpoint.id)
    list_mock.assert_called_once_with(
        ['myfile'], resource_ids=[], include_inactive=False,
        include_all_users=False,
        restrict_to_type=debug.DebugObject.LOGPOINT_TYPE)
    self.assertEqual(prompt_mock.call_count, 1)
    self.AssertErrContains('Deleted 1 logpoint.')

  def testDelete(self):
    logpoints = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=logpoints)
    delete_mock = self.StartObjectPatch(debug.Debuggee, 'DeleteBreakpoint')
    prompt_mock = self.StartObjectPatch(console_io, 'PromptContinue',
                                        return_value=True)
    self.RunDebug(['logpoints', 'delete', '--location', 'myfile'])
    delete_mock.assert_has_calls([mock.call(l.id) for l in logpoints])
    list_mock.assert_called_once_with(
        ['myfile'], resource_ids=[], include_inactive=False,
        include_all_users=False,
        restrict_to_type=debug.DebugObject.LOGPOINT_TYPE)
    self.assertEqual(prompt_mock.call_count, 1)
    self.AssertErrContains('Deleted 10 logpoints')

  def testDeleteById(self):
    logpoints = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    ids = [l.id for l in logpoints]
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=logpoints)
    delete_mock = self.StartObjectPatch(debug.Debuggee, 'DeleteBreakpoint')
    prompt_mock = self.StartObjectPatch(console_io, 'PromptContinue',
                                        return_value=True)
    self.RunDebug(['logpoints', 'delete'] + ids)
    delete_mock.assert_has_calls([mock.call(i) for i in ids])
    list_mock.assert_called_once_with(
        None, resource_ids=ids, include_inactive=False,
        include_all_users=False,
        restrict_to_type=debug.DebugObject.LOGPOINT_TYPE)
    self.assertEqual(prompt_mock.call_count, 1)
    self.AssertErrContains('Deleted 10 logpoints')

  def testDeleteCancel(self):
    logpoints = [
        self.debuggee.AddTargetInfo(self.messages.Breakpoint(
            id='dummy-id-{0}'.format(i),
            action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
            logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
            logMessageFormat='message',
            location=self.messages.SourceLocation(path='myfile', line=i)))
        for i in range(0, 10)]
    self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=logpoints)
    delete_mock = self.StartObjectPatch(debug.Debuggee, 'DeleteBreakpoint')
    self.StartObjectPatch(console_io, '_RawInput', return_value='n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.RunDebug(['logpoints', 'delete', '--location', 'myfile'])
    self.assertEqual(delete_mock.call_count, 0)

  def testDeleteByMultiLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(['logpoints', 'delete', '--location=.*:[01]',
                   '--location=.*:[23]'])
    list_mock.assert_called_once_with(
        ['.*:[01]', '.*:[23]'], resource_ids=[], include_all_users=False,
        include_inactive=False, restrict_to_type=debug.Debugger.LOGPOINT_TYPE)


if __name__ == '__main__':
  test_case.main()
