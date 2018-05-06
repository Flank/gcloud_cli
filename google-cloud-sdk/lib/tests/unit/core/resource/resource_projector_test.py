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

"""Unit tests for the resource_projector module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import datetime
import io

from apitools.base.protorpclite import messages as protorpc_message

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projection_parser
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_transform

from tests.lib import subtests
from tests.lib import test_case

import six
from six.moves import range  # pylint: disable=redefined-builtin

from google.bigtable.admin.v2 import table_pb2


class ResourceProjectionTest(test_case.Base):

  def SetUp(self):
    # self._object is mutable because some tests modify it to verify that
    # projections are copies of the input resource objects.
    self._object = {
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
        'setOfNumbers': set([456, 123, 789]),
        'nested': [
            {'x': [
                {'y': [1, 2]}, {'y': [2, 3]}],
             'z': [555]},
            {'x': [
                {'y': [4, 5]}, {'y': [5, 6]}],
             'z': [777]}],
        'blob': '{"etag": "BwVCYLHABdU="}',
        'badBlob': '{"etag: BwVCYLHABdU="}',
    }
    self.maxDiff = None

  def SameStructure(self, expression, expected, actual):
    # Roll-your-own assertSameStructure().
    expected_out = io.StringIO()
    if expression and expression.startswith('['):
      expression = '[no-pad,' + expression[1:]
    else:
      expression = '[no-pad]'
    printer_format = 'json' + expression
    resource_printer.Print(
        expected, printer_format, out=expected_out, single=True)
    actual_out = io.StringIO()
    resource_printer.Print(
        actual, printer_format, out=actual_out, single=True)
    self.assertMultiLineEqual(expected_out.getvalue(), actual_out.getvalue())

  def CheckProjection(self, expression, expected, defaults=None, resource=None,
                      resource_none=False):
    projector = resource_projector.Compile(expression, defaults=defaults)
    if resource_none:
      resource = None
    elif resource is None:
      resource = self._object
    actual = projector.Evaluate(resource)
    self.SameStructure(expression, expected, actual)

  def testDefaultProjection(self):
    self.CheckProjection('', self._object)

  def testDotProjection(self):
    self.CheckProjection('(.)', self._object)

  def testProjectWithSingleProjectionCases(self):
    self.CheckProjection('(nonExistentKey)', None)
    self.CheckProjection('(string)', {'string': 'one'})
    self.CheckProjection('(integer)', {'integer': 123})
    self.CheckProjection('(integerList.x)', None)
    self.CheckProjection('(integerList.string)', None)

    self.CheckProjection(
        '(integerList[0])',
        {'integerList': [
            0]})

    self.CheckProjection(
        '(integerList[1])',
        {'integerList': [
            None, 1]})

    self.CheckProjection(
        '(integerList[2])',
        {'integerList': [
            None, None, 2]})

    self.CheckProjection(
        '(integerList[19])',
        {'integerList': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, 19]})

    self.CheckProjection(
        '(integerList[20])',
        None)

    self.CheckProjection(
        '(integerList[-1])',
        {'integerList': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, 19]})

    self.CheckProjection(
        '(integerList[-20])',
        {'integerList': [
            0]})

    self.CheckProjection(
        '(integerList[-21])',
        None)

    # Ensures that indices that begin with "0" are treated as base-10
    # integers.
    self.CheckProjection(
        '(integerList[011])',
        {'integerList': [
            None, None, None, None, None, None, None, None, None,
            None, None, 11]})

    # Ensures that out-of-bound index accesses are handled properly.
    self.CheckProjection('(integerList[99999])', None)

    self.CheckProjection('(dict.string)', {'dict': {'string': 'one'}})
    self.CheckProjection('(dict.integer)', {'dict': {'integer': 2}})

    self.CheckProjection(
        '(listOfDicts)',
        {'listOfDicts': [
            {'string': 'one', 'hello': 'world'},
            {'string': 'two'},
            {'another': 'string', 'string': 'three'}]})

    self.CheckProjection(
        '(listOfDicts[1])',
        {'listOfDicts': [None, {'string': 'two'}]})

    self.CheckProjection(
        '(listOfDicts[2])',
        {'listOfDicts': [None, None,
                         {'string': 'three', 'another': 'string'}]})

    self.CheckProjection(
        '(listOfDicts[].nonExistentKey)', None)

    self.CheckProjection(
        '(dictOfDicts.dictOne)',
        {'dictOfDicts': {'dictOne': {'string': 'one'}}})

    self.CheckProjection(
        '(dictOfDicts.dictOne.string)',
        {'dictOfDicts': {'dictOne': {'string': 'one'}}})

    self.CheckProjection(
        '(dictOfDicts.dictTwo)',
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}}})

    self.CheckProjection(
        '(anotherListOfDicts[].keyOne)',
        {'anotherListOfDicts': [
            {'keyOne': 1}, {'keyOne': 11}, {'keyOne': 111}]})

    self.CheckProjection(
        '(listOfDicts[].hello)',
        {'listOfDicts': [{'hello': 'world'}]})

    self.CheckProjection('(listOfDicts[1].hello)', None)

    self.CheckProjection('(garbage[1].x)', None)
    self.CheckProjection('(garbage[].x)', None)

    self.CheckProjection(
        '(nested[].x[].y)',
        {'nested': [
            {'x': [{'y': [1, 2]}, {'y': [2, 3]}]},
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}]}]})

    self.CheckProjection(
        '(nested[].x[0].y)',
        {'nested': [
            {'x': [{'y': [1, 2]}]},
            {'x': [{'y': [4, 5]}]}]})

    self.CheckProjection(
        '(nested[1].x[].y)',
        {'nested': [
            None,
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}]}]})

  def testProjectMultipleProjectionCases(self):
    self.CheckProjection(
        '(integer, string)',
        {'integer': 123, 'string': 'one'})

    self.CheckProjection(
        '(string, integer, nonExistentKey)',
        {'integer': 123, 'string': 'one'})

    self.CheckProjection(
        '(dictOfDicts.dictTwo, listOfDicts[0])',
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'}]})

    self.CheckProjection(
        '(integerList[0], integerList[9], integerList[6], integerList[3])',
        {'integerList': [
            0, None, None, 3, None, None, 6, None, None, 9]})

    self.CheckProjection(
        '(integerList[0], integerList[19], integerList[6], integerList[3])',
        {'integerList': [
            0, None, None, 3, None, None, 6, None, None, None, None, None,
            None, None, None, None, None, None, None, 19]})

    self.CheckProjection(
        '(integerList[0], integerList[00019], integerList[6], integerList[3])',
        {'integerList': [
            0, None, None, 3, None, None, 6, None, None, None, None, None,
            None, None, None, None, None, None, None, 19]})

    self.CheckProjection(
        '(dictOfDicts.dictTwo, dictOfDicts.dictThree)',
        {'dictOfDicts':
         {'dictThree': {'string': 'three', 'another': 1},
          'dictTwo': {'string': 'two', 'hello': 'world'}}})

    self.CheckProjection(
        '(listOfDicts[].string, listOfDicts[0].hello)',
        {'listOfDicts': [{'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three'}]})

    self.CheckProjection(
        '(listOfDicts[].string, listOfDicts[0].hello, listOfDicts[].another)',
        {'listOfDicts': [{'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.CheckProjection(
        '(listOfDicts[1].string, listOfDicts[].string, listOfDicts[0].hello,'
        'integer, listOfDicts[0].string, listOfDicts[].another, string)',
        {'string': 'one',
         'integer': 123,
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.CheckProjection(
        '(listOfDicts[1].string, listOfDicts[].string, listOfDicts[0].hello,'
        'integer, dictOfDicts.dictOne.string, dictOfDicts.dictTwo.hello,'
        'listOfDicts[0].string, listOfDicts[].another, string)',
        {'string': 'one',
         'integer': 123,
         'dictOfDicts': {'dictTwo': {'hello': 'world'},
                         'dictOne': {'string': 'one'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

    self.CheckProjection(
        '(listOfDicts[1].string, listOfDicts[].string, listOfDicts[0].hello,'
        'integer, dictOfDicts.dictOne.string, dictOfDicts.dictTwo,'
        'dictOfDicts.dictTwo.hello, listOfDicts[0].string,'
        'listOfDicts[].another, string)',
        {'string': 'one',
         'integer': 123,
         'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'},
                         'dictOne': {'string': 'one'}},
         'listOfDicts': [{'string': 'one', 'hello': 'world'},
                         {'string': 'two'},
                         {'string': 'three', 'another': 'string'}]})

  def testProjectOrder(self):
    self.CheckProjection(
        '(listOfDicts[0])',
        {'listOfDicts': [
            {'hello': 'world',
             'string': 'one'}]})

    self.CheckProjection(
        '(listOfDicts[0].hello)',
        {'listOfDicts': [
            {'hello': 'world'}]})

    self.CheckProjection(
        '(listOfDicts[0].hello, listOfDicts[].string, integer,'
        'dictOfDicts.dictTwo, listOfDicts[].another, string)',
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}},
         'integer': 123,
         'listOfDicts': [
             {'hello': 'world'},
             {'string': 'two'},
             {'string': 'three', 'another': 'string'}],
         'string': 'one'})

    self.CheckProjection(
        '(dictOfDicts.dictTwo, integer, string, listOfDicts[0].hello,'
        'listOfDicts[].another, listOfDicts[].string)',
        {'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'}},
         'integer': 123,
         'listOfDicts': [
             {'hello': 'world'},
             {'string': 'two'},
             {'string': 'three', 'another': 'string'}],
         'string': 'one'})

    # Individual index accesses always have higher priority than slice
    # accesses for a key. The next two tests ensure that this property
    # is held.
    self.CheckProjection(
        '(anotherListOfDicts[].keyOne, anotherListOfDicts[0].keyTwo)',
        {'anotherListOfDicts': [
            {'keyTwo': 2},
            {'keyOne': 11},
            {'keyOne': 111}]})

    self.CheckProjection(
        '(anotherListOfDicts[0].keyTwo, anotherListOfDicts[].keyOne)',
        {'anotherListOfDicts': [
            {'keyTwo': 2},
            {'keyOne': 11},
            {'keyOne': 111}]})

  def testProjectCopiesResult(self):
    expected = {'string': 'one',
                'integer': 123,
                'dictOfDicts': {'dictTwo': {'string': 'two', 'hello': 'world'},
                                'dictOne': {'string': 'one'}},
                'listOfDicts': [{'string': 'one', 'hello': 'world'},
                                {'string': 'two'},
                                {'string': 'three', 'another': 'string'}]}

    projector = resource_projector.Compile(
        '('
        'listOfDicts[1].string,'
        'listOfDicts[].string,'
        'listOfDicts[0].hello,'
        'integer,'
        'dictOfDicts.dictOne.string,'
        'dictOfDicts.dictTwo,'
        'dictOfDicts.dictTwo.hello,'
        'listOfDicts[0].string,'
        'listOfDicts[].another,'
        'string'
        ')'
    )

    res = projector.Evaluate(self._object)
    self.assertEqual(res, expected)

    # Ensures that project() makes a deep copy of its result
    # before returning it to the client.
    self._object['dictOfDicts']['dictTwo'] = 'garbage'
    self._object['listOfDicts'][0] = 'garbage'
    self._object['listOfDicts'][1]['string'] = 'garbage'
    self._object['integer'] = 300
    self.assertEqual(res, expected)

  def testDoubleIndexArray(self):
    resource = {'b':
                [{'c':
                  {'d':
                   [{'e': 11}, {'e': 12}, {'f': 13}, {'f': 14}]
                  },
                 },
                 {'c':
                  {'d':
                   [{'e': 21}, {'e': 22}, {'f': 23}, {'f': 24}]
                  },
                 },
                ]
               }

    self.CheckProjection('(b[].c.d[])',
                         {'b':
                          [{'c':
                            {'d':
                             [{'e': 11}, {'e': 12}, {'f': 13}, {'f': 14}]
                            },
                           },
                           {'c':
                            {'d':
                             [{'e': 21}, {'e': 22}, {'f': 23}, {'f': 24}]
                            },
                           },
                          ]
                         },
                         resource=resource)

    self.CheckProjection('(b[].c.d[].e)',
                         {'b':
                          [{'c':
                            {'d':
                             [{'e': 11}, {'e': 12}]
                            },
                           },
                           {'c':
                            {'d':
                             [{'e': 21}, {'e': 22}]
                            },
                           },
                          ]
                         },
                         resource=resource)

    self.CheckProjection('(b[].c.d[0].e)',
                         {'b':
                          [{'c':
                            {'d':
                             [{'e': 11}]
                            },
                           },
                           {'c':
                            {'d':
                             [{'e': 21}]
                            },
                           },
                          ]
                         },
                         resource=resource)

  def testCollectionsOrderedDict(self):
    resource = collections.OrderedDict([
        ('name', 'my-instance-a{0}-0'),
        ('SelfLink', 'http://g/selfie/a-0'),
        ('networkInterfaces', [
            collections.OrderedDict([
                ('accessConfigs', [
                    collections.OrderedDict([
                        ('kind', 'compute#accessConfig'),
                        ('type', 'ONE_TO_ONE_NAT'),
                        ('name', 'External NAT'),
                        ('natIP', '74.125.239.110'),
                    ]),
                ]),
                ('networkIP', '10.240.150.0'),
                ('name', 'nic0'),
                ('network', 'default'),
            ]),

        ]),
    ])
    expected = {
        'name': 'my-instance-a{0}-0',
        'SelfLink': 'http://g/selfie/a-0',
        'networkInterfaces': [{
            'accessConfigs': [{
                'kind': 'compute#accessConfig',
                'type': 'ONE_TO_ONE_NAT',
                'name': 'External NAT',
                'natIP': '74.125.239.110',
                }],
            'networkIP': '10.240.150.0',
            'name': 'nic0',
            'network': 'default',
            }],
        }
    self.CheckProjection('', expected, resource=resource)

  def testCollectionsNamedTuple(self):

    class Scope(object):
      _SCOPE_TUPLE = collections.namedtuple('ScopeTuple',
                                            ('id', 'description'))
      INSTALLATION = _SCOPE_TUPLE(
          id='installation',
          description='The installation.')
      USER = _SCOPE_TUPLE(
          id='user',
          description='The user.')
      WORKSPACE = _SCOPE_TUPLE(
          id='workspace',
          description='The workspace.')

    resource = Scope()
    expected = {
        'INSTALLATION': {
            'id': 'installation',
            'description': 'The installation.',
            },
        'USER': {
            'id': 'user',
            'description': 'The user.',
            },
        'WORKSPACE': {
            'id': 'workspace',
            'description': 'The workspace.',
            }
        }
    self.CheckProjection('', expected, resource=resource)

  def testProtoBufMessage(self):

    resources = [table_pb2.Table(name='1'), table_pb2.Table(name='2')]
    expected = [{'name': '1'}, {'name': '2'}]
    self.CheckProjection('', expected, resource=resources)

  def testProtoRpcMessage(self):

    class TradeType(protorpc_message.Enum):
      BUY = 1
      SELL = 2
      SHORT = 3
      CALL = 4

    class Lot(protorpc_message.Message):
      price = protorpc_message.IntegerField(1, required=True)
      quantity = protorpc_message.IntegerField(2, required=True)

    class Order(protorpc_message.Message):
      symbol = protorpc_message.StringField(1, required=True)
      total_quantity = protorpc_message.IntegerField(2, required=True)
      trade_type = protorpc_message.EnumField(TradeType, 3, required=True)
      lots = protorpc_message.MessageField(Lot, 4, repeated=True)
      limit = protorpc_message.IntegerField(5)

    resource = Order(symbol='GOOG', total_quantity=10, trade_type=TradeType.BUY)
    lot1 = Lot(price=304, quantity=7)
    lot2 = Lot(price=305, quantity=3)
    resource.lots = [lot1, lot2]

    expected = {
        'lots': [
            {'price': '304', 'quantity': '7'},
            {'price': '305', 'quantity': '3'},
            ],
        'symbol': 'GOOG',
        'total_quantity': '10',
        'trade_type': 'BUY',
        }
    self.CheckProjection('', expected, resource=resource)
    self.CheckProjection('', 'BUY', resource=TradeType.BUY)

  def testSerializableCopy(self):
    resource = {'x': bytearray(b'original')}
    expected = {'x': 'original'}
    self.CheckProjection('', expected, resource=resource)

    # Changes to the original resource should not affect the projected resource.
    projector = resource_projector.Compile('')
    projected = projector.Evaluate(resource)
    x = resource['x']
    x[0] = 88  # The integer for 'X'.
    self.CheckProjection('', expected, resource=projected)

  def testPruneDefaults(self):
    defaults = resource_projection_parser.Parse('(a[1]:label=A_B)')
    resource = {'a': ['b', 'c'], 'd': 2}
    self.CheckProjection('', expected=resource, resource=resource,
                         defaults=defaults)

    expected = {'a': ['b', None]}
    self.CheckProjection('(a[0])', expected=expected, resource=resource,
                         defaults=defaults)

  def testNoneValueAll(self):
    expected = None
    self.CheckProjection('', expected, resource_none=True)

  def testNoneValueKey(self):
    expected = None
    self.CheckProjection('(a)', expected, resource_none=True)

  def testNoneValueDictAll(self):
    resource = {'a': None}
    expected = None
    self.CheckProjection('', expected, resource=resource)

  def testNoneValueDictKey(self):
    resource = {'a': None}
    expected = resource
    self.CheckProjection('(a)', expected, resource=resource)

  def testOneValueDictAll(self):
    resource = {'a': 1}
    expected = resource
    self.CheckProjection('', expected, resource=resource)

  def testOneValueDictKey(self):
    resource = {'a': 1}
    expected = resource
    self.CheckProjection('(a)', expected, resource=resource)

  def testNoneValueListAll(self):
    resource = [None]
    expected = None
    self.CheckProjection('', expected, resource=resource)

  def testNoneValueListKey(self):
    resource = [None]
    expected = None
    self.CheckProjection('([0])', expected, resource=resource)

  def testOneValueListAll(self):
    resource = [1]
    expected = resource
    self.CheckProjection('', expected, resource=resource)

  def testOneValueListKey(self):
    resource = [1]
    expected = resource
    self.CheckProjection('([0])', expected, resource=resource)

  def testProjectEmptyDict(self):
    resource = {'empty': {},
                'full': {'PASS': 1, 'FAIL': 0}}
    expected = resource
    self.CheckProjection('', expected, resource=resource)
    self.CheckProjection('(empty, full)', expected, resource=resource)

  def testTransformAll(self):
    self.CheckProjection(None, self._object)

  def testTransform(self):
    symbols = {
        'hello': lambda x: 'Hello',
        'identity': lambda x: x,
        'p2': lambda x: x ** 2,
        'p3': lambda x: x ** 3,
        'p4': lambda x: x ** 4,
        'replace': lambda x: 'list replacement',
        'upper': lambda x: x.upper(),
        'x3': lambda x: x * 3,
        'x4': lambda x: x * 4,
        }
    defaults = resource_projection_parser.Parse(
        '('
        'string.upper(),'
        'integer.p2(),'
        'dictOfDicts.dictOne.string.x4(),'
        'nonExistentKey.nonExistentKey.hello(),'
        'listOfDicts[].string.x3(),'
        'anotherListOfDicts.replace(),'
        'integerList[5].p2(),'
        'integerList[10].p3(),'
        'nested[].x[].y[].p4()'
        ')',
        symbols=symbols)

    expected = {
        'anotherListOfDicts': [
            {'keyOne': 1, 'keyThree': 3, 'keyTwo': 2},
            {'keyOne': 11, 'keyThree': 33, 'keyTwo': 22},
            {'keyOne': 111, 'keyThree': 333, 'keyTwo': 222}
        ],
        'badBlob': '{"etag: BwVCYLHABdU="}',
        'blob': '{"etag": "BwVCYLHABdU="}',
        'dict': {
            'integer': 2, 'string': 'one'
        },
        'dictOfDicts': {
            'dictOne': {'string': 'one'},
            'dictThree': {'another': 1, 'string': 'three'},
            'dictTwo': {'hello': 'world', 'string': 'two'}
        },
        'integer': 123,
        'integerList': [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19
        ],
        'listOfDicts': [
            {'hello': 'world', 'string': 'one'},
            {'string': 'two'},
            {'another': 'string', 'string': 'three'}
        ],
        'nested': [
            {'x': [{'y': [1, 2]}, {'y': [2, 3]}], 'z': [555]},
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}], 'z': [777]}
        ],
        'string': 'one',
        'setOfNumbers': [123, 456, 789],
    }
    self.CheckProjection('', expected, defaults=defaults)

    expected = {
        'anotherListOfDicts': [
            {'keyOne': 1, 'keyThree': 3, 'keyTwo': 2},
            {'keyOne': 11, 'keyThree': 33, 'keyTwo': 22},
            {'keyOne': 111, 'keyThree': 333, 'keyTwo': 222}
        ],
        'badBlob': '{"etag: BwVCYLHABdU="}',
        'blob': {
            'etag': 'BwVCYLHABdU=',
        },
        'dict': {
            'integer': 2, 'string': 'one'
        },
        'dictOfDicts': {
            'dictOne': {'string': 'one'},
            'dictThree': {'another': 1, 'string': 'three'},
            'dictTwo': {'hello': 'world', 'string': 'two'}
        },
        'integer': 123,
        'integerList': [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19
        ],
        'listOfDicts': [
            {'hello': 'world', 'string': 'one'},
            {'string': 'two'},
            {'another': 'string', 'string': 'three'}
        ],
        'nested': [
            {'x': [{'y': [1, 2]}, {'y': [2, 3]}], 'z': [555]},
            {'x': [{'y': [4, 5]}, {'y': [5, 6]}], 'z': [777]}
        ],
        'string': 'one',
        'setOfNumbers': [123, 456, 789],
    }
    self.CheckProjection('[json-decode]', expected, defaults=defaults)

    expected = {
        'string': 'ONE',
        'integer': 15129,
        'integerList': [0, 1, 2, 3, 4, 25, 6, 7, 8, 9, 1000,
                        11, 12, 13, 14, 15, 16, 17, 18, 19],
        'badBlob': '{"etag: BwVCYLHABdU="}',
        'blob': '{"etag": "BwVCYLHABdU="}',
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
             'z': [777]}],
        'setOfNumbers': [123, 456, 789],
    }
    self.CheckProjection('[transforms]', expected, defaults=defaults)

    expected = {
        'string': 'ONE',
        'integer': 15129,
        'integerList': [0, 1, 2, 3, 4, 25, 6, 7, 8, 9, 1000,
                        11, 12, 13, 14, 15, 16, 17, 18, 19],
        'badBlob': '{"etag: BwVCYLHABdU="}',
        'blob': {
            'etag': 'BwVCYLHABdU=',
        },
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
             'z': [777]}],
        'setOfNumbers': [123, 456, 789],
    }
    self.CheckProjection(
        '[json-decode,transforms]', expected, defaults=defaults)

    expected = {
        'string': 'Hello',
    }
    self.CheckProjection('(string.hello())', expected, defaults=defaults)

  def testProjectPieces(self):
    self.CheckProjection('(dictOfDicts.dictTwo)',
                         {'dictOfDicts':
                          {'dictTwo': {'string': 'two', 'hello': 'world'}}})

    self.CheckProjection('(listOfDicts[0])',
                         {'listOfDicts': [{'string': 'one', 'hello': 'world'}]})

    self.CheckProjection('(string)',
                         {'string': 'one'})

  def testProjectAndTransformPieces(self):
    symbols = {
        'hello': lambda x: 'Hello',
        'upper': lambda x: x.upper(),
        'x2': lambda x: x * 2,
        }
    defaults = resource_projection_parser.Parse(
        '('
        'dictOfDicts.dictTwo.string.x2(),'
        'listOfDicts[].string.upper(),'
        'nested.hello(),'
        'string.upper()'
        ')',
        symbols=symbols)

    self.CheckProjection('(dictOfDicts.dictTwo)',
                         {'dictOfDicts':
                          {'dictTwo': {'string': 'two', 'hello': 'world'}}},
                         defaults=defaults)
    self.CheckProjection('[transforms](dictOfDicts.dictTwo)',
                         {'dictOfDicts':
                          {'dictTwo': {'string': 'twotwo', 'hello': 'world'}}},
                         defaults=defaults)

    self.CheckProjection('(listOfDicts[0])',
                         {'listOfDicts': [{'string': 'one', 'hello': 'world'}]},
                         defaults=defaults)
    self.CheckProjection('[transforms](listOfDicts[0])',
                         {'listOfDicts': [{'string': 'ONE', 'hello': 'world'}]},
                         defaults=defaults)

    self.CheckProjection('(string)',
                         {'string': 'one'},
                         defaults=defaults)
    self.CheckProjection('[transforms](string)',
                         {'string': 'ONE'},
                         defaults=defaults)

  def testProjectAndTransformDefault(self):
    symbols = {
        'hello': lambda x: 'Hello',
        'upper': lambda x: x.upper(),
        'x2': lambda x: x * 2,
        }
    defaults = resource_projection_parser.Parse(
        '('
        'dictOfDicts.dictTwo.string.x2(),'
        'listOfDicts[].string.upper(),'
        'nested.hello(),'
        'string.upper()'
        ')',
        symbols=symbols)
    self.CheckProjection('(dictOfDicts.dictTwo, listOfDicts[0], string)',
                         {'string': 'one',
                          'listOfDicts': [
                              {'string': 'one', 'hello': 'world'}],
                          'dictOfDicts': {'dictTwo':
                                          {'string': 'two',
                                           'hello': 'world'}}},
                         defaults=defaults)

  def testProjectAndTransformExplicit(self):
    symbols = {
        'hello': lambda x: 'Hello',
        'upper': lambda x: x.upper(),
        'x2': lambda x: x * 2,
        }
    defaults = resource_projection_parser.Parse(
        '('
        'dictOfDicts.dictTwo.string.x2(),'
        'listOfDicts[].string.upper(),'
        'nested.hello(),'
        'string.upper()'
        ')',
        symbols=symbols)
    self.CheckProjection('[transforms]'
                         '(dictOfDicts.dictTwo, listOfDicts[0], string)',
                         {'string': 'ONE',
                          'listOfDicts': [
                              {'string': 'ONE', 'hello': 'world'}],
                          'dictOfDicts': {'dictTwo':
                                          {'string': 'twotwo',
                                           'hello': 'world'}}},
                         defaults=defaults)

  def testProjectAndTransformKwargs(self):

    def _Color(r, red=None, yellow=None, green=None, blue=None):
      value = six.text_type(r)
      for color, substring in (('red', red), ('yellow', yellow),
                               ('green', green), ('blue', blue)):
        if not substring:
          continue
        i = value.find(substring)
        if i < 0:
          continue
        return '{prefix}<{color}>{substring}</{color}>{suffix}'.format(
            color=color,
            prefix=value[:i],
            substring=substring,
            suffix=value[i + len(substring):])
      return value

    symbols = {
        'color': _Color,
        }
    defaults = resource_projection_parser.Parse(
        '('
        'status.color(red=ERROR, yellow=WARNING, green=OK),'
        'tests.color(ERROR, WARNING, OK)'
        ')',
        symbols=symbols)

    resource = {'status': 'All OK.',
                'tests': 'OK'}
    expected = {'status': 'All OK.',
                'tests': 'OK'}
    self.CheckProjection('(status, tests)', expected, resource=resource,
                         defaults=defaults)
    expected = {'status': 'All <green>OK</green>.',
                'tests': '<green>OK</green>'}
    self.CheckProjection('[transforms](status, tests)', expected,
                         resource=resource, defaults=defaults)

    resource = {'status': 'WARNING: What year is this?',
                'tests': 'WARNING'}
    expected = {'status': 'WARNING: What year is this?',
                'tests': 'WARNING'}
    self.CheckProjection('(status, tests)', expected, resource=resource,
                         defaults=defaults)
    expected = {'status': '<yellow>WARNING</yellow>: What year is this?',
                'tests': '<yellow>WARNING</yellow>'}
    self.CheckProjection('[transforms](status, tests)', expected,
                         resource=resource, defaults=defaults)

    resource = {'status': 'ERROR is a problem.',
                'tests': 'ERROR'}
    expected = {'status': 'ERROR is a problem.',
                'tests': 'ERROR'}
    self.CheckProjection('(status, tests)', expected, resource=resource,
                         defaults=defaults)
    expected = {'status': '<red>ERROR</red> is a problem.',
                'tests': '<red>ERROR</red>'}
    self.CheckProjection('[transforms](status, tests)', expected,
                         resource=resource, defaults=defaults)

    resource = {'status': 'OK'}
    expected = {'status': 'OK'}
    self.CheckProjection('(status, tests)', expected, resource=resource,
                         defaults=defaults)
    resource = {'status': 'OK'}
    expected = {'status': '<green>OK</green>'}
    self.CheckProjection('[transforms](status, tests)', expected,
                         resource=resource, defaults=defaults)

  def testProjectDateTimeMax(self):
    resource = {
        'MAX': datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
    }
    expected = {
        'MAX': {
            'datetime': '9999-12-31 23:59:59.999999',
            'day': 31,
            'hour': 23,
            'microsecond': 999999,
            'minute': 59,
            'month': 12,
            'second': 59,
            'year': 9999
        }
    }
    if six.PY3:
      expected['MAX']['fold'] = 0
    self.CheckProjection('(MAX)', expected, resource=resource)

  def testProjectDateTimeStart(self):
    resource = {
        'start': datetime.datetime(2015, 10, 21, 10, 11, 12, 0),
    }
    expected = {
        'start': {
            'datetime': '2015-10-21 10:11:12',
            'day': 21,
            'hour': 10,
            'microsecond': 0,
            'minute': 11,
            'month': 10,
            'second': 12,
            'year': 2015
        }
    }
    if six.PY3:
      expected['start']['fold'] = 0
    self.CheckProjection('(start)', expected, resource=resource)

  def testProjectList(self):

    resource = [4, 5, 6, 7]
    expected = [4, 5, 6, 7]
    self.CheckProjection('', expected, resource=resource)

  def testProjectIterable(self):

    class Iterator(object):

      def __init__(self, low, high):
        self.low = low
        self.high = high

      def __iter__(self):
        for i in range(self.low, self.high):
          yield i

    resource = Iterator(4, 8)
    expected = [4, 5, 6, 7]
    self.CheckProjection('', expected, resource=resource)

  def testProjectGenerator(self):

    resource = (i for i in range(4, 8))
    expected = [4, 5, 6, 7]
    self.CheckProjection('', expected, resource=resource)

  def testProjectObject(self):

    class Stooges(object):

      def __init__(self):
        self.larry = 1
        self.moe = 'Why you!'
        self.curly = ['nyuk', 'nyuk']

    class Resource(object):

      def __init__(self):
        self.stooges = Stooges()

    resource = Resource()
    expected = {
        'stooges': {
            'curly': ['nyuk', 'nyuk'],
            'larry': 1,
            'moe': 'Why you!',
        }
    }
    self.CheckProjection('(stooges)', expected, resource=resource)

  def testProjectSet(self):

    stooges = ('moe', 'larry', 'shemp', 'curly')

    class Resource(object):

      def __init__(self):
        self.stooges = set(stooges)

    projector = resource_projector.Compile('(stooges)', by_columns=True)
    self.assertEqual(set(projector.Evaluate(Resource())[0]), set(stooges))

  def testProjectEmptySet(self):

    resources = [set([])]
    self.assertEqual(resource_projector.MakeSerializable(resources), [[]])

  def testProjectNumericSet(self):

    resources = [set([3, 2, 1])]
    self.assertEqual(resource_projector.MakeSerializable(resources),
                     [[1, 2, 3]])

  def testProjectEmptyFrozenSet(self):

    resources = [frozenset([])]
    self.assertEqual(resource_projector.MakeSerializable(resources), [[]])

  def testProjectNumericFrozenSet(self):

    resources = [frozenset([3, 2, 1])]
    self.assertEqual(resource_projector.MakeSerializable(resources),
                     [[1, 2, 3]])

  def testProjectByColumns(self):
    symbols = {
        'upper': lambda x: x.upper(),
        }
    projector = resource_projector.Compile(
        '(string.upper(), integer, integerList[4])',
        defaults=resource_projection_spec.ProjectionSpec(symbols=symbols),
        by_columns=True)
    actual = projector.Evaluate(self._object)
    expected = ['ONE', 123, 4]
    self.assertEqual(expected, actual)


class ResourceProjectorAttrTest(test_case.Base):

  def testPrintDefaultsSymbols(self):

    default_symbols = {
        'fun': lambda x: 'Hello',
        'map': lambda x: x,
        }
    defaults = resource_projection_spec.ProjectionSpec(symbols=default_symbols)
    self.assertEqual(defaults.active, 0)

    symbols = {
        'iso': lambda x: 'T',
        }
    defaults = resource_projection_spec.ProjectionSpec(defaults=defaults,
                                                       symbols=symbols)
    projector = resource_projector.Compile(
        '(a.map().iso():label=Time, b.x:sort=1, c.fun().iso():align=center)',
        defaults=defaults)
    self.assertEqual(projector.Projection().active, 3)

    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, UNORDERED, 'Time', left, 3, [map().iso()])
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 1, 'X', left, None, None)
   c : (2, UNORDERED, 'C', center, 3, [fun().iso()])
""", actual)

  def testPrintDefaultsNoSymbols(self):

    symbols = {
        'iso': lambda x: 'T',
        'lower': lambda x: x.lower(),
        }
    defaults = resource_projection_parser.Parse(
        '(a:sort=2, b.x.lower():sort=1, x:sort=3, y:align=right, z:label=ZZZ)',
        symbols=symbols)
    self.assertEqual(defaults.active, 1)

    projector = resource_projector.Compile(
        '(a.iso().lower():label=Time:align=right,'
        ' b.x:label=B_X, c:align=center)',
        defaults=defaults)
    self.assertEqual(projector.Projection().active, 3)

    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 2, 'Time', right, 3, [iso().lower()])
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 1, 'B_X', left, 1, [lower()])
   c : (2, UNORDERED, 'C', center, None, None)
   x : (0, 3, 'X', left, None, None)
   y : (0, UNORDERED, 'Y', right, None, None)
   z : (0, UNORDERED, 'ZZZ', left, None, None)
