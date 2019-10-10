# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Unit tests for the resource_property module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_property
from tests.lib import subtests
from tests.lib import test_case

import six
from six.moves import range  # pylint: disable=redefined-builtin


class PropertyGetTest(subtests.Base):

  def RunSubTest(self, r, key, default=None):
    return resource_property.Get(r, key, default)

  def testGetKey(self):

    r = {'meta': 'name'}

    self.Run('name', r, ['meta'])
    self.Run(None, r, ['meta', 'count'])

  def testGetKeyBuiltin(self):

    # 'items' is a Python builtin function.
    r = {'items': 'name'}

    self.Run('name', r, ['items'])

  def testGetDict(self):

    r = {'a': {'b': {'c': {'d': 'abcd'}, 'd': 'abd'}}, 'x': {'y': 'xy'}}

    self.Run('abcd', r, ['a', 'b', 'c', 'd'])
    self.Run('abd', r, ['a', 'b', 'd'])
    self.Run('xy', r, ['x', 'y'])

  def testGetDictInList(self):

    r = {'meta': [{'key': 'size', 'value': 123}]}

    self.Run('size', r, ['meta', 0, 'key'])
    self.Run(123, r, ['meta', 0, 'value'])
    self.Run(None, r, ['meta', 0, 'unknown'])

  def testGetDictInListBuiltin(self):

    r = {'items': [{'key': 'size', 'value': 123}]}

    self.Run('size', r, ['items', 0, 'key'])
    self.Run(123, r, ['items', 0, 'value'])
    self.Run(None, r, ['items', 0, 'unknown'])

  def testGetSetInDict(self):

    r = {'meta': {'key': 'sizes', 'value': set([456, 123, 789])}}

    self.Run('sizes', r, ['meta', 'key'])
    self.Run([123, 456, 789], r, ['meta', 'value'])

  def testGetObject(self):

    class PyObject(object):

      def __init__(self):
        self.key = 'bar'
        self.dictionary = {'1': 2, 3: 4}

    r = {
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
             'z': [777]}],
        'object': PyObject(),
    }

    self.Run(None, r, ['nonExistentKey'])
    self.Run('one', r, ['string'])
    self.Run(123, r, ['integer'])
    self.Run(None, r, ['integerList.x'])
    self.Run(None, r, ['integerList', 'string'])
    self.Run('bar', r, ['object', 'key'])
    self.Run(None, r, ['object', 'dictionary', 1])
    self.Run(2, r, ['object', 'dictionary', '1'])
    self.Run(4, r, ['object', 'dictionary', 3])
    self.Run(None, r, ['object', 'dictionary', '3'])
    self.Run(0, r, ['integerList', 0])
    self.Run(1, r, ['integerList', 1])
    self.Run(2, r, ['integerList', 2])
    self.Run(11, r, ['integerList', 11])
    self.Run(None, r, ['integerList', 99999])
    self.Run('one', r, ['dict', 'string'])
    self.Run(2, r, ['dict', 'integer'])
    self.Run([{'hello': 'world', 'string': 'one'},
              {'string': 'two'},
              {'another': 'string', 'string': 'three'}], r, ['listOfDicts'])
    self.Run({'string': 'two'}, r, ['listOfDicts', 1])
    self.Run({'string': 'three', 'another': 'string'}, r, ['listOfDicts', 2])
    self.Run({'string': 'one'}, r, ['dictOfDicts', 'dictOne'])
    self.Run('one', r, ['dictOfDicts', 'dictOne', 'string'])
    self.Run({'string': 'two', 'hello': 'world'}, r, ['dictOfDicts', 'dictTwo'])
    self.Run(None, r, ['listOfDicts', 1, 'hello'])
    self.Run(None, r, ['garbage', 1, 'x'])

  def testGetNamedTuple(self):

    point = collections.namedtuple('point', ['x', 'y'])
    r = point(123, 456)

    self.Run(123, r, ['x'])
    self.Run(456, r, ['y'])

  def testGetSerializedNamedTuple(self):

    point = collections.namedtuple('point', ['x', 'y'])
    r = resource_projector.MakeSerializable(point(123, 456))

    self.Run(123, r, ['x'])
    self.Run(456, r, ['y'])

  def testGetOrderedDict(self):

    r = collections.OrderedDict([('c', 3), ('b', 2), ('a', 1)])

    self.Run(1, r, ['a'])
    self.Run(2, r, ['b'])
    self.Run(3, r, ['c'])

  def testGetSerializedOrderedDict(self):

    r = collections.OrderedDict([('c', 3), ('b', 2), ('a', 1)])
    r = resource_projector.MakeSerializable(r)

    self.Run(1, r, ['a'])
    self.Run(2, r, ['b'])
    self.Run(3, r, ['c'])

  def testGetDataValue(self):

    r = {'camelName': 'camel', 'snake_name': 'snake'}

    # no key case bias
    self.Run('snake', r, ['snake_name'])
    self.Run('snake', r, ['SNAKE_NAME'])
    self.Run('snake', r, ['snakeName'])
    self.Run('camel', r, ['camel_name'])
    self.Run('camel', r, ['camelName'])

  def testGetDataMultiValue(self):

    r = {
        'abc': [
            {'xyz': 'zero'},
            {'xyz': 'one'},
            {'xyz': 'two'},
        ],
    }

    self.Run('zero', r, ['abc', 0, 'xyz'])
    self.Run('one', r, ['abc', 1, 'xyz'])
    self.Run('two', r, ['abc', 2, 'xyz'])
    self.Run(None, r, ['abc', 3, 'xyz'])
    self.Run(['zero', 'one', 'two'], r, ['abc', None, 'xyz'])
    self.Run(['zero', 'one', 'two'], r, ['abc', 'xyz'])

  def testGetMetaDataValue(self):

    r = {'metadata': {'items':
                      [{'key': 'x', 'value': 123},
                       {'key': 'y', 'value': '456'},
                       {'key': 'z', 'value': 'hello'},
                       {'key': 'u', 'value': 'python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ'},
                       {'key': 'snake_name', 'value': 'snake'},
                       {'key': 'camelName', 'value': 'camel'}]}}

    # direct reference numbers => numbers and strings => strings
    self.Run(123, r, ['metadata', 'x'])
    self.Run('456', r, ['metadata', 'y'])
    self.Run('hello', r, ['metadata', 'z'])
    self.Run('python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ', r, ['metadata', 'u'])

    # no key case bias
    self.Run('snake', r, ['metadata', 'snake_name'])
    self.Run('snake', r, ['metadata', 'SNAKE_NAME'])
    self.Run('snake', r, ['metadata', 'snakeName'])
    self.Run('camel', r, ['metadata', 'camel_name'])
    self.Run('camel', r, ['metadata', 'camelName'])

    # scalar values don't have named attributes
    self.Run(None, r, ['metadata', 'x', 'a'])
    self.Run(None, r, ['metadata', 'y', 'a'])
    self.Run(None, r, ['metadata', 'z', 'a'])

    # a slice of a deserialized numeric value is empty
    self.Run(None, r, ['metadata', 'x', None])
    self.Run(None, r, ['metadata', 'y', None])

    # a slice of a deserialized string is the string (an array of characters)
    self.Run('hello', r, ['metadata', 'z', None])
    self.Run('python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ', r, ['metadata', 'u', None])

    # we really shouldn't know that 'items' is magic, but peeking is allowed
    self.Run(r['metadata']['items'], r, ['metadata', 'items'])

    # dotted name reference to explicit MetaDataValue data
    self.Run(123, r, ['metadata', 'items', 'x'])
    self.Run('456', r, ['metadata', 'items', 'y'])
    self.Run('hello', r, ['metadata', 'items', 'z'])
    self.Run('python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ', r, ['metadata', 'items', 'u'])

  def testGetMetaDataValueDeserialize(self):

    r = {'metadata': {'items': [{'key': 'x', 'value': '{"z": "cracked"}'}]}}

    # direct access returns raw serialized string
    self.Run('{"z": "cracked"}', r, ['metadata', 'x'])

    # reference attribute in deserialized data
    self.Run('cracked', r, ['metadata', 'x', 'z'])

    # slice deserializes to the object
    self.Run({'z': 'cracked'}, r, ['metadata', 'x', None])

  def testGetMetaDict(self):

    r = {'metadict': [{'metric': 'x', 'max': 123},
                      {'metric': 'y', 'max': '456'},
                      {'metric': 'z', 'max': 'hello'},
                      {'metric': 'u', 'max': 'python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ'}]}

    # direct reference numbers => numbers and strings => strings
    self.Run(123, r, ['metadict', 'metric', 'x', 'max'])
    self.Run('456', r, ['metadict', 'metric', 'y', 'max'])
    self.Run('hello', r, ['metadict', 'metric', 'z', 'max'])
    self.Run('python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ', r, ['metadict', 'metric', 'u', 'max'])

    # scalar values don't have named attributes
    self.Run(None, r, ['metadict', 'metric', 'x', 'max', 'a'])
    self.Run(None, r, ['metadict', 'metric', 'y', 'max', 'a'])
    self.Run(None, r, ['metadict', 'metric', 'z', 'max', 'a'])

  def testGetNone(self):

    r = None

    self.Run(None, r, [])
    self.Run(None, r, [None])
    self.Run(None, r, ['a'])

  def testGetIndex(self):

    r = {'a': ['A', 'Z'], 'b': ('A', 'Z'), 'c': {'A': 1, 'Z': 24}}

    self.Run(r, r, [])
    self.Run(r, r, [None])
    self.Run(None, r, [0])

    self.Run('A', r, ['a', 0])
    self.Run('Z', r, ['a', 1])
    self.Run('Z', r, ['a', -1])
    self.Run('A', r, ['a', -2])
    self.Run(['A', 'Z'], r, ['a', None])
    self.Run(None, r, ['a', 'b'])

    self.Run('A', r, ['b', 0])
    self.Run('Z', r, ['b', 1])
    self.Run('Z', r, ['b', -1])
    self.Run('A', r, ['b', -2])
    self.Run(('A', 'Z'), r, ['b', None])
    self.Run(None, r, ['b', 'c'])

    self.Run(None, r, ['c', 0])
    self.Run(None, r, ['c', 1])
    self.Run(None, r, ['c', -1])
    self.Run(None, r, ['c', -2])
    self.Run({'A': 1, 'Z': 24}, r, ['c', None])
    self.Run(1, r, ['c', 'A'])
    self.Run(24, r, ['c', 'Z'])
    self.Run(None, r, ['c', 'a'])

  def testGetDictSlice(self):

    r = collections.OrderedDict()
    r['a'] = {'x': ['A', 'Z']}
    r['b'] = {'x': ('A', 'Z')}
    r['c'] = {'A': 1, 'Z': 24}

    self.Run([['A', 'Z'], ('A', 'Z'), None], r, [None, 'x'])
    self.Run([None, None, 1], r, [None, 'A'])
    self.Run([{'x': ['A', 'Z']}, {'x': ('A', 'Z')}, {'A': 1, 'Z': 24}],
             r, [None, None])

  def testGetLastDictSlice(self):

    r = {'dictslice': [{'name': 'Joe', 'age': 50},
                       {'name': 'Jan', 'age': 40},
                       {'eman': 'eoJ', 'ega': 55},
                       {'eman': 'naJ', 'ega': 44}]}

    self.Run(['Joe', 'Jan', None, None], r, ['dictslice', 'name'])
    self.Run([50, 40, None, None], r, ['dictslice', 'age'])
    self.Run(None, r, ['dictslice', 'foo'])

  def testGetEmptyDictSlice(self):

    r = {}

    self.Run({}, r, [])
    self.Run({}, r, [None])

  def testGetListSlice(self):

    r = [[['A', 'B'], ['Y', 'Z']], [['a', 'b'], ['y', 'z']], [[1, 2], [2, 3]]]

    self.Run([['A', 'B'], ['a', 'b'], [1, 2]], r, [None, 0])
    self.Run([['Y', 'Z'], ['y', 'z'], [2, 3]], r, [None, 1])
    self.Run([None, None, None], r, [None, 2])
    self.Run(
        [[['A', 'B'], ['Y', 'Z']], [['a', 'b'], ['y', 'z']], [[1, 2], [2, 3]]],
        r, [None, None])

    self.Run([['A', 'B'], ['Y', 'Z']], r, [0, None])
    self.Run([['a', 'b'], ['y', 'z']], r, [1, None])
    self.Run([[1, 2], [2, 3]], r, [2, None])
    self.Run(None, r, [3, None])

    self.Run([['A', 'B'], ['Y', 'Z']], r, [0])
    self.Run([['a', 'b'], ['y', 'z']], r, [1])
    self.Run([[1, 2], [2, 3]], r, [2])
    self.Run(None, r, [3])

  def testGetEmptyListSlice(self):

    r = []

    self.Run([], r, [])
    self.Run([], r, [None])

  def testGetIndexString(self):

    r = 'abc'

    self.Run('abc', r, [])
    self.Run('abc', r, [None])
    self.Run('a', r, [0])
    self.Run('b', r, [1])
    self.Run('c', r, [2])
    self.Run(None, r, [3])
    self.Run('c', r, [-1])
    self.Run('b', r, [-2])
    self.Run('a', r, [-3])
    self.Run(None, r, [-4])
    self.Run(None, r, ['a'])
    self.Run(None, r, [123])

  def testGetIndexnumber(self):

    r = 123

    self.Run(123, r, [])
    self.Run(None, r, [None])
    self.Run(None, r, [0])
    self.Run(None, r, [1])
    self.Run(None, r, [2])
    self.Run(None, r, [3])
    self.Run(None, r, [-1])
    self.Run(None, r, [-2])
    self.Run(None, r, [-3])
    self.Run(None, r, [-4])
    self.Run(None, r, ['a'])
    self.Run(None, r, [123])

  def testGetDefault(self):

    r = [1, 'b', None]

    self.Run(1, r, [0], 'UNDEFINED')
    self.Run('b', r, [1], 'UNDEFINED')
    self.Run(None, r, [2], 'UNDEFINED')
    self.Run('UNDEFINED', r, [3], 'UNDEFINED')
    self.Run('UNDEFINED', r, ['b'], 'UNDEFINED')

  def testGetBadKey(self):

    r = {'a': ['x', 'y', 'z']}

    self.Run('z', r, ['a', 2])
    self.Run(None, r, ['a', 2.0])
    self.Run(None, r, ['a', [1]])
    self.Run(None, r, ['a', {'index': 1}])

  def testGetSlice(self):

    r = [
        {
            'a': [
                {
                    'b': [
                        {
                            'c': 'A'
                        },
                        {
                            'c': 'B'
                        }
                    ],
                },
                {
                    'b': [
                        {
                            'c': 'C'
                        }
                    ],
                }
            ]
        },
        {
            'a': [
                {
                    'b': [
                        {
                            'c': 'D'
                        }
                    ],
                }
            ]
        },
        {
            'a': [
                {
                    'b': [
                        {
                            'c': 'E'
                        }
                    ],
                }
            ]
        }
    ]

    self.Run([[['A', 'B'], ['C']], [['D']], [['E']]],
             r,
             ['a', None, 'b', None, 'c'])
    self.Run([[['A', 'B'], ['C']], [['D']], [['E']]],
             r,
             ['a', None, 'b', 'c'])
    self.Run([[['A', 'B'], ['C']], [['D']], [['E']]],
             r,
             ['a', 'b', None, 'c'])
    self.Run([[['A', 'B'], ['C']], [['D']], [['E']]],
             r,
             ['a', 'b', 'c'])


