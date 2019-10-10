# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the yaml command schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.command_lib.util.apis import fake_messages as fm

import six


class CompleterStub(object):

  def SubCompleter(self):
    pass


def CompleterGen(foo=None, bar=None):
  del foo
  del bar
  return CompleterStub


class CommandSchemaUtilTests(test_case.TestCase, parameterized.TestCase):
  """Tests of the command schema utils."""

  def testHook(self):
    self.assertIsNone(util.Hook.FromData({}, 'completer'))
    h = util.Hook.FromData(
        {'completer': CompleterStub.__module__ + ':CompleterStub'}, 'completer')
    self.assertEqual(h, CompleterStub)
    h = util.Hook.FromData(
        {'completer':
             CompleterStub.__module__ + ':CompleterStub.SubCompleter'},
        'completer')
    self.assertEqual(h, CompleterStub.SubCompleter)

    h = util.ImportPythonHook(
        CompleterStub.__module__ + ':CompleterStub')
    self.assertEqual(h.attribute, CompleterStub)
    self.assertFalse(h.kwargs)

    h = util.ImportPythonHook(
        CompleterStub.__module__ + ':CompleterGen:')
    self.assertEqual(h.attribute, CompleterGen)
    self.assertFalse(h.kwargs)
    self.assertEqual(h.GetHook(), CompleterStub)

    h = util.ImportPythonHook(
        CompleterStub.__module__ + ':CompleterGen:foo=a,bar=b')
    self.assertEqual(h.attribute, CompleterGen)
    self.assertEqual(h.kwargs, {'foo': 'a', 'bar': 'b'})
    self.assertEqual(h.GetHook(), CompleterStub)

    with self.assertRaisesRegex(util.InvalidSchemaError,
                                r'Invalid Python hook: \[foo\].'):
      util.ImportPythonHook('foo')
    with self.assertRaisesRegex(util.InvalidSchemaError,
                                r'Invalid Python hook: \[a:b:c:d\].'):
      util.ImportPythonHook('a:b:c:d')
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Invalid Python hook: \[{}:CompleterStub:asdf\]'
        r'. Args must be in the form'.format(CompleterStub.__module__)):
      util.ImportPythonHook(
          CompleterStub.__module__ + ':CompleterStub:asdf')

    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Could not import Python hook: \[foo:bar\]. Module path \[foo:bar\] '
        r'not found: No module named \'?foo\'?.'):
      util.ImportPythonHook('foo:bar')

    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r"Could not import Python hook: \[googlecloudsdk:bar\]. Module path "
        r"\[googlecloudsdk:bar\] not found: "
        r"('module' object|module 'googlecloudsdk') has no attribute 'bar'."):
      util.ImportPythonHook('googlecloudsdk:bar')

  @parameterized.parameters(
      (None, None),
      ('store', 'store'),
      ('store_true', 'store_true'),
      (CompleterStub.__module__ + ':CompleterStub', CompleterStub),
  )
  def testParseAction(self, action, output):
    self.assertEqual(util.ParseAction(action, 'foo'), output)

  def testParseActionDeprecation(self):
    result = util.ParseAction({'deprecated': {'warn': 'warn'}}, 'foo')
    self.assertTrue(issubclass(result, argparse.Action))

  @parameterized.parameters(
      (None, None),
      ('str', str),
      ('int', int),
      ('long', long if six.PY2 else int),
      ('float', float),
      ('bool', bool),
      (CompleterStub.__module__ + ':CompleterStub', CompleterStub),
  )
  def testParseType(self, t, output):
    self.assertEqual(util.ParseType(t), output)

  @parameterized.named_parameters(
      ('ArgDict', util.ArgDict.FromData),
      ('Type', lambda x: util.ParseType({'arg_dict': x})),
  )
  def testArgDict(self, loader):
    data = {'spec': [
        {'api_field': 'string1', 'arg_name': 'a'},
        {'api_field': 'enum1', 'arg_name': 'b'},
        {'api_field': 'bool1', 'arg_name': 'c'},
        {'api_field': 'int1', 'arg_name': 'd'},
        {'api_field': 'float1', 'arg_name': 'e'}
    ]}
    arg_dict = loader(data)
    dict_type = arg_dict.GenerateType(fm.FakeMessage)
    result = dict_type('a=foo,b=thing-one,c=True,d=1,e=2.0')
    self.assertEqual(
        result,
        fm.FakeMessage(string1='foo', enum1=fm.FakeMessage.FakeEnum.THING_ONE,
                       bool1=True, int1=1, float1=2.0))

  @parameterized.named_parameters(
      ('ArgDict', util.ArgDict.FromData),
      ('Type', lambda x: util.ParseType({'arg_dict': x})),
  )
  def testArgDictOptionalKeys(self, loader):
    data = {'spec': [
        {'api_field': 'string1', 'arg_name': 'a', 'required': False},
        {'api_field': 'enum1', 'arg_name': 'b', 'required': False,
         'choices': [
             {'arg_value': 'thing_one',
              'enum_value': fm.FakeMessage.FakeEnum.THING_ONE},
             {'arg_value': 'thing_two',
              'enum_value': fm.FakeMessage.FakeEnum.THING_TWO}
         ]},
        {'api_field': 'bool1', 'arg_name': 'c', 'required': False},
        {'api_field': 'int1', 'arg_name': 'd', 'required': False},
        {'api_field': 'float1', 'arg_name': 'e', 'required': False}
    ]}
    arg_dict = loader(data)
    dict_type = arg_dict.GenerateType(fm.FakeMessage)
    result = dict_type('')
    self.assertEqual(
        result,
        fm.FakeMessage(string1=None, enum1=None, bool1=None, int1=None,
                       float1=None))

  def testErrors(self):
    data = {'spec': [{'api_field': 'message1', 'arg_name': 'a'}]}
    arg_dict = util.ArgDict.FromData(data)
    with self.assertRaisesRegex(util.InvalidSchemaError,
                                'Unknown type for field: message1'):
      arg_dict.GenerateType(fm.FakeMessage)

    data['flatten'] = True
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        'Flattened ArgDicts must have exactly two items in the spec.'):
      util.ArgDict.FromData(data)

    data['spec'].append({'api_field': 'message2', 'arg_name': 'b'})
    arg_dict = util.ArgDict.FromData(data)
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        'Unknown type for field: message1'):
      arg_dict.GenerateType(fm.FakeMessage)

  @parameterized.named_parameters(
      ('ArgDict', util.ArgDict.FromData),
      ('Type', lambda x: util.ParseType({'arg_dict': x})),
  )
  def testArgDictFlattened(self, loader):
    data = {'flatten': True,
            'spec': [{'api_field': 'string1'}, {'api_field': 'string2'}]}
    arg_dict = loader(data)
    dict_type = arg_dict.GenerateType(fm.FakeMessage.InnerMessage)
    result = dict_type('a=b,c=d')
    self.assertEqual(
        result,
        [fm.FakeMessage.InnerMessage(string1='a', string2='b'),
         fm.FakeMessage.InnerMessage(string1='c', string2='d')])

  def testChoices(self):
    data = {'arg_value': 'thing-one',
            'enum_value': fm.FakeMessage.FakeEnum.THING_ONE}
    choice = util.Choice(data)
    self.assertEqual(choice.arg_value, 'thing-one')
    self.assertEqual(choice.enum_value, fm.FakeMessage.FakeEnum.THING_ONE)

  def testChoice_DefaultEnumValue(self):
    data = {'arg_value': 'thing-one'}
    choice = util.Choice(data)
    self.assertEqual(choice.arg_value, 'thing-one')
    self.assertEqual(choice.enum_value, 'THING_ONE')


if __name__ == '__main__':
  test_case.main()
