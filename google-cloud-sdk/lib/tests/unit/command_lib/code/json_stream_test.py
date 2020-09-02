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
from __future__ import unicode_literals

import subprocess
import time

from googlecloudsdk.command_lib.code import json_stream
from tests.lib import test_case
import six


class ReadJsonStreamTest(test_case.TestCase):

  def testParsesJsonEventLines(self):
    input_stream = six.BytesIO(b'{"a":1}\n{"b":2}\n')
    expected = [{"a": 1}, {"b": 2}]
    self.assertSequenceEqual(
        list(json_stream.ReadJsonStream(input_stream)), expected)

  def testRaiseOnNonJson(self):
    with self.assertRaises(ValueError):
      list(json_stream.ReadJsonStream(six.BytesIO(b"nonjson\n")))

  def testReturnsLinesAsTheyAreAvailable(self):
    proc = subprocess.Popen(
        ["bash", "-c", """echo '{"ev":1}'; sleep 0.1; echo '{"ev":2}' """],
        stdout=subprocess.PIPE)
    try:
      received_event_times = []
      for unused_event in json_stream.ReadJsonStream(proc.stdout):
        received_event_times.append(time.time())
      self.assertGreater(
          received_event_times[1] - received_event_times[0],
          0.08,  # 0.1 expected, but the first echo might arrive a little late.
          msg="events must be received at least 0.1 sec apart")
    finally:
      proc.stdout.close()
      proc.wait()