class PropertyConvertCaseTest(subtests.Base):

  def RunSubTest(self, name, func):
    return func(name)

  def testConvertToCamelCase(self):

    def T(expected, name):
      return self.Run(
          expected, name, resource_property.ConvertToCamelCase, depth=2)

    T('camelCase', 'camelCase')
    T('camelCase', 'camel_case')

  def testConvertToSnakeCase(self):

    def T(expected, name):
      return self.Run(
          expected, name, resource_property.ConvertToSnakeCase, depth=2)

    T('snake_case', 'snakeCase')
    T('snake_http_case', 'snakeHTTPCase')
    T('snake_case', 'snake_case')

  def testConvertToAngrySnakeCase(self):

    def T(expected, name):
      return self.Run(
          expected, name, resource_property.ConvertToAngrySnakeCase, depth=2)

    T('ANGRY_SNAKE_CASE', 'angrySnakeCase')
    T('ANGRY_SNAKE_HTTP_CASE', 'angrySnakeHTTPCase')
    T('ANGRY_SNAKE_CASE', 'angry_snake_case')
    T('ANGRY_SNAKE_CASE', 'ANGRY_SNAKE_CASE')


class GetMessageFieldTypeTest(subtests.Base):

  def RunSubTest(self, key, message):
    return resource_property.GetMessageFieldType(key, message)

  def testGetMessageFieldType(self):

    def T(expected, key, message, exception=None):
      return self.Run(expected, key, message, exception=exception, depth=2)

    message = apis.GetMessagesModule('compute', 'v1').InstanceGroup

    T((six.text_type, ['name']),
      ['name'], message)
    T((six.text_type, ['namedPorts', 'name']),
      ['namedPorts', 'name'], message)
    T((six.text_type, ['namedPorts', 'name']),
      ['namedPorts', 1, 'name'], message)
    T((int, ['namedPorts', 'port']),
      ['named_ports', 'port'], message)
    T((int, ['namedPorts', 'port']),
      ['named_ports', None, 'port'], message)

    T(None, ['foo'], message, exception=KeyError)