""", actual)

  def testDefaultAlignments(self):

    projector = resource_projector.Compile('(a, b, c)')
    alignments = projector.Projection().Alignments()

    align = alignments[0]
    actual = align('x', 3)
    self.assertEqual(actual, 'x  ')

    align = alignments[1]
    actual = align('x', 3)
    self.assertEqual(actual, 'x  ')

    align = alignments[2]
    actual = align('x', 3)
    self.assertEqual(actual, 'x  ')

  def testAllAlignments(self):

    projector = resource_projector.Compile(
        '(a:align=left, b:align=center, c:align=right)')
    alignments = projector.Projection().Alignments()

    align = alignments[0]
    actual = align('x', 3)
    self.assertEqual(actual, 'x  ')

    align = alignments[1]
    actual = align('x', 3)
    self.assertEqual(actual, ' x ')

    align = alignments[2]
    actual = align('x', 3)
    self.assertEqual(actual, '  x')

  def testLabelsWithDefaults(self):

    defaults = resource_projection_parser.Parse(
        '(a:sort=2, b.x:sort=1, x:sort=3, y:align=right, z:label=ZZZ)')
    projector = resource_projector.Compile('(a)', defaults=defaults)
    actual = projector.Projection().Labels()
    self.assertEqual(actual, ['A'])

  def testAliasesWithDefaults(self):

    defaults = resource_projection_parser.Parse(
        '(a:sort=2, b.x:alias=bx:alias=xb:sort=1, x:sort=3, y:align=right,'
        ' z:alias=zzz:label=ZZZ)')
    projector = resource_projector.Compile('(a,bx,zzz)', defaults=defaults)
    actual = projector.Projection().Aliases()
    expected = {
        'A': ['a'],
        'bx': ['b', 'x'],
        'xb': ['b', 'x'],
        'X': ['b', 'x'],
        'Y': ['y'],
        'zzz': ['z'],
        'ZZZ': ['z'],
        }
    self.assertEqual(expected, actual)

  def testNameWithDefaults(self):

    defaults = resource_projection_parser.Parse(
        '(a:sort=2, b.x:sort=1, x:sort=3, y:align=right, z:label=ZZZ)')

    actual = defaults.Name()
    expected = None
    self.assertEqual(expected, actual)

    defaults = resource_projection_parser.Parse(
        'defaults(a:sort=2, b.x:sort=1, x:sort=3, y:align=right, z:label=ZZZ)')

    actual = defaults.Name()
    expected = 'defaults'
    self.assertEqual(expected, actual)

    projector = resource_projector.Compile('(a)', defaults=defaults)
    actual = projector.Projection().Name()
    expected = None
    self.assertEqual(expected, actual)

    projector = resource_projector.Compile('test(a)', defaults=defaults)
    actual = projector.Projection().Name()
    expected = 'test'
    self.assertEqual(expected, actual)

  def testPrintKeyAttributesBase(self):

    projector = resource_projector.Compile(
        '(a:sort=102, b.x:sort=101, x:sort=103, y:align=right, z:label=ZZZ)')
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 102, 'A', left, None, None)
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 101, 'X', left, None, None)
   x : (2, 103, 'X', left, None, None)
   y : (2, UNORDERED, 'Y', right, None, None)
   z : (2, UNORDERED, 'ZZZ', left, None, None)
""", actual)

  def testPrintKeyAttributesOnly(self):

    projector = resource_projector.Compile(
        '(a:sort=2, b.x:sort=1, x:sort=3, y:align=right, z:label=ZZZ)'
        ':(a:label=Time:align=right:sort=1, b.x:label=B_X, c:align=center)')
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 1, 'Time', right, None, None)
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 2, 'B_X', left, None, None)
   c : (0, UNORDERED, 'C', center, None, None)
   x : (2, 4, 'X', left, None, None)
   y : (2, UNORDERED, 'Y', right, None, None)
   z : (2, UNORDERED, 'ZZZ', left, None, None)
