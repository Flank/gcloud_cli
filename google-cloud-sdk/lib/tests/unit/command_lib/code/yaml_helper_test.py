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

import doctest
import unittest

from googlecloudsdk.command_lib.code import yaml_helper
from tests.lib import test_case
import six


class GetOrCreateTest(test_case.TestCase):

  def testGetExistingDict(self):
    obj = {'A': {'B': {'C': {'D': [1, 2, 3]}}}}

    self.assertIs(
        yaml_helper.GetOrCreate(obj, ('A', 'B', 'C')), obj['A']['B']['C'])

  def testCreateDict(self):
    obj = {'A': {'B': {}}}
    self.assertEqual(yaml_helper.GetOrCreate(obj, ('A', 'B', 'C', 'D')), {})
    self.assertEqual(obj, {'A': {'B': {'C': {'D': {}}}}})

  def testCreateList(self):
    obj = {'A': {'B': {}}}
    self.assertEqual(
        yaml_helper.GetOrCreate(obj, ('A', 'B', 'C', 'D'), constructor=list),
        [])
    self.assertEqual(obj, {'A': {'B': {'C': {'D': []}}}})


class GetAllTest(test_case.TestCase):

  def testIntermediateList(self):
    obj = {'A': {'B': {'C': [{'D': 1}, {'D': 2}, {'D': 3}]}}}
    six.assertCountEqual(self, yaml_helper.GetAll(obj, ('A', 'B', 'C', 'D')),
                         (1, 2, 3))

  def testFinalList(self):
    obj = {'A': {'B': {'C': [1, 2, 3]}}}
    six.assertCountEqual(self, yaml_helper.GetAll(obj, ('A', 'B', 'C')),
                         (1, 2, 3))

  def testNotAListOrObj(self):
    obj = {'A': {'B': 3}}
    with self.assertRaises(ValueError):
      list(yaml_helper.GetAll(obj, ('A', 'B', 'C')))


class DocTest(unittest.TestCase):

  def testDocTest(self):
    failures, _ = doctest.testmod(yaml_helper)
    self.assertEqual(failures, 0, '%s doctests failed' % failures)
