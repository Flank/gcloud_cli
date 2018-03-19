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

"""Tests of the util module."""

import os
import socket

from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock
import portpicker


class UtilTests(sdk_test_base.WithOutputCapture):

  def testEnsureComponentIsInstalled(self):
    ensure_mock = self.StartObjectPatch(util.update_manager.UpdateManager,
                                        'EnsureInstalledAndRestart')
    util.EnsureComponentIsInstalled('foo', 'bar')
    ensure_mock.assert_called_with(
        ['foo'], msg='You need the [foo] component to use the bar.')

  def testGetCloudSDKRoot(self):
    class SDKRootValue(object):

      def __init__(self, sdk_root=None):
        # Accessed as a property.
        self.sdk_root = sdk_root

    # Limit the patch scope to this method, because TearDown() logic from other
    # modules also accesses util.config.Paths().
    with mock.patch.object(util.config, 'Paths') as paths_mock:
      paths_mock.return_value = SDKRootValue()
      with self.assertRaises(util.NoCloudSDKError):
        util.GetCloudSDKRoot()

      paths_mock.return_value = SDKRootValue('valid_root')
      self.assertEqual('valid_root', util.GetCloudSDKRoot())

  def testWriteEnvYaml(self):
    env = {'hello': 'world', 'foo': 'bar'}
    output_dir = self.CreateTempDir()
    util.WriteEnvYaml(env, output_dir)

    env_file_path = os.path.join(output_dir, 'env.yaml')
    yaml_env = yaml.load_path(env_file_path)
    self.assertEqual(env, yaml_env)

  def testReadNonExistentEnvYaml(self):
    output_dir = self.CreateTempDir()
    with self.assertRaises(util.NoEnvYamlError):
      util.ReadEnvYaml(output_dir)

  def testReadEnvYaml(self):
    env = {'hello': 'world', 'foo': 'bar'}
    output_dir = self.CreateTempDir()
    util.WriteEnvYaml(env, output_dir)

    yaml_env = util.ReadEnvYaml(output_dir)
    self.assertEqual(env, yaml_env)

  @test_case.Filters.DoNotRunOnWindows
  def testPrintEnvExportNotWindows(self):
    env = {'hello': 'world', 'foo': 'bar foo'}
    util.PrintEnvExport(env)

    self.AssertOutputContains('export hello=world')
    self.AssertOutputContains('export foo="bar foo"')

  @test_case.Filters.RunOnlyOnWindows
  def testPrintEnvExportWindows(self):
    env = {'hello': 'world', 'foo': 'bar foo'}
    util.PrintEnvExport(env)

    self.AssertOutputContains('set hello=world')
    self.AssertOutputContains('set foo="bar foo"')

  def testGetDataDir(self):
    config_dir = config.Paths().global_config_dir

    data_dir = util.GetDataDir('datastore')
    self.assertEqual(os.path.join(config_dir, 'emulators', 'datastore'),
                     data_dir)
    self.assertTrue(os.path.isdir(data_dir))

    properties.VALUES.emulator.datastore_data_dir.Set('hello')
    self.assertEqual('hello', util.GetDataDir('datastore'))

  @test_case.Filters.skip('fails under IPv6', 'b/33234465')
  def testGetHostPort(self):
    socket_mock = self.StartObjectPatch(socket.socket, 'connect_ex')
    socket_mock.return_value = 1
    properties.VALUES.emulator.datastore_host_port.Set('[::1]:8081')
    properties.VALUES.emulator.pubsub_host_port.Set('[::1]:8085')
    self.assertEqual('[::1]:8081', util.GetHostPort('datastore'))
    self.assertEqual('[::1]:8085', util.GetHostPort('pubsub'))

    properties.VALUES.emulator.datastore_host_port.Set(
        '[2620::1012:a:476:5b8a:e9d8:596f]:8080')
    self.assertEqual('[2620::1012:a:476:5b8a:e9d8:596f]:8080',
                     util.GetHostPort('datastore'))

    port_picker_mock = self.StartObjectPatch(portpicker, 'pick_unused_port')
    port_picker_mock.return_value = 8123
    socket_mock.return_value = 0
    self.assertEqual('[::1]:8123', util.GetHostPort('pubsub'))

  @test_case.Filters.skip('fails under IPv6', 'b/33234465')
  def testGetInvalidHostPort(self):
    properties.VALUES.emulator.pubsub_host_port.Set('invalidhostport8080')
    with self.assertRaises(util.InvalidHostError):
      util.GetHostPort('pubsub')

    properties.VALUES.emulator.datastore_host_port.Set('localhost8085')
    with self.assertRaises(util.InvalidHostError):
      util.GetHostPort('datastore')

  @test_case.Filters.skip('fails under IPv6', 'b/33234465')
  def testEmulatorNoDefaultPort(self):
    port_picker_mock = self.StartObjectPatch(portpicker, 'pick_unused_port')
    port_picker_mock.return_value = 8123
    self.assertEqual('[::1]:8123', util.GetHostPort('unknownemulator'))

if __name__ == '__main__':
  test_case.main()
