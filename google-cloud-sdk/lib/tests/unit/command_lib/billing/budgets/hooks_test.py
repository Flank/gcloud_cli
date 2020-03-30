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
# Lint as: python3
"""Tests for google3.third_party.py.tests.unit.command_lib.billing.hooks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.billingbudgets import hooks
from tests.lib import parameterized
from tests.lib import test_case


class HooksTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.named_parameters([
      ('int', '100', False),
      ('non-zero float', '100.45', False),
      ('float', '.45', False),
      ('int with currency', '100USD', False),
      ('float with currency', '100.45USD', False),
      ('no number after decimal', '100.', True),
      ('two letter currency', '100.45US', True),
  ])
  def testCheckMoneyRegex(self, input_string, expected_throws_error):
    actual_throws_error = False
    try:
      hooks.CheckMoneyRegex(input_string)
    except hooks.InvalidBudgetAmountInput:
      actual_throws_error = True
    self.assertEqual(actual_throws_error, expected_throws_error)

  @parameterized.named_parameters([
      ('units, nanos, currency', '123.45USD', '123', '45', 'USD'),
      ('units, currency', '123USD', '123', '0', 'USD'),
      ('units, nanos', '123.45', '123', '45', ''),
      ('units', '123', '123', '0', ''),
      ('nanos', '.45', '0', '45', ''),
      ('nanos, currency', '.45USD', '0', '45', 'USD')
  ])
  def testParseToMoney(
      self, money_input, expected_units, expected_nanos, expected_currency):
    expected_output = hooks.GetMessagesModule().GoogleTypeMoney(
        units=int(expected_units),
        nanos=int(expected_nanos),
        currencyCode=expected_currency)
    self.assertEqual(hooks.ParseToMoneyType(money_input), expected_output)

  @parameterized.named_parameters([
      ('no rules plus one rule', [], ['a'], ['a']),
      ('one rule plus one rule', ['a'], ['b'], ['a', 'b']),
      ('one rule plus same rule', ['a'], ['a'], ['a']),
      ('two rules plus two different rules',
       ['a', 'b'], ['c', 'd'], ['a', 'b', 'c', 'd']),
  ])
  def testUpdateThresholdRules(
      self, existing_rules, added_rules, expected_all_rules):
    output = hooks.AddRules(existing_rules, added_rules)
    self.assertEqual(output, expected_all_rules)


if __name__ == '__main__':
  test_case.main()
