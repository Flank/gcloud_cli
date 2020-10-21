# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for Spanner emulator commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.emulators import spanner_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case
import mock


def _IsRunningOnWindows():
  """Returns True if the current os is Linux."""
  current_os = platforms.OperatingSystem.Current()
  return current_os is platforms.OperatingSystem.WINDOWS


def _IsRunningOnLinux():
  """Returns True if the current os is Linux."""
  current_os = platforms.OperatingSystem.Current()
  return current_os is platforms.OperatingSystem.LINUX


class SpannerStartTestBeta(cli_test_base.CliTestBase):
  """Tests for commands and side-effects."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    """Patches mocks into the modules under test."""
    # We verify these mocks.
    self.exec_mock = mock.MagicMock()
    self.prefix_output_mock = mock.MagicMock()

    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')
    cloud_sdk_mock = self.StartObjectPatch(util, 'GetCloudSDKRoot')
    cloud_sdk_mock.return_value = 'pathtocloudsdk'

    exec_emulator_mock = self.StartObjectPatch(util, 'Exec', self.exec_mock)
    exec_emulator_mock.return_value.__enter__.return_value = 'proc'

    self.StartObjectPatch(util, 'PrefixOutput', self.prefix_output_mock)

  def _ExpectedDockerCommand(self, host, grpc_port, rest_port,
                             enable_fault_injection):
    if enable_fault_injection:
      return [
          'docker', 'run', '-p', '{}:{}:9010'.format(host, grpc_port), '-p',
          '{}:{}:9020'.format(host, rest_port),
          spanner_util.SPANNER_EMULATOR_DOCKER_IMAGE, './gateway_main',
          '--hostname', '0.0.0.0', '--enable_fault_injection'
      ]
    else:
      return [
          'docker', 'run', '-p', '{}:{}:9010'.format(host, grpc_port), '-p',
          '{}:{}:9020'.format(host, rest_port),
          spanner_util.SPANNER_EMULATOR_DOCKER_IMAGE
      ]

  def _ExpectedNativeCommand(self, host, grpc_port, rest_port,
                             enable_fault_injection):
    return [
        os.path.join('pathtocloudsdk', 'bin', 'cloud_spanner_emulator',
                     'gateway_main'),
        '--hostname',
        host,
        '--grpc_port',
        grpc_port,
        '--http_port',
        rest_port,
        ('--enable_fault_injection' if enable_fault_injection else ''),
    ]

  def testRun_WithNoArgs(self):
    self.Run('emulators spanner start')
    if _IsRunningOnLinux():
      self.exec_mock.assert_called_with(
          self._ExpectedNativeCommand('localhost', '9010', '9020', False))
    else:
      self.exec_mock.assert_called_with(
          self._ExpectedDockerCommand('127.0.0.1', '9010', '9020', False))
    self.prefix_output_mock.assert_called_with(
        'proc', spanner_util.SPANNER_EMULATOR_COMPONENT_ID)

  def testRun_WithHostPort(self):
    self.Run(
        'emulators spanner start --host-port=1.2.3.4:1111 --rest-port 1234')
    if _IsRunningOnLinux():
      self.exec_mock.assert_called_with(
          self._ExpectedNativeCommand('1.2.3.4', '1111', '1234', False))
    else:
      self.exec_mock.assert_called_with(
          self._ExpectedDockerCommand('1.2.3.4', '1111', '1234', False))

  def testRun_WithUseDocker(self):
    self.Run('emulators spanner start --use-docker=true')
    self.exec_mock.assert_called_with(
        self._ExpectedDockerCommand('127.0.0.1', '9010', '9020', False))

  def testRun_WithEnableFaultInjection(self):
    self.Run('emulators spanner start --enable-fault-injection=true')
    if _IsRunningOnLinux():
      self.exec_mock.assert_called_with(
          self._ExpectedNativeCommand('localhost', '9010', '9020', True))
    else:
      self.exec_mock.assert_called_with(
          self._ExpectedDockerCommand('127.0.0.1', '9010', '9020', True))


class SpannerStartTestAlpha(SpannerStartTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class SpannerEnvInitTestBeta(cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.read_yaml_mock = mock.MagicMock()

    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')
    self.StartObjectPatch(util, 'ReadEnvYaml',
                          self.read_yaml_mock).return_value = {
                              'foo': 'bar',
                              'quotme': 'xyzzy this',
                          }

  def testRun(self):
    result = self.Run('emulators spanner env-init')
    self.assertEqual({'foo': 'bar', 'quotme': 'xyzzy this'}, result)
    self.read_yaml_mock.assert_called_with(spanner_util.GetDataDir())
    if _IsRunningOnWindows():
      self.AssertOutputEquals("set foo=bar\nset quotme='xyzzy this'\n")
    else:
      self.AssertOutputEquals("export foo=bar\nexport quotme='xyzzy this'\n")


class SpannerEnvInitTestAlpha(SpannerEnvInitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
