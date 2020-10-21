# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import subprocess

from googlecloudsdk.command_lib.code import kubernetes
from googlecloudsdk.command_lib.code import run_subprocess
from googlecloudsdk.command_lib.code import skaffold
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from surface import code
from surface.code import dev
from tests.lib import test_case
from tests.lib.calliope import util
import mock


class DevTest(test_case.TestCase):

  COMMON_ARGS = [
      '--service-name=fakeservice', '--image=fakeimage',
      '--builder=myfakebuilder'
  ]

  def SetUp(self):
    self.StartObjectPatch(skaffold, 'PrintUrlThreadContext')
    self.StartObjectPatch(skaffold, 'Skaffold')
    properties.VALUES.core.project.Set('myproject')
    self.addCleanup(properties.VALUES.core.project.Set, None)

    self.parser = util.ArgumentParser()
    code.Code.Args(self.parser)
    dev.Dev.Args(self.parser)

    self.find_executable_on_path = self.StartObjectPatch(
        file_utils, 'FindExecutableOnPath', return_value=True)
    self.mock_run = self.StartObjectPatch(run_subprocess, 'Run')

  def testSelectMinikube(self):
    args = self.parser.parse_args(['--minikube-profile=fake-profile'] +
                                  self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'Minikube') as mock_minikube:
      cmd.Run(args)

    mock_minikube.assert_called()

  def testSelectMinikubeDefaultOnWindows(self):
    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'Minikube') as mock_minikube:
      with mock.patch.object(platforms.OperatingSystem,
                             'Current') as mock_current:
        mock_current.return_value = platforms.OperatingSystem.WINDOWS
        cmd.Run(args)

    mock_minikube.assert_called()

  def testSelectMinikubeDefaultOnMac(self):
    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'Minikube') as mock_minikube:
      with mock.patch.object(platforms.OperatingSystem,
                             'Current') as mock_current:
        mock_current.return_value = platforms.OperatingSystem.MACOSX
        cmd.Run(args)

    mock_minikube.assert_called()

  def testSelectKind(self):
    args = self.parser.parse_args(['--kind-cluster=fake-cluster'] +
                                  self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'KindClusterContext') as mock_kind:
      cmd.Run(args)

    mock_kind.assert_called()

  def testSelectMinikubeDefaultOnLinux(self):
    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'Minikube') as mock_minikube:
      with mock.patch.object(platforms.OperatingSystem,
                             'Current') as mock_current:
        mock_current.return_value = platforms.OperatingSystem.LINUX
        cmd.Run(args)

    mock_minikube.assert_called()

  def testSelectExternal(self):
    args = self.parser.parse_args(['--kube-context=context'] + self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes,
                           'ExternalClusterContext') as mock_cluster:
      cmd.Run(args)

    mock_cluster.assert_called()

  def testNoDocker(self):
    self.find_executable_on_path.return_value = False

    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with self.assertRaises(dev.RuntimeMissingDependencyError):
      cmd.Run(args)

  def testDockerRunning(self):
    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    self.mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd='')
    with self.assertRaises(dev.RuntimeMissingDependencyError):
      cmd.Run(args)


class EnsureComponentsInstalled(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    dev.Dev.Args(self.parser)

    self.StartObjectPatch(config, 'Paths').return_value.sdk_root = '/'

  def testNoFlags(self):
    args = self.parser.parse_args([])

    with mock.patch.object(update_manager.UpdateManager,
                           'EnsureInstalledAndRestart') as ensure_installed:
      dev._EnsureComponentsInstalled(args)

    ensure_installed.assert_called_with(['skaffold', 'minikube'])

  def testKind(self):
    args = self.parser.parse_args(['--kind-cluster=abc'])

    with mock.patch.object(update_manager.UpdateManager,
                           'EnsureInstalledAndRestart') as ensure_installed:
      dev._EnsureComponentsInstalled(args)

    ensure_installed.assert_called_with(['skaffold', 'kind'])

  def testExternal(self):
    args = self.parser.parse_args(['--kube-context=abc'])

    with mock.patch.object(update_manager.UpdateManager,
                           'EnsureInstalledAndRestart') as ensure_installed:
      dev._EnsureComponentsInstalled(args)

    ensure_installed.assert_called_with(['skaffold'])

  def testMinikube(self):
    args = self.parser.parse_args(['--minikube-profile=abc'])

    with mock.patch.object(update_manager.UpdateManager,
                           'EnsureInstalledAndRestart') as ensure_installed:
      dev._EnsureComponentsInstalled(args)

    ensure_installed.assert_called_with(['skaffold', 'minikube'])


class EnsureComponentsInstalledSkip(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    dev.Dev.Args(self.parser)

    self.StartObjectPatch(config, 'Paths').return_value.sdk_root = None

  def testNoFlags(self):
    args = self.parser.parse_args([])

    with mock.patch.object(update_manager.UpdateManager,
                           'EnsureInstalledAndRestart') as ensure_installed:
      dev._EnsureComponentsInstalled(args)

    ensure_installed.assert_not_called()
