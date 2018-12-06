# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine predict tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.command_lib.ml_engine import predict_utilities
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

JSON_FORMAT = 'json'
TEXT_FORMAT = 'text'


class ReadPredictInstancesTest(base.MlBetaPlatformTestBase):

  def testJsonInstances(self):
    instance_file = io.BytesIO(b'{"images": [0, 1], "key": 3}')
    instances = predict_utilities.ReadInstances(instance_file, JSON_FORMAT)
    expected_instances = [{'images': [0, 1], 'key': 3}]
    self.assertEqual(expected_instances, instances)

  def testJsonInstancesTrailingNewline(self):
    instance_file = io.BytesIO(b'{"images": [0, 1], "key": 3}\n')
    instances = predict_utilities.ReadInstances(instance_file, JSON_FORMAT)
    expected_instances = [{'images': [0, 1], 'key': 3}]
    self.assertEqual(expected_instances, instances)

  def testTextInstances(self):
    instance_file = io.BytesIO(b'abcd')
    instances = predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)
    expected_instances = ['abcd']
    self.assertEqual(expected_instances, instances)

  def testTextInstancesUTF8BOM(self):
    instance_file = io.BytesIO(b'\xef\xbb\xbfabcd')
    instances = predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)
    expected_instances = ['abcd']
    self.assertEqual(expected_instances, instances)

  def testTextInstancesTrailingNewline(self):
    instance_file = io.BytesIO(b'abcd\n')
    instances = predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)
    expected_instances = ['abcd']
    self.assertEqual(expected_instances, instances)

  def testMultipleJsonInstances(self):
    test_instances = (b'{"images": [0, 1], "key": 3}\n'
                      b'{"images": [3, 2], "key": 2}\n'
                      b'{"images": [2, 1], "key": 1}')
    instance_file = io.BytesIO(test_instances)
    instances = predict_utilities.ReadInstances(instance_file, JSON_FORMAT)
    expected_instances = [{
        'images': [0, 1],
        'key': 3
    }, {
        'images': [3, 2],
        'key': 2
    }, {
        'images': [2, 1],
        'key': 1
    }]
    self.assertEqual(expected_instances, instances)

  def testMultipleTextInstances(self):
    instance_file = io.BytesIO(b'2, 3\n4, 5')
    instances = predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)
    expected_instances = ['2, 3', '4, 5']
    self.assertEqual(expected_instances, instances)

  def testEmptyFile(self):
    instance_file = io.BytesIO(b'')
    with self.assertRaisesRegex(core_exceptions.Error,
                                'No valid instance was found.'):
      predict_utilities.ReadInstances(instance_file, JSON_FORMAT)

  def testExactlyEnoughInstances(self):
    test_instances = b'\n'.join([b'{"images": [0, 1], "key": 3}'] * 100)
    instance_file = io.BytesIO(test_instances)
    instances = predict_utilities.ReadInstances(instance_file, JSON_FORMAT,
                                                limit=100)
    self.assertEqual(100, len(instances))

  def testTooManyInstances(self):
    test_instances = b'\n'.join([b'{"images": [0, 1], "key": 3}'] * 101)
    instance_file = io.BytesIO(test_instances)
    with self.assertRaisesRegex(core_exceptions.Error, 'no more than 100'):
      predict_utilities.ReadInstances(instance_file, JSON_FORMAT, limit=100)

  def testTooManyInstancesNoLimit(self):
    test_instances = b'\n'.join([b'{"images": [0, 1], "key": 3}'] * 100)
    instance_file = io.BytesIO(test_instances)
    instance_file = io.BytesIO(test_instances)

    instances = predict_utilities.ReadInstances(
        instance_file, JSON_FORMAT, limit=None)
    self.assertEqual(100, len(instances))

  def testNewlineOnlyJSON(self):
    instance_file = io.BytesIO(b'\n')
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      predict_utilities.ReadInstances(instance_file, JSON_FORMAT)

  def testNewlineOnlyTEXT(self):
    instance_file = io.BytesIO(b'\n')
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)

  def testEmptyLineJson(self):
    test_instances = (b'{"images": [0, 1], "key": 3}\n\n'
                      b'{"images": [0, 1], "key": 3}')
    instance_file = io.BytesIO(test_instances)
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      predict_utilities.ReadInstances(instance_file, JSON_FORMAT)

  def testEmptyLineText(self):
    instance_file = io.BytesIO(b'2, 3\n\n2, 3')
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      predict_utilities.ReadInstances(instance_file, TEXT_FORMAT)


class ReadInstancesFromArgsTest(base.MlBetaPlatformTestBase):

  def testReadInstancesFromArgs_NoInstances(self):
    with self.AssertRaisesExceptionMatches(
        predict_utilities.InvalidInstancesFileError,
        'Exactly one of --json-instances and --text-instances must be '
        'specified.'):
      predict_utilities.ReadInstancesFromArgs(None, None)

  def testReadInstancesFromArgs_BothInstances(self):
    with self.AssertRaisesExceptionMatches(
        predict_utilities.InvalidInstancesFileError,
        'Exactly one of --json-instances and --text-instances must be '
        'specified.'):
      predict_utilities.ReadInstancesFromArgs('foo.json', 'bar.txt')

  def testReadInstancesFromArgs_Json(self):
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=b'{"a": "b"}\n')
    self.assertEqual(
        predict_utilities.ReadInstancesFromArgs(instances_file, None),
        [{'a': 'b'}])

  def testReadInstancesFromArgs_JsonStdin(self):
    self.WriteInput('{"a": "b"}')
    self.assertEqual(
        predict_utilities.ReadInstancesFromArgs('-', None),
        [{'a': 'b'}])

  def testReadInstancesFromArgs_Text(self):
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=b'foo\nbar')
    self.assertEqual(
        predict_utilities.ReadInstancesFromArgs(None, instances_file),
        ['foo', 'bar'])

  def testReadInstancesFromArgs_WithBOM(self):
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=b'\xef\xbb\xbf{"a": "b"}\n')
    self.assertEqual(
        predict_utilities.ReadInstancesFromArgs(instances_file, None),
        [{'a': 'b'}])

  def testReadInstancesFromArgs_TextStdin(self):
    self.WriteInput('foo\nbar')
    self.assertEqual(
        predict_utilities.ReadInstancesFromArgs(None, '-'),
        ['foo', 'bar'])


class ParseModelOrVersionRefTest(base.MlBetaPlatformTestBase):

  def testParseModelOrVersionRef_Version(self):
    self.assertEqual(
        predict_utilities.ParseModelOrVersionRef('m', 'v'),
        resources.REGISTRY.Create('ml.projects.models.versions',
                                  projectsId=self.Project(),
                                  modelsId='m',
                                  versionsId='v'))

  def testParseModelOrVersionRef_Model(self):
    self.assertEqual(
        predict_utilities.ParseModelOrVersionRef('m', None),
        resources.REGISTRY.Create('ml.projects.models',
                                  projectsId=self.Project(),
                                  modelsId='m'))

  def testParseModelOrVersionRef_MissingModel(self):
    with self.assertRaises(resources.RequiredFieldOmittedException):
      predict_utilities.ParseModelOrVersionRef(None, 'v')

  def testParseModelOrVersionRef_MissingModelAndVersion(self):
    with self.assertRaises(resources.RequiredFieldOmittedException):
      predict_utilities.ParseModelOrVersionRef(None, None)


if __name__ == '__main__':
  test_case.main()
