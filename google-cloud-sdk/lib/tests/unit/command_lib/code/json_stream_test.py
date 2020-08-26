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

import os

from googlecloudsdk.command_lib.code import json_stream
from tests.lib import test_case
import mock


class FakeFile(object):

  @staticmethod
  def fileno():
    return 20


class ReadJsonStreamTest(test_case.TestCase):

  def testStreamJson(self):
    read_outputs = [b'{"a": "b",', b'"c" : 3}\n{', b'"d": 4}', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = [{'a': 'b', 'c': 3}, {'d': 4}]
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile())), expected_objects)

  def testIgnoreNonJson(self):
    read_outputs = [b'\a\n{"a": "b",', b'"c" : 3}', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = [{'a': 'b', 'c': 3},]
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile(), ignore_non_json=True)),
          expected_objects)

  def testRaiseOnNonJson(self):
    read_outputs = [b'\a\n{"a": "b",', b'"c" : 3}', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      with self.assertRaises(ValueError):
        list(json_stream.ReadJsonStream(FakeFile(), ignore_non_json=False))

  def testIgnoreBlankLines(self):
    read_outputs = [b'{"a": "b",', b'"c" : 3}\n\n{', b'"d": 4}', b'\n', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = ({'a': 'b', 'c': 3}, {'d': 4})
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile())), expected_objects)

  def testIgnoreNonObjects(self):
    read_outputs = [b'{"a": "b",', b'"c" : 3}\n{', b'"d": 4}', b'\n52', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = [{'a': 'b', 'c': 3}, {'d': 4}]
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile())), expected_objects)

  def testEmitMultipleLinesPerChunk(self):
    read_outputs = [b'{"a": 1}\n{"a":2}\n', b'']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = [{'a': 1}, {'a': 2}]
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile())), expected_objects)

  def testSplitCodepoint(self):
    # Split a unicode codepoint across two read outputs and make sure they
    # get put back together properly.
    read_outputs = [b'{"a": "\xF0\x9F', b'\x98\x80', b'"}', '']
    with mock.patch.object(os, 'read', side_effect=read_outputs):
      expected_objects = [{'a': b'\xF0\x9F\x98\x80'.decode('utf-8')},]
      self.assertSequenceEqual(
          list(json_stream.ReadJsonStream(FakeFile())), expected_objects)