""", actual)

  def testPrintKeyAttributesOnlyUsingAliases(self):

    projector = resource_projector.Compile(
        '(a:sort=2, b.x:sort=1:label=B, x:sort=3, y:align=right,'
        ' z:label=ZZZ)'
        ':(A:label=Time:align=right:sort=1, B:label=B_X, X:align=center,'
        '  ZZZ:sort=2)'
    )
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 1, 'Time', right, None, None)
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 3, 'B_X', left, None, None)
   x : (2, 5, 'X', center, None, None)
   y : (2, UNORDERED, 'Y', right, None, None)
   z : (2, 2, 'ZZZ', left, None, None)
""", actual)

  def testPrintKeyAttributesOnlyWithAlignChange(self):

    projector = resource_projector.Compile(
        '(a:sort=2, b.x:sort=1, x:sort=3, y:align=right, z:label=ZZZ)'
        ':(a:label='':sort=1, b.x:label=B_X, c:align=center)')
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 1, '', left, None, None)
   b : (1, UNORDERED, None, left, None, None)
     x : (2, 2, 'B_X', left, None, None)
   c : (0, UNORDERED, 'C', center, None, None)
   x : (2, 4, 'X', left, None, None)
   y : (2, UNORDERED, 'Y', right, None, None)
   z : (2, UNORDERED, 'ZZZ', left, None, None)
