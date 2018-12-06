# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests of the Condition API message wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import condition
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.run import base


class ConditionTest(base.ServerlessApiBase, parameterized.TestCase):
  """Sanity check for Condition."""

  def SetUp(self):
    self.condition_class = self.serverless_messages.ConfigurationCondition

  def testGetStatus(self):
    """Check status converts bool as expected."""
    for st in ['True', 'TRUE']:
      cond = condition.Conditions(
          [self.condition_class(type='type1', status=st)])
      self.assertTrue(cond['type1']['status'])
    for st in ['false', 'Unknown', 'foo-bar']:
      cond = condition.Conditions(
          [self.condition_class(type='type1', status=st)])
      self.assertFalse(cond['type1']['status'])

  def testGet(self):
    """Sanity check for getter."""
    cond1 = self.condition_class(type='type1', status='False')
    cond = condition.Conditions([cond1])
    self.assertEqual(cond1.status, str(cond['type1']['status']))
    self.assertEqual(1, len(cond))

    cond2 = self.condition_class(
        type='type2', status='False', message='bar')
    cond = condition.Conditions([cond1, cond2])
    self.assertEqual(cond2.message, cond['type2']['message'])
    self.assertEqual(cond2.message, cond['type2']['message'])
    self.assertEqual(cond2.status, str(cond['type2']['status']))
    self.assertEqual(2, len(cond))

  def testGet_KeyError(self):
    cond = condition.Conditions([])
    with self.assertRaises(KeyError):
      _ = cond['non-existing-type']

  def testContain(self):
    cond = condition.Conditions(
        [self.condition_class(type='type1', status='False')])
    self.assertTrue('type1' in cond)
    self.assertFalse('type2' in cond)

  def testIter(self):
    cond = condition.Conditions(
        [self.condition_class(type='type1', status='False'),
         self.condition_class(type='type2', status='False')])
    for cond_type in cond:
      self.assertFalse(cond[cond_type]['status'])

  # pylint: disable=bad-whitespace
  @parameterized.parameters(
      ({'status': 'False'}, {'status':'True', 'message':'foo'}, None),
      ({'status': 'False', 'message': 'bar'},
       {'status':'True', 'message':'foo'}, 'bar'),
      ({'status': 'False', 'message': 'bar'}, {'status':'True'}, 'bar'))
  # pylint: enable=bad-whitespace
  def testMessage_Error(self, type1_args, type2_args, result):
    """The message is always whatever the error is, otherwise why not ready."""
    cond = condition.Conditions(
        [self.condition_class(type='type1', **type1_args),
         self.condition_class(type='type2', **type2_args)],
        ready_condition='type1')
    self.assertEqual(cond.DescriptiveMessage(), result)

  def testMessage_Unready(self):
    cond = condition.Conditions(
        [self.condition_class(type='type1', status='Unknown', message='bar'),
         self.condition_class(type='type2', status='Unknown', message='foo')],
        ready_condition='type1')
    self.assertEqual(cond.DescriptiveMessage(), 'bar')

  def testIsTerminal(self):
    """Test condition reports itself as terminal when it is."""
    cond = condition.Conditions(
        [self.condition_class(type='type1', status='False'),
         self.condition_class(type='type2', status='True')],
        ready_condition='type1')
    self.assertTrue(cond.IsTerminal())

    cond = condition.Conditions(
        [self.condition_class(type='type1', status='False'),
         self.condition_class(type='type2', status='False')],
        ready_condition='type2')
    self.assertTrue(cond.IsTerminal())

  def testNotTerminal(self):
    """Test condition reports itself as not terminal when it is not."""
    cond = condition.Conditions(
        [self.condition_class(type='type1', status='Unknown'),
         self.condition_class(type='type2', status='True')],
        ready_condition='type1')
    self.assertFalse(cond.IsTerminal())

    cond = condition.Conditions(
        [self.condition_class(type='type1', status='False'),
         self.condition_class(type='type2', status='True')],
        ready_condition='type2',
        observed_generation=1, generation=2)
    self.assertFalse(cond.IsTerminal())


if __name__ == '__main__':
  test_case.main()
