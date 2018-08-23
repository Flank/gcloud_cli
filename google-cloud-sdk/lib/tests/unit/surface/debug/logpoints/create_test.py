# -*- coding: utf-8 -*- #
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

"""Tests for the 'debug logpoints create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.debug import debug
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base


class CreateTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testCreate(self):
    logpoint = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
        logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
        logMessageFormat='message',
        location=self.messages.SourceLocation(path='myfile', line=123)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateLogpoint',
                                        return_value=logpoint)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=logpoint)
    self.RunDebug(['logpoints', 'create', 'myfile:123', 'message'])
    create_mock.assert_called_once_with(
        location='myfile:123', log_level='info',
        log_format_string='message', condition=None, user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('logLevel: INFO', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)

  def testCreateMovedLocation(self):
    logpoint = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
        logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
        logMessageFormat='message',
        location=self.messages.SourceLocation(path='myfile', line=123)))
    adjusted_logpoint = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        action=self.messages.Breakpoint.ActionValueValuesEnum.LOG,
        logLevel=self.messages.Breakpoint.LogLevelValueValuesEnum.INFO,
        logMessageFormat='message',
        location=self.messages.SourceLocation(path='myfile', line=124)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateLogpoint',
                                        return_value=logpoint)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=adjusted_logpoint)
    self.RunDebug(['logpoints', 'create', 'myfile:123', 'message'])
    create_mock.assert_called_once_with(
        location='myfile:123', log_level='info',
        log_format_string='message', condition=None, user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputNotContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('location: myfile:124', normalize_space=True)
    self.AssertOutputContains('logLevel: INFO', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)
    self.AssertErrContains('logpoint location to myfile:124',
                           normalize_space=True)

if __name__ == '__main__':
  test_case.main()
