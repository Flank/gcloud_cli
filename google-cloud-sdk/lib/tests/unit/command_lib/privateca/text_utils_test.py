# Lint as: python3
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.text_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.privateca import text_utils
from tests.lib import cli_test_base
from tests.lib import test_case


class TextUtilsTest(cli_test_base.CliTestBase, test_case.TestCase):

  def testSnakeCaseToCamelCaseSingleWord(self):
    self.assertEqual(text_utils.SnakeCaseToCamelCase('word'), 'word')

  def testSnakeCaseToCamelCaseMultipleWords(self):
    self.assertEqual(text_utils.SnakeCaseToCamelCase('wd1_wd2'), 'wd1Wd2')

  def testSnakeCaseToCamelCaseStartsWithLowercase(self):
    self.assertEqual(text_utils.SnakeCaseToCamelCase('Wd1_wd2'), 'wd1Wd2')

  def testToSnakeCasedDictEmpty(self):
    self.assertEqual(text_utils.ToSnakeCaseDict({}), {})

  def testToSnakeCasedDictSimple(self):
    test_dict = {'some_field': 'SomeValue', 'some_other_field': 2}
    self.assertEqual(
        text_utils.ToSnakeCaseDict(test_dict), {
            'someField': 'SomeValue',
            'someOtherField': 2
        })

  def testToSnakeCasedDictNested(self):
    test_dict = {'some_field': {'another_field': 3}}
    self.assertEqual(
        text_utils.ToSnakeCaseDict(test_dict),
        {'someField': {
            'anotherField': 3
        }})

  def testToSnakeCasedDictMixed(self):
    test_dict = {'some_field': {'another_field': 3}, 'third_field': [1, 2]}
    self.assertEqual(
        text_utils.ToSnakeCaseDict(test_dict), {
            'someField': {
                'anotherField': 3
            },
            'thirdField': [1, 2]
        })


if __name__ == '__main__':
  test_case.main()