""", actual)

  def testPrintKeyAttributesOnlyWithBooleanSet(self):

    projector = resource_projector.Compile(
        '(a, b, c, d, f)'
        ':(a:optional, b:reverse, c:optional:reverse, d:format=yaml, f:wrap)'
        ':(a:sort=1, e:sort=2)'
    )
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 1, 'A', left, None, None, [optional])
   b : (2, UNORDERED, 'B', left, None, None, [reverse])
   c : (2, UNORDERED, 'C', left, None, None, [optional|reverse])
   d : (2, UNORDERED, 'D', left, None, None, [subformat])
   e : (2, 2, 'E', left, None, None, [hidden])
   f : (2, UNORDERED, 'F', left, None, None, [wrap])
""", actual)

  def testPrintKeyAttributesWithDuplicateColumns(self):

    symbols = {
        'id': lambda x: x,
    }
    projector = resource_projector.Compile(
        '(a.id(1):label=#1:sort=102, a.id(2):label=#2:sort=101:align=right)',
        defaults=resource_projection_spec.ProjectionSpec(symbols=symbols))
    buf = io.StringIO()
    projector.Projection().Print(buf)
    actual = buf.getvalue()
    self.assertEqual("""\
   a : (2, 102, '#1', left, 2, [id(1)])
""", actual)


