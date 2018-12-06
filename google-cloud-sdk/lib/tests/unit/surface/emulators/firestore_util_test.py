# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests of the firestore_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.emulators import firestore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class FirestoreUtilTests(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

  def Project(self):
    return 'fake-project'

  def testGetFirestoreEmulatorRoot(self):
    self._DoTestGetFirestoreEmulatorRoot('cloud-firestore-emulator')

  def _DoTestGetFirestoreEmulatorRoot(self, firestore_dir):
    cloud_sdk_mock = self.StartObjectPatch(util, 'GetCloudSDKRoot')
    cloud_sdk_mock.return_value = 'pathtocloudsdk'

    os_isdir_mock = self.StartObjectPatch(os.path, 'isdir')
    os_isdir_mock.return_value = True

    expected = os.path.join(cloud_sdk_mock.return_value, 'platform',
                            firestore_dir)
    self.assertEqual(expected, firestore_util.GetFirestoreEmulatorRoot())

    os_isdir_mock.return_value = False
    with self.assertRaises(firestore_util.NoFirestoreEmulatorError):
      firestore_util.GetFirestoreEmulatorRoot()

  @test_case.Filters.DoNotRunOnWindows
  def testArgsForFirestoreEmulatorOnNonWindows(self):
    self._DoTestArgsForFirestoreEmulatorOnNonWindows('cloud_firestore_emulator')

  def _DoTestArgsForFirestoreEmulatorOnNonWindows(self, firestore_exec):
    firestore_root_mock = self.StartObjectPatch(firestore_util,
                                                'GetFirestoreEmulatorRoot')
    firestore_root_mock.return_value = 'pathtofirestoreroot'

    firestore_executable = os.path.join(firestore_root_mock.return_value,
                                        firestore_exec)
    self.assertEqual(
        execution_utils.ArgsForExecutableTool(firestore_executable, 'args'),
        firestore_util.ArgsForFirestoreEmulator(['args']))

  @test_case.Filters.RunOnlyOnWindows
  def testArgsForFirestoreEmulatorWindows(self):
    self._DoTestArgsForFirestoreEmulatorWindows('cloud_firestore_emulator.cmd')

  def _DoTestArgsForFirestoreEmulatorWindows(self, firestore_exec):
    firestore_root_mock = self.StartObjectPatch(firestore_util,
                                                'GetFirestoreEmulatorRoot')
    firestore_root_mock.return_value = 'pathtofirestoreroot'

    firestore_executable = os.path.join(firestore_root_mock.return_value,
                                        firestore_exec)
    self.assertEqual(
        execution_utils.ArgsForCMDTool(firestore_executable, 'args'),
        firestore_util.ArgsForFirestoreEmulator(['args']))

  def testStartFirestoreEmulator(self):
    self._DoTestStartFirestoreEmulator()

  def _DoTestStartFirestoreEmulator(self):
    firestore_root_mock = self.StartObjectPatch(firestore_util,
                                                'GetFirestoreEmulatorRoot')
    firestore_root_mock.return_value = 'pathtofirestoreroot'
    exec_mock = self.StartObjectPatch(util, 'Exec')

    args = type(
        str('args_mock'), (object,), {
            'host_port': arg_parsers.HostPort('localhost', '8080'),
            'rules': '/path/to/firestore.rules'
        })
    firestore_util.StartFirestoreEmulator(args)
    start_args = [
        'start', '--host=localhost', '--port=8080',
        '--rules=/path/to/firestore.rules'
    ]
    exec_args = firestore_util.ArgsForFirestoreEmulator(start_args)
    exec_mock.assert_called_once_with(exec_args, log_file=None)


if __name__ == '__main__':
  test_case.main()
