# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for surface.emulators.start."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java
from surface.emulators import start
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import util as pubsub_emulator_util
import mock

# A stub value for util.GetPubSubRoot().
PUBSUB_ROOT = 'pubsub_root'
PROXY_PATH = 'proxy_path'


class StartTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.base_cmd = 'alpha emulators start --project=thecloud '
    self.pubsub_exec_mock = mock.MagicMock()
    self.pubsub_prefix_output_mock = mock.MagicMock()
    self.proxy_exec_mock = mock.MagicMock()
    self.proxy_prefix_output_mock = mock.MagicMock()

    class _ContextManager(object):

      def __enter__(self):
        pass

      def __exit__(self, *a):
        pass

    self.StartObjectPatch(java, 'RequireJavaInstalled')
    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')
    # Note that if we want to do testing around default ports etc, can't set
    # this
    self.StartObjectPatch(util.portpicker, 'is_port_free', return_value=True)
    self.StartObjectPatch(start.tempfile, 'mkstemp',
                          return_value=(1, '/tmp/file'))

    self.StartObjectPatch(util, 'GetCloudSDKRoot',
                          return_value='googlecloudsdk_root')

    self.StartObjectPatch(util, 'GetEmulatorRoot',
                          return_value=PUBSUB_ROOT)

    self.StartObjectPatch(
        pubsub_util.util,
        'Exec',
        self.pubsub_exec_mock).return_value = _ContextManager()

    start_emulator_mock = self.StartObjectPatch(
        start.proxy_util, 'StartEmulatorProxy', self.proxy_exec_mock)
    start_emulator_mock.return_value.__enter__.return_value = 'proc'

    self.StartObjectPatch(start.contextlib.ExitStack, 'enter_context',
                          mock.MagicMock())

    self.StartObjectPatch(start.util, 'PrefixOutput',
                          self.proxy_prefix_output_mock)

    self.StartObjectPatch(util, 'GetEmulatorProxyPath',
                          return_value=PROXY_PATH)

  def testEmulatorDoesntExist(self):
    with self.assertRaises(util.EmulatorArgumentsError):
      self.Run(self.base_cmd + '--emulators=supdog')

  def testAllWithOthers(self):
    with self.assertRaises(util.EmulatorArgumentsError):
      self.Run(self.base_cmd + '--emulators=all,pubsub')
    with self.assertRaises(util.EmulatorArgumentsError):
      self.Run(self.base_cmd + '--emulators=pubsub,all')

  def testAllWithRouteToPublic(self):
    with self.assertRaises(util.EmulatorArgumentsError):
      self.Run(self.base_cmd + '--emulators=all --route-to-public=true')

  def _ExpectedPubsubCommand(self, args):
    """The expected command for starting the emulator with args."""
    return pubsub_emulator_util.ExpectedCommand(self.IsOnWindows(), args)

  def testRun(self):
    default = util.AttrDict({'host_port': {'host': 'localhost', 'port': 1111}})
    self.StartObjectPatch(pubsub_util.util, 'AttrDict', return_value=default)

    self.Run(self.base_cmd + '--emulators=pubsub')
    self.proxy_exec_mock.assert_called_with(args=['/tmp/file', '/tmp/file'])
    self.proxy_prefix_output_mock.assert_called_with('proc',
                                                     'emulator-reverse-proxy')

    pubsub_expected = self._ExpectedPubsubCommand(
        ['--host=localhost', '--port=1111'])
    self.pubsub_exec_mock.assert_called_with(pubsub_expected, log_file=1)


if __name__ == '__main__':
  test_case.main()
