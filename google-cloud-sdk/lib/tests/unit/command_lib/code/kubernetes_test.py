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
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.updater import update_manager
from tests.lib import test_case
import mock


class Matcher(object):

  def __init__(self, matcher):
    self._matcher = matcher

  def __eq__(self, other):
    return self._matcher(other)


class FloatMatcher(object):

  def __init__(self, value, delta=0.01):
    self._value = value
    self._delta = delta

  def __eq__(self, other):
    return abs(self._value - other) < self._delta


class SdkPathTestCase(test_case.TestCase):

  SDK_PATH = os.path.join("sdk", "path")

  def SetUp(self):
    self.StartObjectPatch(config, "Paths").return_value.sdk_root = self.SDK_PATH
    self.StartObjectPatch(update_manager.UpdateManager,
                          "EnsureInstalledAndRestart").return_value = True


class StartMinikubeTest(SdkPathTestCase):

  MINIKUBE_PATH = os.path.join("sdk", "path", "bin", "minikube")

  MINIKUBE_TEARDOWN_CALL = mock.call(
      [MINIKUBE_PATH, "stop", "-p", "cluster-name"],
      show_output=False,
      timeout_sec=150)

  def SetUp(self):
    self.StartObjectPatch(run_subprocess, "Run")

  def testAlreadyRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={"Host": "Running"}), \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name"):
      # Assert "minikube start" is not called.
      mock_run.assert_not_called()

    self.assertEqual(self.MINIKUBE_TEARDOWN_CALL, mock_run.call_args)

  def testNotYetRunning(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "StreamOutputJson") as mock_stream, \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name"):
      self.assertIn("cluster-name", mock_stream.call_args[0][0])
      self.assertIn("start", mock_stream.call_args[0][0])

    self.assertEqual(mock_run.call_args, self.MINIKUBE_TEARDOWN_CALL)

  def testNotYetRunningError(self):
    get_json_side_effect = subprocess.CalledProcessError(1, "cmd")
    with mock.patch.object(run_subprocess, "GetOutputJson", side_effect=get_json_side_effect), \
         mock.patch.object(run_subprocess, "StreamOutputJson") as mock_stream, \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name"):
      self.assertIn("cluster-name", mock_stream.call_args[0][0])
      self.assertIn("start", mock_stream.call_args[0][0])
      self.assertEqual(mock_stream.call_args[1]["event_timeout_sec"], 90)

    self.assertEqual(mock_run.call_args, self.MINIKUBE_TEARDOWN_CALL)

  def testDriver(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "StreamOutputJson") as mock_stream, \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name", vm_driver="my-driver"):
      self.assertIn("--vm-driver=my-driver", mock_stream.call_args[0][0])

    self.assertEqual(mock_run.call_args, self.MINIKUBE_TEARDOWN_CALL)

  def testDockerDriver(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "StreamOutputJson") as mock_stream, \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         kubernetes.Minikube("cluster-name", vm_driver="docker"):
      self.assertIn("--vm-driver=docker", mock_stream.call_args[0][0])
      self.assertIn("--container-runtime=docker", mock_stream.call_args[0][0])

    self.assertEqual(mock_run.call_args, self.MINIKUBE_TEARDOWN_CALL)

  def testDebug(self):
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "StreamOutputJson") as mock_stream, \
         mock.patch.object(run_subprocess, "Run"), \
         kubernetes.Minikube("cluster-name", debug=True):
      self.assertIn("--alsologtostderr", mock_stream.call_args[0][0])
      self.assertIn("-v8", mock_stream.call_args[0][0])
      self.assertIs(mock_stream.call_args[1]["show_stderr"], True)

  def testProgressBar(self):
    stream_output = [
        {
            "type": "io.k8s.sigs.minikube.step",
            "data": {
                "currentstep": "1",
                "totalsteps": "3"
            }
        },
        {
            "type": "io.k8s.sigs.minikube.step",
            "data": {
                "currentstep": "2",
                "totalsteps": "3"
            }
        },
        {
            "type": "io.k8s.sigs.minikube.download.progress",
            "data": {
                "progress": "0.33333",
                "currentstep": "2",
                "totalsteps": "3"
            }
        },
        {
            "type": "io.k8s.sigs.minikube.download.progress",
            "data": {
                "progress": "0.77777",
                "currentstep": "2",
                "totalsteps": "3"
            }
        },
        {
            "type": "io.k8s.sigs.minikube.step",
            "data": {
                "currentstep": "3",
                "totalsteps": "3"
            }
        },
    ]
    with mock.patch.object(run_subprocess, "GetOutputJson", return_value={}), \
         mock.patch.object(run_subprocess, "StreamOutputJson", return_value=stream_output), \
         mock.patch.object(run_subprocess, "Run") as mock_run, \
         mock.patch.object(console_io, "ProgressBar") as mock_progress_bar, \
         kubernetes.Minikube("cluster-name"):
      set_progress = (
          mock_progress_bar.return_value.__enter__.return_value.SetProgress)
      expected_calls = [
          mock.call(FloatMatcher(float(1) / 3)),
          mock.call(FloatMatcher(float(2) / 3)),
          mock.call(FloatMatcher(float(2.33333) / 3)),
          mock.call(FloatMatcher(float(2.77777) / 3)),
          mock.call(FloatMatcher(float(3) / 3))
      ]
      set_progress.assert_has_calls(expected_calls)

    self.assertEqual(mock_run.call_args, self.MINIKUBE_TEARDOWN_CALL)

  @test_case.Filters.RunOnlyOnLinux
  def testNotEnoughCpuErrorLinux(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "message": "Ensure your  system has enough CPUs. The minimum "
                       "allowed is 2 CPUs.\n",
            "exitcode": "29"
        }
    }
    expected_error_message = ("Not enough CPUs. Cloud Run Emulator requires "
                              "2 CPUs.")
    with self.assertRaisesRegex(kubernetes.MinikubeStartError,
                                expected_error_message):
      kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  @test_case.Filters.DoNotRunOnLinux
  def testNotEnoughCpuErrorMacOrWindows(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "message": "Ensure your  system has enough CPUs. The minimum "
                       "allowed is 2 CPUs.\n",
            "exitcode": "29"
        }
    }
    expected_error_message = ("Not enough CPUs. Cloud Run Emulator requires "
                              "2 CPUs. Increase Docker VM CPUs to 2.")
    with self.assertRaisesRegex(kubernetes.MinikubeStartError,
                                expected_error_message):
      kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  def testDockerUnreachable(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "exitcode": "69",
            "message": "blah blah blah",
        }
    }
    expected_error_message = "Cannot reach docker daemon."
    with self.assertRaisesRegex(kubernetes.MinikubeStartError,
                                expected_error_message):
      kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  def testOtherError(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "message": "Blah blah blah.\n",
            "exitcode": "64"
        }
    }
    expected_error_message = "Unable to start Cloud Run Emulator."
    with self.assertRaisesRegex(kubernetes.MinikubeStartError,
                                expected_error_message):
      kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  def testNonExitErrors(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "message": "Blah blah blah.\n",
        }
    }
    # No exception means pass.
    kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  def testHostPermissionsError(self):
    event = {
        "type": "io.k8s.sigs.minikube.error",
        "data": {
            "id": "HOST_HOME_PERMISSION",
            "advice": "Do something.",
            "exitcode": "37"
        }
    }

    with self.assertRaisesRegex(kubernetes.MinikubeStartError, "Do something."):
      kubernetes._HandleMinikubeStatusEvent(mock.Mock(), event)

  def testStepNoSteps(self):
    event = {
        "type": "io.k8s.sigs.minikube.step",
        "data": {
        }
    }

    progress_bar = mock.MagicMock()
    set_progress = progress_bar.SetProgress
    kubernetes._HandleMinikubeStatusEvent(progress_bar, event)
    set_progress.assert_not_called()

  def testDownloadNoSteps(self):
    event = {
        "type": "io.k8s.sigs.minikube.download.progress",
        "data": {
        }
    }

    progress_bar = mock.MagicMock()
    kubernetes._HandleMinikubeStatusEvent(progress_bar, event)
    progress_bar.SetProgress.assert_not_called()


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