class ResourceProjectorMethodTest(subtests.Base):

  def RunSubTest(self, fun, expression, defaults=None, symbols=None, **kwargs):
    if symbols:
      defaults = resource_projection_spec.ProjectionSpec(defaults=defaults,
                                                         symbols=symbols)
    projector = resource_projector.Compile(expression, defaults=defaults)
    return getattr(projector.Projection(), fun)(**kwargs) if fun else None

  def testAttributes(self):

    def T(expected, expression, **kwargs):
      self.Run(expected, 'Attributes', expression, depth=2, **kwargs)

    # A format spec has 3 parts: TYPE [ATTRIBUTES] (PROJECTION). All commands
    # have a default format spec. The display format spec is determined by
    # composing the default spec and the --format flag spec (string
    # concatenation). The --format flag spec need not specify all 3 parts.
    # For example, given a default spec "table(name,value)", --format="[box]"
    # adds the "box" attribute to produce a boxed table:
    #   "table(name,value) [box]"
    # However,
    #   "table[box](name, value) json"
    # results in "json(name, value)" (the attributes are reset), because
    # attributes are TYPE specific (here TYPE table changed to json).
    # These tests cases test format spec concatenation.

    # one attribute group
    T({'box': 1, 'no-pad': 1}, '[box,no-pad](a)')
    T({'box': 1, 'no-pad': 1}, '[box,pad=2,no-pad](a)')
    T({'box': 1, 'pad': 2}, '[box,no-pad,pad=2](a)')

    # multiple attribute groups combine
    T({'box': 1, 'no-pad': 1}, '[box][no-pad](a)')
    T({'box': 1, 'no-pad': 1}, '[box] [no-pad] (a)')
    T({'box': 1, 'no-pad': 1}, '[box](a)[no-pad]')
    T({'box': 1, 'no-pad': 1}, '[box] (a) [no-pad]')

    # if old name is not None then specifying name clears previous attributes
    T({'box': 1, 'no-pad': 1}, '[box]default[no-pad](a)')
    T({'box': 1, 'no-pad': 1}, '[box]default[no-pad](a)[box]')
    T({'no-pad': 1}, 'none[box]default[no-pad](a)')
    T({'box': 1, 'no-pad': 1}, 'none[box]default[no-pad](a)[box]')
    T({'box': 1, 'no-pad': 1}, '[box] default [no-pad] (a)')
    T({'box': 1, 'no-pad': 1}, '[box] default [no-pad] (a) [box] ')
    T({'no-pad': 1}, 'none [box] default [no-pad] (a)')
    T({'box': 1, 'no-pad': 1}, 'none [box] default [no-pad] (a) [box]')

  def testLabels(self):

    def T(expected, expression, **kwargs):
      self.Run(expected, 'Labels', expression, depth=2, **kwargs)

    T(['A', 'B', 'C'], '(a, b, c)')
    T(['a', 'B b', ''], '(a:label="a", b:label="B b", c:label="")')
    T(None, '(a:label="", b:label="", c:label="")')

  def testOrder(self):

    def T(expected, expression, **kwargs):
      self.Run(expected, 'Order', expression, depth=2, **kwargs)

    T([], '(a, b, c)')
    T([(1, False), (0, True)], '(a:sort=102:reverse, b:sort=101, c)')
    T([(1, True), (0, False)], '(a:sort=102, b:sort=101:reverse)(a, b, c)')
    T([(0, False)], '(a:sort=101, b, c)')
    T([(2, False), (0, False)], '(a:sort=102, b, c:sort=101)')
    T([(1, True)], '(a, b:reverse:sort=101, c)')
    T([(2, False), (0, True), (1, True)], '(a:reverse, b:reverse, c:sort=101)')
    T([(2, True), (0, True), (1, False)],
      '(a:sort=102:reverse, b:sort=103, c:sort=101:reverse)')
    T([(0, True), (2, False), (1, False)],
      '(a:sort=102:reverse, b:sort=103, c:sort=101:reverse):'
      '(a:sort=1, c:no-reverse)')

  def testColumnCount(self):

    class _MockArgs(object):

      def __init__(self):
        self.on = True
        self.off = False

    def T(expected, expression, **kwargs):
      symbols = {
          resource_transform.GetTypeDataName('conditionals'): _MockArgs(),
      }
      symbols.update(resource_transform.GetTransforms())
      self.Run(expected, 'ColumnCount', expression, symbols=symbols,
               depth=2, **kwargs)

    T(0, '')
    T(1, '(a)')
    T(2, '(a, b)')
    T(3, '(a, b, c)')
    T(3, '(a.if((off OR on)), b.list(), c.format(":{0}:", d))')
    T(3, '(a.if(off OR on), b.list(), c.format(":{0}:", d))')
    T(2, '(a.if(off), b.if(on), c.if(on))')
    T(1, '(a.if(off), b.if(off), c.if(on))')
    T(0, '(a.if(off), b.if(off), c.if(off))')

  def testName(self):

    def T(expected, expression, **kwargs):
      self.Run(expected, 'Name', expression,
               symbols=resource_transform.GetTransforms(), **kwargs)

    T(None, '')
    T(None, '()')
    T(None, '(a)')
    T(None, '[box](a)')
    T(None, '(a)[box]')
    T('test', 'test(a)')
    T('test', '(a)test')
    T('test', 'test[box](a)')
    T('test', 'test(a)[box]')
    T('test', '(a)test[box]')
    T('test', '[box]test(a)')
    T('test', '(a)[box]test')
    T('test', 'test:(foo:sort=1)')
    T('test', 'test :(foo:sort=1)')
    T('test', 'test: (foo:sort=1)')
    T('test', 'test : (foo:sort=1)')
    T('test', 'junk test')
    T('test', '(a.if((a OR b) AND (y OR z)))test')

  def testExceptions(self):

    def T(expected, expression, **kwargs):
      self.Run(expected, None, expression,
               symbols=resource_transform.GetTransforms(),
               exception=resource_exceptions.ExpressionSyntaxError, **kwargs)

    T(None, '(')
    T(None, ')')
    T(None, '(attribute]0[)')
    T(None, '(attribute[0)')
    T(None, '(attribute[0.attributeTwo)')
    T(None, '(attribute[0[.attributeTwo)')
    T(None, '(attribute...)')
    T(None, '(..)')
    T(None, '(...)')
    T(None, '(item.oops())')
    T(None, 'item.oops()')
    T(None, '(a:align)')
    T(None, '(a:foo=bar)')
    T(None, '(a:align=unknown)')
    T(None, '(a:align)')
    T(None, '(a:alias)')
    T(None, '(a:no-alias)')
    T(None, '(a:alias=)')
    T(None, '(a:alias="")')
    T(None, '(a:reverse=1)')
    T(None, '(a.if(a, b)')
    T(None, '(a.if(x)')
    T(None, '[box,pad=2(a:align=unknown)')
    T(None, '(a.list().b)')
    T(None, '(a.list().b.list())')


