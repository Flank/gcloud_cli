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
"""Tests of the datastore_util module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import os
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock


class DatastoreUtilTests(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

  def Project(self):
    return 'fake-project'

  def testGetLegacyGCDRoot(self):
    self._DoTestGetGCDRoot('gcd', True)

  def testGetGCDRoot(self):
    self._DoTestGetGCDRoot('cloud-datastore-emulator', False)

  def _DoTestGetGCDRoot(self, gcd_dir, legacy):
    cloud_sdk_mock = self.StartObjectPatch(util, 'GetCloudSDKRoot')
    cloud_sdk_mock.return_value = 'pathtocloudsdk'

    os_isdir_mock = self.StartObjectPatch(os.path, 'isdir')
    os_isdir_mock.return_value = True
    args = type(str('args_mock'),
                (object,),
                dict(legacy=legacy))

    expected = os.path.join(cloud_sdk_mock.return_value, 'platform', gcd_dir)
    self.assertEqual(expected, datastore_util.GetGCDRoot(args))

    os_isdir_mock.return_value = False
    with self.assertRaises(datastore_util.NoGCDError):
      datastore_util.GetGCDRoot(args)

  @test_case.Filters.DoNotRunOnWindows
  def testArgsForLegacyGCDEmulatorOnNonWindows(self):
    self._DoTestArgsForGCDEmulatorOnNonWindows('gcd.sh', True)

  @test_case.Filters.DoNotRunOnWindows
  def testArgsForGCDEmulatorOnNonWindows(self):
    self._DoTestArgsForGCDEmulatorOnNonWindows('cloud_datastore_emulator',
                                               False)

  def _DoTestArgsForGCDEmulatorOnNonWindows(self, gcd_exec, legacy):
    gcd_root_mock = self.StartObjectPatch(datastore_util, 'GetGCDRoot')
    gcd_root_mock.return_value = 'pathtogcdroot'
    args = type(str('args_mock'),
                (object,),
                dict(legacy=legacy))

    gcd_executable = os.path.join(gcd_root_mock.return_value, gcd_exec)
    self.assertEqual(execution_utils.ArgsForExecutableTool(gcd_executable,
                                                           'args'),
                     datastore_util.ArgsForGCDEmulator(['args'], args))

  @test_case.Filters.RunOnlyOnWindows
  def testArgsForLegacyGCDEmulatorWindows(self):
    self._DoTestArgsForGCDEmulatorWindows('gcd.cmd', True)

  @test_case.Filters.RunOnlyOnWindows
  def testArgsForGCDEmulatorWindows(self):
    self._DoTestArgsForGCDEmulatorWindows('cloud_datastore_emulator.cmd',
                                          False)

  def _DoTestArgsForGCDEmulatorWindows(self, gcd_exec, legacy):
    gcd_root_mock = self.StartObjectPatch(datastore_util, 'GetGCDRoot')
    gcd_root_mock.return_value = 'pathtogcdroot'

    args = type(str('args_mock'),
                (object,),
                dict(legacy=legacy))

    gcd_executable = os.path.join(gcd_root_mock.return_value, gcd_exec)
    self.assertEqual(execution_utils.ArgsForCMDTool(gcd_executable, 'args'),
                     datastore_util.ArgsForGCDEmulator(['args'], args))

  def testPrepareLegacyGCDDataDir(self):
    self._DoTestPrepareGCDDataDir(True)

  def testPrepareGCDDataDir(self):
    self._DoTestPrepareGCDDataDir(False)

  def _DoTestPrepareGCDDataDir(self, legacy):
    gcd_root_mock = self.StartObjectPatch(datastore_util, 'GetGCDRoot')
    gcd_root_mock.return_value = 'pathtogcdroot'
    exec_mock = self.StartObjectPatch(util, 'Exec')
    process = mock.Mock()
    process.poll.return_value = 0
    exec_mock.return_value.__enter__.return_value = process
    prefix_mock = self.StartObjectPatch(util, 'PrefixOutput')

    data_dir = self.CreateTempDir()
    args = type(str('args_mock'),
                (object,),
                dict(legacy=legacy,
                     data_dir=data_dir))

    # Nothing should be done if data-dir is non-empty
    tmp_file = self.Touch(directory=data_dir)
    datastore_util.PrepareGCDDataDir(args)
    self.assertFalse(exec_mock.called)

    # gcd create should be called if data-dir is empty
    exec_mock.reset_mock()
    prefix_mock.reset_mock()
    os.remove(tmp_file)
    datastore_util.PrepareGCDDataDir(args)
    create_args = ['create',
                   '--project_id={0}'.format(self.Project()),
                   data_dir,]
    exec_args = datastore_util.ArgsForGCDEmulator(create_args, args)
    exec_mock.assert_called_once_with(exec_args)
    prefix_mock.assert_called_once_with(process, 'datastore')

    # gcd create should be called if data-dir does not exist
    exec_mock.reset_mock()
    prefix_mock.reset_mock()
    os.rmdir(data_dir)
    datastore_util.PrepareGCDDataDir(args)
    exec_mock.assert_called_once_with(exec_args)
    prefix_mock.assert_called_once_with(process, 'datastore')

    # Should throw exception if PrepareGCDDataDir fails
    process.poll.return_value = 1
    with self.assertRaises(datastore_util.UnableToPrepareDataDir):
      datastore_util.PrepareGCDDataDir(args)

  def testStartLegacyGCDEmulator(self):
    self._DoTestStartGCDEmulator(True)

  def testStartGCDEmulator(self):
    self._DoTestStartGCDEmulator(False)

  def _DoTestStartGCDEmulator(self, legacy):
    gcd_root_mock = self.StartObjectPatch(datastore_util, 'GetGCDRoot')
    gcd_root_mock.return_value = 'pathtogcdroot'
    exec_mock = self.StartObjectPatch(util, 'Exec')

    args = type(str('args_mock'),
                (object,),
                dict(host_port=arg_parsers.HostPort('localhost', '8080'),
                     store_on_disk=True,
                     data_dir='temp_dir',
                     consistency=0.7,
                     legacy=legacy))
    datastore_util.StartGCDEmulator(args)
    start_args = ['start',
                  '--host=localhost',
                  '--port=8080',
                  '--store_on_disk=True',
                  '--consistency=0.7',
                  '--allow_remote_shutdown',
                  'temp_dir',]
    exec_args = datastore_util.ArgsForGCDEmulator(start_args, args)
    exec_mock.assert_called_once_with(exec_args, log_file=None)

  def testWriteLegacyGCDEnvYaml(self):
    self._DoTestWriteGCDEnvYaml(True)

  def testWriteGCDEnvYaml(self):
    self._DoTestWriteGCDEnvYaml(False)

  def _DoTestWriteGCDEnvYaml(self, legacy):
    env_mock = self.StartObjectPatch(util, 'WriteEnvYaml')

    args = type(str('args_mock'),
                (object,),
                dict(host_port=arg_parsers.HostPort('localhost', '8080'),
                     store_on_disk=True,
                     data_dir='temp_dir',
                     legacy=legacy))
    datastore_util.WriteGCDEnvYaml(args)
    env = {'DATASTORE_HOST': 'http://localhost:8080',
           'DATASTORE_EMULATOR_HOST': 'localhost:8080',
           'DATASTORE_EMULATOR_HOST_PATH': 'localhost:8080/datastore',
           'DATASTORE_DATASET': self.Project(),
           'DATASTORE_PROJECT_ID': self.Project(),}
    env_mock.assert_called_once_with(env, 'temp_dir')

  def testWriteIPV6EnvYaml(self):
    env_mock = self.StartObjectPatch(util, 'WriteEnvYaml')

    args = type(str('args_mock'),
                (object,),
                dict(host_port=arg_parsers.HostPort('::', '8080'),
                     store_on_disk=True,
                     data_dir='temp_dir'))
    datastore_util.WriteGCDEnvYaml(args)
    env = {'DATASTORE_HOST': 'http://:::8080',
           'DATASTORE_EMULATOR_HOST': ':::8080',
           'DATASTORE_EMULATOR_HOST_PATH': ':::8080/datastore',
           'DATASTORE_DATASET': self.Project(),
           'DATASTORE_PROJECT_ID': self.Project(),}
    env_mock.assert_called_once_with(env, 'temp_dir')


if __name__ == '__main__':
  test_case.main()
