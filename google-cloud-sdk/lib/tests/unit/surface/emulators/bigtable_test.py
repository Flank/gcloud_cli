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
"""Tests for Bigtable emulator commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.command_lib.emulators import bigtable_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case
import mock


def _IsRunningOnWindows():
  """Returns True if the current os is Windows."""
  current_os = platforms.OperatingSystem.Current()
  return current_os is platforms.OperatingSystem.WINDOWS


class BigtableStartTest(cli_test_base.CliTestBase):
  """Tests for commands and side-effects."""

  # A stub value for util.GetEmulatorRoot().
  BIGTABLE_ROOT = os.path.join('BIGTABLE_ROOT', 'platform')

  def SetUp(self):
    """Patches mocks into the modules under test."""
    # We verify these mocks.
    self.exec_mock = mock.MagicMock()
    self.prefix_output_mock = mock.MagicMock()

    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')
    self.StartObjectPatch(util, 'GetHostPort', return_value='localhost:9999')
    self.StartObjectPatch(
        util, 'GetEmulatorRoot', return_value=self.BIGTABLE_ROOT)
    exec_emulator_mock = self.StartObjectPatch(util, 'Exec', self.exec_mock)
    exec_emulator_mock.return_value.__enter__.return_value = 'proc'

    self.StartObjectPatch(util, 'PrefixOutput', self.prefix_output_mock)

  def ExpectedCommand(self, args):
    """The expected command for starting the emulator with args."""
    bigtable_executable = 'cbtemulator'
    if _IsRunningOnWindows():
      bigtable_executable += '.exe'
    return [os.path.join(self.BIGTABLE_ROOT, bigtable_executable)] + args

  def testRun_WithNoArgs(self):
    self.Run('beta emulators bigtable start')
    self.exec_mock.assert_called_with(
        self.ExpectedCommand(['--host=localhost', '--port=9999']))
    self.prefix_output_mock.assert_called_with('proc', bigtable_util.BIGTABLE)

  def testRun_WithHostPort(self):
    self.Run('beta emulators bigtable start --host-port=1.2.3.4:1111')
    self.exec_mock.assert_called_with(
        self.ExpectedCommand(['--host=1.2.3.4', '--port=1111']))


class BigtableEnvInitTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.read_yaml_mock = mock.MagicMock()

    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')
    self.StartObjectPatch(util, 'ReadEnvYaml',
                          self.read_yaml_mock).return_value = {
                              'foo': 'bar',
                              'quotme': 'xyzzy this',
                          }

  def testRun(self):
    result = self.Run('beta emulators bigtable env-init')
    self.assertEqual({'foo': 'bar', 'quotme': 'xyzzy this'}, result)
    self.read_yaml_mock.assert_called_with(bigtable_util.GetDataDir())
    if _IsRunningOnWindows():
      self.AssertOutputEquals("set foo=bar\nset quotme='xyzzy this'\n")
    else:
      self.AssertOutputEquals("export foo=bar\nexport quotme='xyzzy this'\n")


if __name__ == '__main__':
  test_case.main()
