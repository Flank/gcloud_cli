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

"""Tests for the 'debug snapshots create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.debug import debug
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base


class CreateTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testCreate(self):
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        location=self.messages.SourceLocation(path='myfile', line=123)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateSnapshot',
                                        return_value=snapshot)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=snapshot)
    self.RunDebug([
        'snapshots', 'create', 'myfile:123'])
    create_mock.assert_called_once_with(
        location='myfile:123', expressions=None,
        condition=None, user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)
    self.AssertOutputContains(
        'consoleViewUrl: '
        'https://console.cloud.google.com/debug/fromgcloud?'
        'project={project}'
        '&dbgee={debuggee}'
        '&bp=dummy-id'.format(
            debuggee=self.debuggee.target_id,
            project=self.project_number))

  def testCreateWithExpressions(self):
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id', condition='cond', expressions=['expr1', 'expr2'],
        location=self.messages.SourceLocation(path='myfile', line=123)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateSnapshot',
                                        return_value=snapshot)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=snapshot)
    self.RunDebug([
        'snapshots', 'create', 'myfile:123', '--expression', 'expr1',
        '--condition=cond', '--expression=expr2'])
    create_mock.assert_called_once_with(
        location='myfile:123', expressions=['expr1', 'expr2'],
        condition='cond', user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)
    self.AssertOutputContains(
        'consoleViewUrl: '
        'https://console.cloud.google.com/debug/fromgcloud?'
        'project={project}'
        '&dbgee={debuggee}'
        '&bp=dummy-id'.format(
            debuggee=self.debuggee.target_id,
            project=self.project_number))

  def testCreateOneExpression(self):
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id', expressions=['expr1'],
        location=self.messages.SourceLocation(path='myfile', line=123)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateSnapshot',
                                        return_value=snapshot)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=snapshot)
    self.RunDebug([
        'snapshots', 'create', 'myfile:123', '--expression', 'expr1'])
    create_mock.assert_called_once_with(
        location='myfile:123', expressions=['expr1'], condition=None,
        user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)
    self.AssertOutputContains(
        'consoleViewUrl: '
        'https://console.cloud.google.com/debug/fromgcloud?'
        'project={project}'
        '&dbgee={debuggee}'
        '&bp=dummy-id'.format(
            debuggee=self.debuggee.target_id,
            project=self.project_number))

  def testCreateMovedLocation(self):
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        location=self.messages.SourceLocation(path='myfile', line=123)))
    final_snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id='dummy-id',
        location=self.messages.SourceLocation(path='myfile', line=124)))
    create_mock = self.StartObjectPatch(debug.Debuggee, 'CreateSnapshot',
                                        return_value=snapshot)
    self.StartObjectPatch(debug.Debuggee, 'WaitForBreakpointSet',
                          return_value=final_snapshot)
    self.RunDebug(['snapshots', 'create', 'myfile:123'])
    create_mock.assert_called_once_with(
        location='myfile:123', condition=None, expressions=None,
        user_email='fake_account')
    self.AssertOutputContains('id: dummy-id', normalize_space=True)
    self.AssertOutputNotContains('location: myfile:123', normalize_space=True)
    self.AssertOutputContains('location: myfile:124', normalize_space=True)
    self.AssertOutputContains('status: ACTIVE', normalize_space=True)
    self.AssertErrContains('snapshot location to myfile:124',
                           normalize_space=True)

if __name__ == '__main__':
  test_case.main()
