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

import os.path
import subprocess

from googlecloudsdk.command_lib.code import kubernetes
from googlecloudsdk.command_lib.code import run_subprocess
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager
from tests.lib import test_case
import mock


class Matcher(object):

  def __init__(self, matcher):
    self._matcher = matcher

  def __eq__(self, other):
    return self._matcher(other)


class SdkPathTestCase(test_case.TestCase):

  SDK_PATH = os.path.join("sdk", "path")

  def SetUp(self):
    self.StartObjectPatch(config, "Paths").return_value.sdk_root = self.SDK_PATH
    self.StartObjectPatch(update_manager.UpdateManager,
                          "EnsureInstalledAndRestart").return_value = True


class StartMinikubeTest(SdkPathTestCase):

  MINIKUBE_TEARDOWN_CALL = mock.call([
      os.path.join("sdk", "path", "bin", "minikube"), "stop", "-p",
      "cluster-name"
  ],
                                     show_output=False,
                                     timeout_sec=150)

  def testAlreadyRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputJson") as mock_get_json:
      mock_get_json.return_value = {"Host": "Running"}
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.Minikube("cluster-name"):
          # Assert "minikube start" is not called.
          mock_run.assert_not_called()

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testNotYetRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputJson") as mock_get_json:
      mock_get_json.return_value = {}
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.Minikube("cluster-name"):
          self.assertIn("cluster-name", mock_run.call_args[0][0])
          self.assertIn("start", mock_run.call_args[0][0])

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testNotYetRunningError(self):
    with mock.patch.object(run_subprocess, "GetOutputJson") as mock_get_json:
      mock_get_json.side_effect = subprocess.CalledProcessError(1, "cmd")
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.Minikube("cluster-name"):
          self.assertIn("cluster-name", mock_run.call_args[0][0])
          self.assertIn("start", mock_run.call_args[0][0])

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testDriver(self):
    with mock.patch.object(run_subprocess, "GetOutputJson") as mock_get_json:
      mock_get_json.return_value = {}
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.Minikube("cluster-name", vm_driver="my-driver"):
          self.assertIn("--vm-driver=my-driver", mock_run.call_args[0][0])

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testDockerDriver(self):
    with mock.patch.object(run_subprocess, "GetOutputJson") as mock_get_json:
      mock_get_json.return_value = {}
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.Minikube("cluster-name", vm_driver="docker"):
          mock_run.assert_called_once_with(
              Matcher(lambda cmd: "--vm-driver=docker" in cmd),
              timeout_sec=150,
              show_output=False)
          mock_run.assert_called_once_with(
              Matcher(lambda cmd: "--container-runtime=docker" in cmd),
              timeout_sec=150,
              show_output=False)

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testDebug(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name", debug=True):
      mock_run.assert_called_once_with(
          Matcher(lambda cmd: "--alsologtostderr" in cmd),
          timeout_sec=150,
          show_output=True)
      mock_run.assert_called_once_with(
          Matcher(lambda cmd: "-v8" in cmd), timeout_sec=150, show_output=True)


class MinikubeClusterTest(SdkPathTestCase):

  def testEnvVars(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = [
          "DOCKER_A=abcd",
          "DOCKER_B=1234",
          "MY_ENV_VAR=My23",
          "ENV_VAR_WITH_EQ=a=3",
      ]

      minikube_cluster = kubernetes.MinikubeCluster(
          "cluster-name", shared_docker=False)

      expected_env_vars = {
          "DOCKER_A": "abcd",
          "DOCKER_B": "1234",
          "MY_ENV_VAR": "My23",
          "ENV_VAR_WITH_EQ": "a=3"
      }
      self.assertEqual(minikube_cluster.env_vars, expected_env_vars)

  def testUsageComment(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = [
          "DOCKER_A=abcd",
          "# A usage comment.",
      ]

      minikube_cluster = kubernetes.MinikubeCluster(
          "cluster-name", shared_docker=False)

      expected_env_vars = {
          "DOCKER_A": "abcd",
      }
      self.assertEqual(minikube_cluster.env_vars, expected_env_vars)


class StartKindTest(SdkPathTestCase):

  PATH_TO_KIND = os.path.join(SdkPathTestCase.SDK_PATH, "bin", "kind")

  KIND_TEARDOWN_CALL = mock.call(
      [PATH_TO_KIND, "delete", "cluster", "--name", "cluster-name"],
      show_output=False,
      timeout_sec=150)

  def testAlreadyRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = ["cluster-name"]
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.KindClusterContext("cluster-name"):
          # Assert "kind create cluster" is not called.
          mock_run.assert_not_called()

    self.assertEqual(mock_get_lines.call_args[0][0],
                     [self.PATH_TO_KIND, "get", "clusters"])
    self.assertEqual(self.KIND_TEARDOWN_CALL, mock_run.call_args)

  def testNotYetRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = []
      with mock.patch.object(run_subprocess, "Run") as mock_run:
        with kubernetes.KindClusterContext("cluster-name"):
          mock_run.assert_called_once_with([
              self.PATH_TO_KIND, "create", "cluster", "--name", "cluster-name"
          ],
                                           timeout_sec=150,
                                           show_output=True)

    self.assertEqual(self.KIND_TEARDOWN_CALL, mock_run.call_args)

  def testDeleteKind(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = ["cluster-name"]
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        kubernetes.DeleteKindClusterIfExists("cluster-name")

    mock_run.assert_called_once_with(
        [self.PATH_TO_KIND, "delete", "cluster", "--name", "cluster-name"],
        timeout_sec=150,
        show_output=False)


class KubeNamespace(SdkPathTestCase):

  PATH_TO_KUBECTL = os.path.join(SdkPathTestCase.SDK_PATH, "bin", "kubectl")

  def testNamespaceAlreadyExists(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = ["namespace/a", "namespace/b"]
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.KubeNamespace("a"):
          mock_run.assert_not_called()

        with kubernetes.KubeNamespace("b"):
          mock_run.assert_not_called()

  def testNamespaceNotExists(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = ["namespace/a"]
      with mock.patch.object(run_subprocess, "Run") as mock_run:

        with kubernetes.KubeNamespace("b"):
          self.assertEqual(mock_run.call_args[0][0],
                           [self.PATH_TO_KUBECTL, "create", "namespace", "b"])

        self.assertEqual(mock_run.call_args_list[1][0][0],
                         [self.PATH_TO_KUBECTL, "delete", "namespace", "b"])

  def testCallWithContext(self):
    with mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:
      mock_get_lines.return_value = ["namespace/a"]
      with mock.patch.object(run_subprocess, "Run") as mock_run, \
       mock.patch.object(run_subprocess, "GetOutputLines") as mock_get_lines:

        with kubernetes.KubeNamespace("b", "my-context"):
          self.assertEqual(mock_get_lines.call_args[0][0], [
              self.PATH_TO_KUBECTL, "--context", "my-context", "get",
              "namespaces", "-o", "name"
          ])
          self.assertEqual(mock_run.call_args_list[0][0][0], [
              self.PATH_TO_KUBECTL, "--context", "my-context", "create",
              "namespace", "b"
          ])

        self.assertEqual(mock_run.call_args_list[1][0][0], [
            self.PATH_TO_KUBECTL, "--context", "my-context", "delete",
            "namespace", "b"
        ])
