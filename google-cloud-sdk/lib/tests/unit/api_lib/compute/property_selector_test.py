# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the property_selector module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.compute import property_selector
from tests.lib import test_case
from six.moves import range  # pylint: disable=redefined-builtin


class ProperySelectorTest(test_case.TestCase):

  def SetUp(self):
    self.object = {
        'string': 'one',
        'integer': 123,
        'integerList': list(range(20)),
        'dict': {'string': 'one', 'integer': 2},
        'listOfDicts': [
            {'string': 'one', 'hello': 'world'},
            {'string': 'two'},
            {'string': 'three', 'another': 'string'}],
        'dictOfDicts': {'dictOne': {'string': 'one'},
                        'dictTwo': {'string': 'two', 'hello': 'world'},
                        'dictThree': {'string': 'three', 'another': 1}},
        'anotherListOfDicts': [
            {'keyOne': 1, 'keyTwo': 2, 'keyThree': 3},
            {'keyOne': 11, 'keyTwo': 22, 'keyThree': 33},
            {'keyOne': 111, 'keyTwo': 222, 'keyThree': 333}],
        'nested': [
            {'x': [
                {'y': [1, 2]}, {'y': [2, 3]}],
             'z': [555]},
            {'x': [
                {'y': [4, 5]}, {'y': [5, 6]}],
             'z': [777]}]
    }

  def TestFiltering(self, properties, expected):
    selector = property_selector.PropertySelector(properties=properties)
    self.assertEqual(selector.Apply(self.object), expected)

  def testFilteringWithSinglePropertyCases(self):
    self.TestFiltering([], self.object)
    self.TestFiltering(['nonExistentKey'], {})
    self.TestFiltering(['string'], {'string': 'one'})
    self.TestFiltering(['integer'], {'integer': 123})
    self.TestFiltering(['integerList.x'], {})
    self.TestFiltering(['integerList.string'], {})

    self.TestFiltering(
        ['integerList[0]'],
        {'integerList': [
            0, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None]})

    self.TestFiltering(
        ['integerList[1]'],
        {'integerList': [
            None, 1, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None]})

    self.TestFiltering(
        ['integerList[2]'],
        {'integerList': [
            None, None, 2, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None]})

    # Ensures that indices that begin with "0" are treated as base-10
    # integers.
    self.TestFiltering(
        ['integerList[011]'],
        {'integerList': [
            None, None, None, None, None, None, None, None, None,
            None, None, 11, None, None, None, None, None, None, None, None]})

    # Ensures that out-of-bound index accesses are handled properly.
    self.TestFiltering(['integerList[99999]'], {})

    self.TestFiltering(['dict.string'], {'dict': {'string': 'one'}})
    self.TestFiltering(['dict.integer'], {'dict': {'integer': 2}})

    self.TestFiltering(
        ['listOfDicts'],
        {'listOfDicts': [
            {'hello': 'world', 'string': 'one'},
            {'string': 'two'},
            {'another': 'string', 'string': 'three'}]})

    self.TestFiltering(
        ['listOfDicts[1]'],
        {'listOfDicts': [None, {'string': 'two'}, None]})

    self.TestFiltering(
        ['listOfDicts[2]'],
        {'listOfDicts': [None, None,
                         {'string': 'three', 'another': 'string'}]})

    self.TestFiltering(
        ['listOfDicts[].nonExistentKey'], {})

    self.TestFiltering(
        ['dictOfDicts.dictOne'],
        {'dictOfDicts': {'dictOne': {'string': 'one'}}})

    self.TestFiltering(
        ['dictOfDicts.dictOne.string'],
        {'dictOfDicts': {'dictOne': {'string': 'one'}}})

    self.TestFiltering(
        ['dictOfDicts.dictTwo'],
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}}})

    self.TestFiltering(
        ['anotherListOfDicts[].keyOne'],
        {'anotherListOfDicts': [
            {'keyOne': 1}, {'keyOne': 11}, {'keyOne': 111}]})

    self.TestFiltering(
        ['listOfDicts[].hello'],
        {'listOfDicts': [{'hello': 'world'}, None, None]})

    self.TestFiltering(['listOfDicts[1].hello'], {})

    self.TestFiltering(['garbage[1].x'], {})
    self.TestFiltering(['garbage[].x'], {})

    self.TestFiltering(
        ['nested[].x[].y'],
        {'nested': [
            {'x': [{'y': [1, 2]}, {'y': [2, 3]}]},
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}]}]})

    self.TestFiltering(
        ['nested[].x[0].y'],
        {'nested': [
            {'x': [{'y': [1, 2]}, None]},
            {'x': [{'y': [4, 5]}, None]}]})

    self.TestFiltering(
        ['nested[1].x[].y'],
        {'nested': [
            None,
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}]}]})

  def testFilteringMultiplePropertyCases(self):
    self.TestFiltering(
        ['string',
         'integer',
         'nonExistentKey'],
        {'integer': 123, 'string': 'one'})

    self.TestFiltering(
        ['dictOfDicts.dictTwo',
         'listOfDicts[0]'],
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'}, None, None]})

    self.TestFiltering(
        ['integerList[0]',
         'integerList[00019]',
         'integerList[6]',
         'integerList[3]'],
        {'integerList': [
            0, None, None, 3, None, None, 6, None, None, None, None, None,
            None, None, None, None, None, None, None, 19]})

    self.TestFiltering(
        ['dictOfDicts.dictTwo',
         'dictOfDicts.dictThree'],
        {'dictOfDicts':
         {'dictThree': {'string': 'three', 'another': 1},
          'dictTwo': {'string': 'two', 'hello': 'world'}}})

    self.TestFiltering(
        ['listOfDicts[].string',
         'listOfDicts[0].hello'],
        {'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three'}]})

    self.TestFiltering(
        ['listOfDicts[].string',
         'listOfDicts[0].hello',
         'listOfDicts[].another'],
        {'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.TestFiltering(
        ['listOfDicts[1].string',
         'listOfDicts[].string',
         'listOfDicts[0].hello',
         'integer',
         'listOfDicts[0].string',
         'listOfDicts[].another',
         'string'],
        {'string': 'one',
         'integer': 123,
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.TestFiltering(
        ['listOfDicts[1].string',
         'listOfDicts[].string',
         'listOfDicts[0].hello',
         'integer',
         'dictOfDicts.dictOne.string',
         'dictOfDicts.dictTwo.hello',
         'listOfDicts[0].string',
         'listOfDicts[].another',
         'string'],
        {'string': 'one',
         'integer': 123,
         'dictOfDicts': {'dictTwo': {'hello': 'world'},
                         'dictOne': {'string': 'one'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.TestFiltering(
        ['listOfDicts[1].string',
         'listOfDicts[].string',
         'listOfDicts[0].hello',
         'integer',
         'dictOfDicts.dictOne.string',
         'dictOfDicts.dictTwo',
         'dictOfDicts.dictTwo.hello',
         'listOfDicts[0].string',
         'listOfDicts[].another',
         'string'],
        {'string': 'one',
         'integer': 123,
         'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'},
                         'dictOne': {'string': 'one'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

  def testFilteringOrder(self):
    self.TestFiltering(
        ['listOfDicts[0].hello',
         'listOfDicts[].string',
         'integer',
         'dictOfDicts.dictTwo',
         'listOfDicts[].another',
         'string'],
        collections.OrderedDict([
            ('listOfDicts',
             [collections.OrderedDict([
                 ('hello', 'world'), ('string', 'one')]),
              collections.OrderedDict([
                  ('string', 'two')]),
              collections.OrderedDict([
                  ('string', 'three'), ('another', 'string')])]),
            ('integer', 123),
            ('dictOfDicts', collections.OrderedDict([
                ('dictTwo',
                 collections.OrderedDict([
                     ('hello', 'world'), ('string', 'two')]))])),
            ('string', 'one')
        ]))

    self.TestFiltering(
        ['dictOfDicts.dictTwo',
         'integer',
         'string',
         'listOfDicts[0].hello',
         'listOfDicts[].another',
         'listOfDicts[].string'],
        collections.OrderedDict([
            ('dictOfDicts', collections.OrderedDict([
                ('dictTwo',
                 collections.OrderedDict([
                     ('hello', 'world'), ('string', 'two')]))])),
            ('integer', 123),
            ('string', 'one'),
            ('listOfDicts',
             [collections.OrderedDict([
                 ('hello', 'world'), ('string', 'one')]),
              collections.OrderedDict([
                  ('string', 'two')]),
              collections.OrderedDict([
                  ('another', 'string'), ('string', 'three')])]),
        ]))

    # Individual index accesses always have higher priority than slice
    # accesses for a key. The next two tests ensure that this property
    # is held.
    self.TestFiltering(
        ['anotherListOfDicts[].keyOne',
         'anotherListOfDicts[0].keyTwo'],
        collections.OrderedDict([
            ('anotherListOfDicts',
             [collections.OrderedDict([
                 ('keyTwo', 2), ('keyOne', 1)]),
              collections.OrderedDict([
                  ('keyOne', 11)]),
              collections.OrderedDict([
                  ('keyOne', 111)])])
        ]))

    self.TestFiltering(
        ['anotherListOfDicts[0].keyTwo',
         'anotherListOfDicts[].keyOne'],
        collections.OrderedDict([
            ('anotherListOfDicts',
             [collections.OrderedDict([
                 ('keyTwo', 2), ('keyOne', 1)]),
              collections.OrderedDict([
                  ('keyOne', 11)]),
              collections.OrderedDict([
                  ('keyOne', 111)])])
        ]))

  def testFilteringCopiesResult(self):
    expected = {'string': 'one',
                'integer': 123,
                'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'},
                                'dictOne': {'string': 'one'}},
                'listOfDicts': [{'string': 'one', 'hello': 'world'},
                                {'string': 'two'},
                                {'string': 'three', 'another': 'string'}]}

    selector = property_selector.PropertySelector([
        'listOfDicts[1].string',
        'listOfDicts[].string',
        'listOfDicts[0].hello',
        'integer',
        'dictOfDicts.dictOne.string',
        'dictOfDicts.dictTwo',
        'dictOfDicts.dictTwo.hello',
        'listOfDicts[0].string',
        'listOfDicts[].another',
        'string',
    ])
    res = selector.Apply(self.object)

    self.assertEqual(res, expected)

    # Ensures that Apply() makes a deep copy of its result
    # before returning it to the client.
    self.object['dictOfDicts']['dictTwo'] = 'garbage'
    self.object['listOfDicts'][0] = 'garbage'
    self.object['listOfDicts'][1]['string'] = 'garbage'
    self.object['integer'] = 300
    self.assertEqual(res, expected)

  def testGetProperty(self):

    def TestGetProperty(prop, expected):
      getter = property_selector.PropertyGetter(prop)
      self.assertEqual(getter.Get(self.object), expected)

    TestGetProperty('integerList[2]', 2)
    TestGetProperty('integerList[99999]', None)
    TestGetProperty('anotherListOfDicts[0].keyOne', 1)
    TestGetProperty('anotherListOfDicts[].keyOne', [1, 11, 111])
    TestGetProperty('nested[].x[].y',
                    [[[1, 2], [2, 3]], [[4, 5], [5, 6]]])

  def testIllegalProperties(self):

    def TestBadProperty(prop):
      with self.assertRaises(property_selector.IllegalProperty):
        getter = property_selector.PropertyGetter(prop)
        getter.Get(self.object)

    TestBadProperty('')
    TestBadProperty('[0]')
    TestBadProperty('attribute]0[')
    TestBadProperty('attribute[0')
    TestBadProperty('attribute[0][1]')
    TestBadProperty('attribute[][1]')
    TestBadProperty('attribute[][]')
    TestBadProperty('attribute[0.attributeTwo')
    TestBadProperty('attribute[0[.attributeTwo')
    TestBadProperty('attribute...')
    TestBadProperty('.')
    TestBadProperty('...')

  def testTrasnformations(self):
    selector = property_selector.PropertySelector(transformations=[
        ('string', lambda x: x.upper()),
        ('dictOfDicts.dictOne.string', lambda x: x * 4),
        ('nonExistentKey.nonExistentKey', lambda _: 'Hello!'),
        ('listOfDicts[].string', lambda x: x * 3),
        ('anotherListOfDicts', lambda x: 'list replacement'),
        ('integerList[5]', lambda x: x ** 2),
        ('integerList[10]', lambda x: x ** 3),
        ('nested[].x[].y[]', lambda x: x ** 4),
    ])
    res = selector.Apply(self.object)
    self.assertEqual(res, {
        'string': 'ONE',
        'integer': 123,
        'integerList': [0, 1, 2, 3, 4, 25, 6, 7, 8, 9, 1000,
                        11, 12, 13, 14, 15, 16, 17, 18, 19],
        'dict': {'string': 'one', 'integer': 2},
        'listOfDicts': [
            {'string': 'oneoneone', 'hello': 'world'},
            {'string': 'twotwotwo'},
            {'string': 'threethreethree', 'another': 'string'}],
        'dictOfDicts': {'dictOne': {'string': 'oneoneoneone'},
                        'dictTwo': {'string': 'two', 'hello': 'world'},
                        'dictThree': {'string': 'three', 'another': 1}},
        'anotherListOfDicts': 'list replacement',
        'nested': [
            {'x': [
                {'y': [1, 16]}, {'y': [16, 81]}],
             'z': [555]},
            {'x': [
                {'y': [256, 625]}, {'y': [625, 1296]}],
             'z': [777]}]
    })

  def testFilteringAndTransformations(self):
    selector = property_selector.PropertySelector(
        properties=[
            'dictOfDicts.dictTwo',
            'listOfDicts[0]',
            'string',
        ],
        transformations=[
            ('string', lambda x: x.upper()),
            ('dictOfDicts.dictTwo.string', lambda x: x * 2),
            ('listOfDicts[].string', lambda x: x.upper()),
            ('nested', lambda x: 'Hello'),
        ])
    res = selector.Apply(self.object)
    self.assertEqual(res, {
        'string': 'ONE',
        'dictOfDicts': {'dictTwo': {'string': 'twotwo', 'hello': 'world'}},
        'listOfDicts': [{'string': 'ONE', 'hello': 'world'}, None, None],
    })


if __name__ == '__main__':
  test_case.main()
