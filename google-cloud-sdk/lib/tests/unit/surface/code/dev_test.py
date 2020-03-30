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

import os
import os.path
import subprocess

from googlecloudsdk.command_lib.code import kubernetes
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms
from surface import code
from surface.code import dev
from tests.lib import test_case
from tests.lib.calliope import util
import mock


class DevTest(test_case.TestCase):

  COMMON_ARGS = ['--service-name=fakeservice', '--image-name=fakeimage']

  def SetUp(self):
    self.StartObjectPatch(dev, 'Skaffold')
    properties.VALUES.core.project.Set('myproject')
    self.addCleanup(properties.VALUES.core.project.Set, None)

    self.parser = util.ArgumentParser()
    code.Code.Args(self.parser)
    dev.Dev.Args(self.parser)

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

  def testSelectKindDefaultOnLinux(self):
    args = self.parser.parse_args(self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes, 'KindClusterContext') as mock_kind:
      with mock.patch.object(platforms.OperatingSystem,
                             'Current') as mock_current:
        mock_current.return_value = platforms.OperatingSystem.LINUX
        cmd.Run(args)

    mock_kind.assert_called()

  def testSelectExternal(self):
    args = self.parser.parse_args(['--kube-context=context'] + self.COMMON_ARGS)
    cmd = dev.Dev(None, None)

    with mock.patch.object(kubernetes,
                           'ExternalClusterContext') as mock_cluster:
      cmd.Run(args)

    mock_cluster.assert_called()


class SkaffoldTest(test_case.TestCase):

  SDK_PATH = os.path.join('sdk', 'path')
  SKAFFOLD_PATH = os.path.join(SDK_PATH, 'bin', 'skaffold')

  def SetUp(self):
    self.StartObjectPatch(config, 'Paths').return_value.sdk_root = self.SDK_PATH
    self.StartObjectPatch(update_manager.UpdateManager,
                          'EnsureInstalledAndRestart').return_value = True

  def testKeyboardInterrupted(self):
    with mock.patch.object(subprocess, 'Popen'):
      with dev.Skaffold('./skaffold.yaml') as proc:
        raise KeyboardInterrupt()

      proc.terminate.assert_called()

  def testCommand(self):
    with mock.patch.object(subprocess, 'Popen') as popen:
      with dev.Skaffold('./skaffold.yaml'):
        pass

      popen.assert_called_with(
          [mock.ANY, 'dev', '-f', './skaffold.yaml', '--port-forward'],
          env=mock.ANY)

  def testCommandWithContext(self):
    with mock.patch.object(subprocess, 'Popen') as popen:
      with dev.Skaffold('./skaffold.yaml', context_name='fake-context'):
        pass

      popen.assert_called_with([
          self.SKAFFOLD_PATH, 'dev', '-f', './skaffold.yaml', '--port-forward',
          '--kube-context', 'fake-context'
      ],
                               env=mock.ANY)

  def testCommandWithNamespace(self):
    with mock.patch.object(subprocess, 'Popen') as popen:
      with dev.Skaffold('./skaffold.yaml', namespace='fake-namespace'):
        pass

      popen.assert_called_with([
          self.SKAFFOLD_PATH, 'dev', '-f', './skaffold.yaml', '--port-forward',
          '--namespace', 'fake-namespace'
      ],
                               env=mock.ANY)

  def testEnvVars(self):
    with mock.patch.object(subprocess, 'Popen') as popen:
      with dev.Skaffold('./skaffold.yaml', env_vars={'A': 'B', 'C': 'D'}):
        pass

      _, _, kwargs = popen.mock_calls[0]
      self.assertEqual(kwargs['env']['A'], 'B')
      self.assertEqual(kwargs['env']['C'], 'D')
