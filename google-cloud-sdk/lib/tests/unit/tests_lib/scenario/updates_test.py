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

"""Tests for the updates module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import encoding
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.scenario import updates


class ModeTests(test_case.TestCase, parameterized.TestCase):

  @parameterized.parameters([
      (None, [], False),
      ('', [], False),
      ('RESULT', [updates.Mode.RESULT], False),
      ('RESULT,UX,API_REQUESTS',
       [updates.Mode.RESULT, updates.Mode.UX, updates.Mode.API_REQUESTS],
       False),
      ('RESULT,UX,API_REQUESTS,API_RESPONSES',
       [updates.Mode.RESULT, updates.Mode.UX, updates.Mode.API_REQUESTS,
        updates.Mode.API_RESPONSES], True),
  ])
  def testCurrentMode(self, value, expected, makes_api_calls):
    encoding.SetEncodedValue(os.environ, updates.UPDATE_MODES_ENV_VAR, value)
    actual = updates.Mode.Current()
    self.assertEqual(expected, actual)
    self.assertEqual(makes_api_calls, updates.Mode.MakesApiCalls())

  @parameterized.parameters([
      ('BOGUS'),
      ('BOGUS,RESULT'),
  ])
  def testCurrentModeErrors(self, value):
    with self.assertRaises(updates.Error):
      encoding.SetEncodedValue(os.environ, updates.UPDATE_MODES_ENV_VAR, value)
      updates.Mode.Current()


class ContextTests(test_case.TestCase):

  def testAttributes(self):
    backing_data = {'foo': 'bar'}
    field = 'field'
    context = updates.Context(backing_data, field, updates.Mode.RESULT)
    self.assertEqual(backing_data, context.BackingData())
    self.assertEqual(field, context.Field())
    self.assertFalse(context.WasMissing())
    self.assertEqual(('?', '?'), context.Location())

    context = updates.Context(backing_data, field, updates.Mode.RESULT,
                              was_missing=True, location='asdf')
    self.assertEqual(backing_data, context.BackingData())
    self.assertEqual(field, context.Field())
    self.assertTrue(context.WasMissing())
    self.assertEqual('asdf', context.Location())

  def testForKeyAndUpdate(self):
    backing_data = {'a': {'b': {'c': 'd', 'e': 'f'}}}
    context = updates.Context(backing_data, 'a', updates.Mode.RESULT)

    c = context.ForKey('b.c')

    # No update, because no modes given.
    c.Update('new d', [])
    self.assertEqual({'c': 'd', 'e': 'f'}, c.BackingData())
    self.assertEqual({'a': {'b': {'c': 'd', 'e': 'f'}}}, backing_data)

    # Updates reflected in original data.
    c.Update('new d', [updates.Mode.RESULT])
    self.assertEqual({'c': 'new d', 'e': 'f'}, c.BackingData())
    self.assertEqual({'a': {'b': {'c': 'new d', 'e': 'f'}}}, backing_data)

    # Update with None should remove element
    c.Update(None, [updates.Mode.RESULT])
    self.assertEqual({'e': 'f'}, c.BackingData())
    self.assertEqual({'a': {'b': {'e': 'f'}}}, backing_data)

  def testLocationFromYaml(self):
    data_string = """\
a:
  b:
    c: d
    e: f
"""
    data = yaml.load(data_string, round_trip=True)
    context = updates.Context(data, 'a', updates.Mode.RESULT)
    self.assertEqual(('1', '0'), context.Location())

    c = context.ForKey('b.c')
    self.assertEqual(('3', '4'), c.Location())


if __name__ == '__main__':
  test_case.main()