class ResourceProjectionSpecCombineDefaultsTest(test_case.Base):

  def testCombineDefaultsOne(self):
    aliases_1 = {
        'foo': 'bar',
        'foo.bar': 'foobar',
        'xyzzy': 'XYZZY',
    }
    symbols_1 = {
        'hello': 'MockHello()',
        'upper': 'MockUpper()',
        'x2': 'MockSquare()',
    }
    defaults_1 = resource_projection_spec.ProjectionSpec(
        aliases=aliases_1,
        symbols=symbols_1,
    )

    expected = defaults_1

    actual = resource_projection_spec.CombineDefaults([defaults_1])

    self.assertEqual(expected.aliases, actual.aliases)
    self.assertEqual(expected.symbols, actual.symbols)

  def testCombineDefaultsWithNoAliasesOrSymbols(self):
    expected = resource_projection_spec.ProjectionSpec(aliases={}, symbols={})
    actual = resource_projection_spec.CombineDefaults([expected])

    self.assertEqual(expected.aliases, actual.aliases)
    self.assertEqual(expected.symbols, actual.symbols)

  def testCombineDefaultsWithNoneDefaultAndNoAliasesOrSymbols(self):
    expected = resource_projection_spec.ProjectionSpec(aliases={}, symbols={})
    actual = resource_projection_spec.CombineDefaults([None, expected])

    self.assertEqual(expected.aliases, actual.aliases)
    self.assertEqual(expected.symbols, actual.symbols)

  def testCombineDefaultsWithAliasesAndSymbols(self):
    aliases_1 = {
        'foo': 'bar',
        'foo.bar': 'foobar',
        'xyzzy': 'XYZZY',
    }
    symbols_1 = {
        'hello': 'MockHello()',
        'upper': 'MockUpper()',
        'x2': 'MockSquare()',
    }
    defaults_1 = resource_projection_spec.ProjectionSpec(
        aliases=aliases_1,
        symbols=symbols_1,
    )

    aliases_2 = {
        'baz': 'BAZ',
        'foo': 'foobar',
        'foo.bar': 'bar',
    }
    symbols_2 = {
        'color': 'MockColor()',
    }
    defaults_2 = resource_projection_spec.ProjectionSpec(
        aliases=aliases_2,
        symbols=symbols_2,
    )

    aliases_expected = {
        'baz': 'BAZ',
        'foo': 'foobar',
        'foo.bar': 'bar',
        'xyzzy': 'XYZZY',
    }
    symbols_expected = {
        'color': 'MockColor()',
        'hello': 'MockHello()',
        'upper': 'MockUpper()',
        'x2': 'MockSquare()',
    }
    expected = resource_projection_spec.ProjectionSpec(
        aliases=aliases_expected,
        symbols=symbols_expected,
    )

    actual = resource_projection_spec.CombineDefaults([defaults_1, defaults_2])

    self.assertEqual(expected.aliases, actual.aliases)
    self.assertEqual(expected.symbols, actual.symbols)


if __name__ == '__main__':
  test_case.main()
