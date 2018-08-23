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

"""Tests for the 'debug snapshots describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.debug import debug
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base

YAML_TEMPLATE = """
condition: cond
consoleViewUrl: https://console.cloud.google.com/debug/fromgcloud?project=12345&dbgee=test-default-debuggee&bp={id}
expressions:
  - expr1
  - expr2
id: {id}
isFinalState: false
location: {path}:{line}
"""


class DescribeTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testDescribeByLocation(self):
    id_format = 'dummy-id-{0}'
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id=id_format.format(1), condition='cond',
        expressions=['expr1', 'expr2'],
        location=self.messages.SourceLocation(path='myfile', line=1)))
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[snapshot])
    self.RunDebug(['snapshots', 'describe', '--location=myfile'])
    list_mock.assert_called_with(
        ['myfile'],
        resource_ids=[],
        include_all_users=True,
        restrict_to_type=debug.Debugger.SNAPSHOT_TYPE,
        full_details=True)
    self.AssertOutputContains(YAML_TEMPLATE.format(
        id=id_format.format(1), path='myfile', line=1), normalize_space=True)

  def testDescribeById(self):
    id_format = 'dummy-id-{0}'
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id=id_format.format(1), condition='cond',
        expressions=['expr1', 'expr2'],
        location=self.messages.SourceLocation(path='myfile', line=1)))
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[snapshot])
    self.RunDebug(['snapshots', 'describe', snapshot.id])
    list_mock.assert_called_with(
        None,
        resource_ids=[snapshot.id],
        include_all_users=True,
        restrict_to_type=debug.Debugger.SNAPSHOT_TYPE,
        full_details=True)
    self.AssertOutputContains(YAML_TEMPLATE.format(
        id=id_format.format(1), path='myfile', line=1), normalize_space=True)

  def testDescribeCustomFormat(self):
    id_format = 'dummy-id-{0}'
    snapshot = self.debuggee.AddTargetInfo(self.messages.Breakpoint(
        id=id_format.format(1), isFinalState=True, status=None))
    list_mock = self.StartObjectPatch(
        debug.Debuggee, 'ListBreakpoints', return_value=[snapshot])
    self.RunDebug(['snapshots', 'describe', '--format=value(short_status())',
                   snapshot.id])
    list_mock.assert_called_with(
        None,
        resource_ids=[snapshot.id],
        include_all_users=True,
        restrict_to_type=debug.Debugger.SNAPSHOT_TYPE,
        full_details=True)
    self.AssertOutputContains('COMPLETED')

  def testDescribeByMultiLocation(self):
    list_mock = self.StartObjectPatch(debug.Debuggee, 'ListBreakpoints',
                                      return_value=[])
    self.RunDebug(
        ['snapshots', 'describe', '--location=.*:[01]', '--location=.*:[23]'])
    list_mock.assert_called_once_with(
        ['.*:[01]', '.*:[23]'],
        resource_ids=[],
        include_all_users=True,
        restrict_to_type=debug.Debugger.SNAPSHOT_TYPE,
        full_details=True)


if __name__ == '__main__':
  test_case.main()
