# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Tests for core yaml util file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import yaml
from tests.lib import test_case

import six


class YAMLTest(test_case.Base):

  def testJSONSerialization(self):
    data = yaml.load("""\
                     foo: [a, b, c]
                     bar: [d, e, f]
                     """)
    j = json.dumps(data)
    self.assertEqual(json.loads(j),
                     {'foo': ['a', 'b', 'c'], 'bar': ['d', 'e', 'f']})

  def testInadequateRoundTrip(self):
    data = yaml.load("""\
                     boolean:
                       true
                     dict:
                       xyz: 789
                       abc: 123
                     floating:
                       3.14
                     integer:
                       123
                     list:
                       - a
                       - 2
                       - bcd
                       - 456
                     string:
                       abc
                     """, round_trip=True)

    value = data['boolean']
    self.assertEqual(True, value)
    self.assertFalse(hasattr(value, 'lc'))

    value = data['dict']
    self.assertEqual(
        [('xyz', 789), ('abc', 123)],
        [(k, v) for k, v in six.iteritems(value)])
    self.assertEqual(3, value.lc.line)
    self.assertEqual(23, value.lc.col)

    value = data['floating']
    self.assertEqual(3.14, value)
    self.assertFalse(hasattr(value, 'lc'))

    value = data['integer']
    self.assertEqual(123, value)
    self.assertFalse(hasattr(value, 'lc'))

    value = data['list']
    self.assertEqual(
        ['a', 2, 'bcd', 456],
        value)
    self.assertEqual(10, value.lc.line)
    self.assertEqual(23, value.lc.col)

    value = data['string']
    self.assertEqual('abc', value)
    self.assertFalse(hasattr(value, 'lc'))

  def testLocationValueLoad(self):
    data = yaml.load("""\
                     boolean:
                       true
                     dict:
                       xyz: 789
                       abc: 123
                     floating:
                       3.14
                     integer:
                       123
                     list:
                       - a
                       - 2
                       - bcd
                       - 456
                     string:
                       abc
                     """, location_value=True)

    obj = data['boolean']
    self.assertEqual(True, obj.value)
    self.assertEqual(1, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

    obj = data['dict']
    self.assertEqual(
        [('xyz', '789'), ('abc', '123')],
        [(k, v) for k, v in six.iteritems(obj.value)])
    self.assertEqual(
        [('xyz', 789), ('abc', 123)],
        [(k, v.value) for k, v in six.iteritems(obj.value)])
    self.assertEqual(3, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

    obj = data['floating']
    self.assertEqual(3.14, obj.value)
    self.assertEqual(6, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

    obj = data['integer']
    self.assertEqual(123, obj.value)
    self.assertEqual(8, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

    obj = data['list']
    self.assertEqual(
        ['a', '2', 'bcd', '456'],
        obj.value)
    self.assertEqual(
        ['a', 2, 'bcd', 456],
        [v.value for v in obj.value])
    self.assertEqual(10, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

    obj = data['string']
    self.assertEqual('abc', obj.value)
    self.assertEqual(15, obj.lc.line)
    self.assertEqual(23, obj.lc.col)

  def testStripLocations(self):
    lv_data = yaml.load("""\
        null: null
        boolean: true
        integer: 123
        float: 3.14
        string: abc
        dict:
          xyz: 789
          abc: 123
        list:
        - a
        - 2
    """, location_value=True)
    data = yaml.strip_locations(lv_data)

    self.assertEqual(None, data['null'])
    self.assertEqual(True, data['boolean'])
    self.assertEqual(123, data['integer'])
    self.assertEqual(3.14, data['float'])
    self.assertEqual('abc', data['string'])
    self.assertIsInstance(data['dict'], dict)
    self.assertIsInstance(data['list'], list)

  def testAllJJSONSerialization(self):
    expected = """\
name: Doc1
boolean: false
dict:
 xyz: 012
 abc: 897
integer: 123
list:
- a
- b
- c
- d
---
 name: Doc2
 dict:
   xyz: 789
   abc: 456
 integer: 456
 list:
 - e
 - f
 - g
 - h
"""
    data = list(yaml.load_all(expected, round_trip=True))
    self.assertEqual(len(data), 2)
    json_out = yaml.dump_all_round_trip(data)
    data_after = list(yaml.load_all(json_out, round_trip=True))
    self.assertCountEqual(data, data_after)


if __name__ == '__main__':
  test_case.main()
