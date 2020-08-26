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

from googlecloudsdk.command_lib.code import json_stream
from googlecloudsdk.command_lib.code import skaffold_events
from tests.lib import test_case
import mock


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
      events = list(skaffold_events.ReadEventStream(mock_response))

    self.assertEqual(events, [{"name": "fake-event"}, {"name": "fake-event2"}])

  def testIgnoreNonDicts(self):
    read_output = []
    read_output.append({
        "result": {
            "event": {
                "name": "fake-event"
            }
        }
    })
    read_output.append(42)
    read_output.append({
        "result": {
            "event": {
                "name": "fake-event2"
            }
        }
    })

    with mock.patch.object(
        json_stream, "ReadJsonStream", return_value=read_output):
      mock_response = mock.Mock()
      events = list(skaffold_events.ReadEventStream(mock_response))

    self.assertEqual(events, [{"name": "fake-event"}, {"name": "fake-event2"}])


class GetServiceLocalPortTest(test_case.TestCase):

  def testGetPorts(self):
    with mock.patch.object(skaffold_events,
                           "ReadEventStream") as mock_read_events:
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
          list(
              skaffold_events.GetServiceLocalPort(mock_response, "my-service")),
          [12345, 34567])

  def testIgnoreOtherServices(self):
    with mock.patch.object(skaffold_events,
                           "ReadEventStream") as mock_read_events:
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
          list(
              skaffold_events.GetServiceLocalPort(mock_response, "my-service")),
          [34567])
