# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for Pub/Sub emulator commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java
from surface.emulators import pubsub
from surface.emulators.pubsub import start
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import util as pubsub_emulator_util
import mock


class PubSubStartTest(cli_test_base.CliTestBase):
  """Tests for generated commands and side-effects."""

  def SetUp(self):
    """Patches mocks into the modules under test."""
    # We verify these mocks.
    self.exec_mock = mock.MagicMock()
    self.write_yaml_mock = mock.MagicMock()
    self.prefix_output_mock = mock.MagicMock()

    self.StartObjectPatch(java, 'RequireJavaInstalled')
    self.StartObjectPatch(pubsub.util, 'EnsureComponentIsInstalled')
    self.StartObjectPatch(start.util,
                          'GetHostPort',
                          return_value='localhost:9999')
    self.StartObjectPatch(util,
                          'GetEmulatorRoot',
                          return_value=pubsub_emulator_util.PUBSUB_ROOT)

    exec_emulator_mock = self.StartObjectPatch(
        pubsub_util.util, 'Exec', self.exec_mock)
    exec_emulator_mock.return_value.__enter__.return_value = 'proc'

    self.StartObjectPatch(pubsub_util.util, 'WriteEnvYaml',
                          self.write_yaml_mock)
    self.StartObjectPatch(pubsub_util.util, 'PrefixOutput',
                          self.prefix_output_mock)

  def ExpectedCommand(self, args):
    """The expected command for starting the emulator with args."""
    return pubsub_emulator_util.ExpectedCommand(self.IsOnWindows(), args)

  def testRun_WithNoArgs(self):
    self.Run('beta emulators pubsub start')
    self.exec_mock.assert_called_with(self.ExpectedCommand(
        ['--host=localhost', '--port=9999']), log_file=None)
    self.write_yaml_mock.assert_called_with(
        {'PUBSUB_EMULATOR_HOST': 'localhost:9999'}, pubsub_util.GetDataDir())
    self.prefix_output_mock.assert_called_with('proc', pubsub_util.PUBSUB)

  def testRun_WithHostPort(self):
    self.Run('beta emulators pubsub start --host-port=1.2.3.4:1111')
    self.exec_mock.assert_called_with(self.ExpectedCommand(
        ['--host=1.2.3.4', '--port=1111']), log_file=None)
    self.write_yaml_mock.assert_called_with(
        {'PUBSUB_EMULATOR_HOST': '1.2.3.4:1111'}, pubsub_util.GetDataDir())
    self.prefix_output_mock.assert_called_with('proc', pubsub_util.PUBSUB)

  def testRun_WithDataDir(self):
    self.Run('beta emulators pubsub start --data-dir=foo')
    self.exec_mock.assert_called_with(self.ExpectedCommand(
        ['--host=localhost', '--port=9999']), log_file=None)
    self.write_yaml_mock.assert_called_with(
        {'PUBSUB_EMULATOR_HOST': 'localhost:9999'}, 'foo')
    self.prefix_output_mock.assert_called_with('proc', pubsub_util.PUBSUB)


class PubSubEnvInitTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.read_yaml_mock = mock.MagicMock()

    self.StartObjectPatch(java, 'RequireJavaInstalled')
    self.StartObjectPatch(pubsub.util, 'EnsureComponentIsInstalled')
    self.StartObjectPatch(pubsub_util.util, 'ReadEnvYaml',
                          self.read_yaml_mock).return_value = {'foo': 'bar'}

  def testRun_WithNoArgs(self):
    result = self.Run('beta emulators pubsub env-init')
    self.assertEqual({'foo': 'bar'}, result)
    self.read_yaml_mock.assert_called_with(pubsub_util.GetDataDir())
    self.AssertOutputContains('foo=bar')

  def testRun_WithDataDir(self):
    result = self.Run('beta emulators pubsub env-init --data-dir=baz')
    self.assertEqual({'foo': 'bar'}, result)
    self.read_yaml_mock.assert_called_with('baz')
    self.AssertOutputContains('foo=bar')


if __name__ == '__main__':
  test_case.main()