class LookupFieldTest(subtests.Base):

  def RunSubTest(self, key, fields):
    return resource_property.LookupField(key, fields)

  def testLookupField(self):

    def T(expected, key, fields):
      return self.Run(expected, key, fields, depth=2)

    fields = {
        'someWhere.overThe.rainBow',
        'theWalrus.wasPaul',
        'sitting_on.a_corn_flake',
    }

    T(['someWhere', 'overThe', 'rainBow'],
      ['someWhere', 'overThe', 'rainBow'],
      fields)
    T(['someWhere', 'overThe', 'rainBow'],
      ['someWhere', 'over_the', 'rainBow'],
      fields)
    T(['someWhere', None, 'overThe', 1, 'rainBow'],
      ['someWhere', None, 'over_the', 1, 'rainBow'],
      fields)
    T(None,
      ['someWhere', 'overthe', 'rainBow'],
      fields)
    T(['theWalrus', 'wasPaul'],
      ['the_walrus', 'wasPaul'],
      fields)
    T(['theWalrus', 'wasPaul'],
      ['theWalrus', 'was_paul'],
      fields)
    T(None,
      ['theWalrus', 'waspaul'],
      fields)
    T(['sitting_on', 'a_corn_flake'],
      ['sittingOn', 'aCornFlake'],
      fields)

    T(None,
      ['someWhere', 'overThe', 'rainBow'],
      {})
    T(None,
      ['someWhere', 'over_the', 'rainBow'],
      {})
    T(None,
      ['someWhere', 'overthe', 'rainBow'],
      {})
    T(None,
      ['the_walrus', 'wasPaul'],
      {})
    T(None,
      ['theWalrus', 'was_paul'],
      {})
    T(None,
      ['theWalrus', 'waspaul'],
      {})


if __name__ == '__main__':
  test_case.main()
