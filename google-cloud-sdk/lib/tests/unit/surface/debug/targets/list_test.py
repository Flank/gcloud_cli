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

"""Tests for the 'debug targets list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.debug import debug
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base


class ListTest(base.DebugSdkTest, sdk_test_base.WithOutputCapture):

  def testListWhenEmpty(self):
    list_mock = self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                                      return_value=[])
    result = self.RunDebug(['targets', 'list'])

    list_mock.assert_called_once_with(include_inactive=False,
                                      include_stale=False)
    self.assertEqual([], list(result))

  def testList(self):
    targets = [
        debug.Debuggee(self.messages.Debuggee(
            id=('debugee' + version),
            project='12345', labels=self.messages.Debuggee.LabelsValue(
                additionalProperties=[
                    self.messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='module', value='test-module'),
                    self.messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='version', value=version)])))
        for version in ['testV1', 'testV2']]
    list_mock = self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                                      return_value=targets)
    result = self.RunDebug(['targets', 'list'])
    list_mock.assert_called_once_with(include_inactive=False,
                                      include_stale=False)
    self.assertEqual(targets, list(result))
    self.AssertOutputContains('test-module-testV1')
    self.AssertOutputContains('test-module-testV2')
    self.AssertOutputContains('NAME ID', normalize_space=True)

  def testListIncludeInactive(self):
    targets = [
        debug.Debuggee(self.messages.Debuggee(
            id=('debugee' + version),
            project='12345', labels=self.messages.Debuggee.LabelsValue(
                additionalProperties=[
                    self.messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='module', value='test-module'),
                    self.messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='version', value=version)])))
        for version in ['testV1', 'testV2']]
    list_mock = self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                                      return_value=targets)
    result = self.RunDebug(['targets', 'list', '--include-inactive'])
    list_mock.assert_called_once_with(include_inactive=True,
                                      include_stale=True)
    self.assertEqual(targets, list(result))
    self.AssertOutputContains('test-module-testV1')
    self.AssertOutputContains('test-module-testV2')
    self.AssertOutputContains('NAME ID', normalize_space=True)


if __name__ == '__main__':
  test_case.main()
