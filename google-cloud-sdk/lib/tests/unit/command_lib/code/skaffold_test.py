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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import os.path
import subprocess

from googlecloudsdk.command_lib.code import json_stream
from googlecloudsdk.command_lib.code import skaffold
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager
from tests.lib import test_case
import mock


class SkaffoldTest(test_case.TestCase):

  SDK_PATH = os.path.join("sdk", "path")
  SKAFFOLD_PATH = os.path.join(SDK_PATH, "bin", "skaffold")

  def SetUp(self):
    self.StartObjectPatch(config, "Paths").return_value.sdk_root = self.SDK_PATH
    self.StartObjectPatch(update_manager.UpdateManager,
                          "EnsureInstalledAndRestart").return_value = True

  def testKeyboardInterrupted(self):
    with mock.patch.object(subprocess, "Popen"):
      with skaffold.Skaffold("./skaffold.yaml") as proc:
        raise KeyboardInterrupt()

      proc.terminate.assert_called()

  def testCommand(self):
    with mock.patch.object(subprocess, "Popen") as popen:
      with skaffold.Skaffold("./skaffold.yaml"):
        pass

      popen.assert_called_with(
          [mock.ANY, "dev", "-f", "./skaffold.yaml", "--port-forward"],
          env=mock.ANY)

  def testCommandWithContext(self):
    with mock.patch.object(subprocess, "Popen") as popen:
      with skaffold.Skaffold("./skaffold.yaml", context_name="fake-context"):
        pass

    _, args, _ = popen.mock_calls[0]
    self.assertIn("--kube-context=fake-context", args[0])

  def testCommandWithNamespace(self):
    with mock.patch.object(subprocess, "Popen") as popen:
      with skaffold.Skaffold("./skaffold.yaml", namespace="fake-namespace"):
        pass

    _, args, _ = popen.mock_calls[0]
    self.assertIn("--namespace=fake-namespace", args[0])

  def testEnvVars(self):
    with mock.patch.object(subprocess, "Popen") as popen:
      with skaffold.Skaffold("./skaffold.yaml", env_vars={"A": "B", "C": "D"}):
        pass

    _, _, kwargs = popen.mock_calls[0]
    self.assertEqual(kwargs["env"]["A"], "B")
    self.assertEqual(kwargs["env"]["C"], "D")

  def testDebug(self):
    with mock.patch.object(subprocess, "Popen") as popen:
      with skaffold.Skaffold("./skaffold.yaml", debug=True):
        pass

    _, args, _ = popen.mock_calls[0]
    self.assertIn("-vdebug", args[0])


class ReadEventStreamTest(test_case.TestCase):

  def testStream(self):
    read_output = [{
        "result": {
            "event": {
                "name": "fake-event"
            }
        }
    }, {
        "result": {
            "event": {
                "name": "fake-event2"
            }
        }
    }]

    with mock.patch.object(
        json_stream, "ReadJsonStream", return_value=read_output):
      mock_response = mock.Mock()
      events = list(skaffold.ReadEventStream(mock_response))

    self.assertEqual(events, [{"name": "fake-event"}, {"name": "fake-event2"}])

  def testIgnoreNonDicts(self):
    read_output = []
    read_output.append({"result": {"event": {"name": "fake-event"}}})
    read_output.append(42)
    read_output.append({"result": {"event": {"name": "fake-event2"}}})

    with mock.patch.object(
        json_stream, "ReadJsonStream", return_value=read_output):
      mock_response = mock.Mock()
      events = list(skaffold.ReadEventStream(mock_response))

    self.assertEqual(events, [{"name": "fake-event"}, {"name": "fake-event2"}])


class GetServiceLocalPortTest(test_case.TestCase):

  def testGetPorts(self):
    with mock.patch.object(skaffold, "ReadEventStream") as mock_read_events:
      mock_read_events.return_value = [{
          "portEvent": {
              "resourceName": "my-service",
              "localPort": 12345
          }
      }, {
          "portEvent": {
              "resourceName": "my-service",
              "localPort": 34567
          }
      }]

      mock_response = mock.Mock()
      self.assertEqual(
          list(skaffold.GetServiceLocalPort(mock_response, "my-service")),
          [12345, 34567])

  def testIgnoreOtherServices(self):
    with mock.patch.object(skaffold, "ReadEventStream") as mock_read_events:
      mock_read_events.return_value = [{
          "portEvent": {
              "resourceName": "my-service2",
              "localPort": 12345
          }
      }, {
          "portEvent": {
              "resourceName": "my-service",
              "localPort": 34567
          }
      }]

      mock_response = mock.Mock()
      self.assertEqual(
          list(skaffold.GetServiceLocalPort(mock_response, "my-service")),
          [34567])
