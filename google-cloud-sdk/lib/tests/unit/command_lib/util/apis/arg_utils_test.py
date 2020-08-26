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

"""Tests for the arg_marshalling module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from apitools.base.protorpclite import messages as _messages
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.calliope import util
from tests.lib.command_lib.util.apis import base
from tests.lib.command_lib.util.apis import fake_messages as fm

import mock
import six


class ArgUtilTests(base.Base, sdk_test_base.SdkBase, parameterized.TestCase):
  """Tests for generating args for Get API calls."""

  @parameterized.parameters(
      ('string1', fm.FakeMessage.string1),
      ('enum1', fm.FakeMessage.enum1),
      ('bool1', fm.FakeMessage.bool1),
      ('int1', fm.FakeMessage.int1),
      ('float1', fm.FakeMessage.float1),
      ('message1', fm.FakeMessage.message1),
      ('message1.string2', fm.FakeMessage.InnerMessage.string2),
      ('message2', fm.FakeMessage.message2),
      ('message2.deeper_message', fm.FakeMessage.InnerMessage2.deeper_message),
      ('message2.deeper_message.deep_string',
       fm.FakeMessage.InnerMessage2.DeeperMessage.deep_string),
      ('repeated_message.string1', fm.FakeMessage.InnerMessage.string1),

  )
  def testGetFieldFromMessage(self, field_path, result):
    self.assertEqual(result,
                     arg_utils.GetFieldFromMessage(fm.FakeMessage, field_path))

  def testGetFromNamespace(self):
    ns = mock.MagicMock(foo_bar='baz', qux=None, project=None)
    value = arg_utils.GetFromNamespace(ns, 'foo-bar')
    self.assertEqual(value, 'baz')

    value = arg_utils.GetFromNamespace(ns, 'qux', fallback=lambda: 42)
    self.assertEqual(value, 42)

    properties.VALUES.core.project.Set('fake-project')
    value = arg_utils.GetFromNamespace(ns, 'project')
    self.assertEqual(value, None)

    value = arg_utils.GetFromNamespace(ns, 'project', use_defaults=True)
    self.assertEqual(value, 'fake-project')

  def testGetFieldFromMessageError(self):
    with self.assertRaises(arg_utils.UnknownFieldError):
      arg_utils.GetFieldFromMessage(fm.FakeMessage, 'string3')

  def testGetFieldValueFromMessage(self):
    m = fm.FakeMessage(
        string1='a',
        enum1=fm.FakeMessage.FakeEnum.THING_ONE,
        bool1=True,
        int1=123,
        float1=123.45,
        message1=fm.FakeMessage.InnerMessage(
            string1='b',
            ),
        message2=fm.FakeMessage.InnerMessage2(
            deeper_message=fm.FakeMessage.InnerMessage2.DeeperMessage(
                deep_string='c',
                )
            ),
        repeated_message=[
            fm.FakeMessage.InnerMessage(
                enum1=fm.FakeMessage.FakeEnum.THING_ONE),
            fm.FakeMessage.InnerMessage(
                enum1=fm.FakeMessage.FakeEnum.THING_TWO)
        ]
    )

    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'string1'),
                     m.string1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'enum1'), m.enum1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'enum2'), [])
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'bool1'), m.bool1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'int1'), m.int1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'float1'), m.float1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'bytes1'), None)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'message1'),
                     m.message1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'message1.string1'),
                     m.message1.string1)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'message2'),
                     m.message2)
    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(m, 'message2.deeper_message'),
        m.message2.deeper_message)
    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(
            m, 'message2.deeper_message.deep_string'),
        m.message2.deeper_message.deep_string)
    self.assertEqual(arg_utils.GetFieldValueFromMessage(m, 'repeated_message'),
                     m.repeated_message)
    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(m, 'repeated_message[0]'),
        m.repeated_message[0])
    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(m, 'repeated_message[0].string1'),
        m.repeated_message[0].string1)

    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(m, 'repeated_message[2]'),
        None)
    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(m, 'repeated_message[2].string1'),
        None)

    self.assertEqual(
        arg_utils.GetFieldValueFromMessage(
            fm.FakeMessage(), 'message2.deeper_message.deep_string'),
        None)

  @parameterized.parameters(
      ('invalid',
       r'Invalid field path \[invalid\] for message \[FakeMessage\]. Details: '
       r'\[Field \[invalid\] not found in message \[FakeMessage\]. Available '
       r'fields:'),
      ('string1[0]',
       r'Invalid field path \[string1\[0\]\] for message \[FakeMessage\]. '
       r'Details: \[Index cannot be specified for non-repeated field '
       r'\[string1\]\]'),
      ('enum1.string1',
       r'Invalid field path \[enum1.string1\] for message \[FakeMessage\]. '
       r'Details: \[\[enum1\] is not a valid field on field \[FakeEnum\]\]'),
      ('repeated_message.string1',
       r'Invalid field path \[repeated_message.string1\] for message '
       r'\[FakeMessage\]. Details: \[Index needs to be specified for repeated '
       r'field \[repeated_message\]\]'),
      ('repeated_message[2].string1[0]',
       r'Invalid field path \[repeated_message\[2\].string1\[0\]\] for message '
       r'\[FakeMessage\]. Details: \[Index cannot be specified for '
       r'non-repeated field \[string1\]\]'),
      ('repeated_message[2].invalid',
       r'Invalid field path \[repeated_message\[2\].invalid\] for message '
       r'\[FakeMessage\]. Details: \[Field \[invalid\] not found in message '
       r'\[InnerMessage\]. Available fields:'),
  )
  def testGetFieldValueFromMessageError(self, path, expected):
    with self.assertRaisesRegex(arg_utils.InvalidFieldPathError, expected):
      arg_utils.GetFieldValueFromMessage(fm.FakeMessage(), path)

  def testSetFieldInMessage(self):
    m = fm.FakeMessage()
    self.assertEqual(m.string1, None)

    arg_utils.SetFieldInMessage(m, 'string1', 'a')
    arg_utils.SetFieldInMessage(m, 'message1.string1', 'b')
    arg_utils.SetFieldInMessage(m, 'message1.string2', 'c')
    arg_utils.SetFieldInMessage(m, 'message2.deeper_message.deep_string', 'd')
    arg_utils.SetFieldInMessage(m, 'repeated_message.string1', 'e')
    arg_utils.SetFieldInMessage(m, 'repeated_message.string2', 'f')
    self.assertEqual(m.string1, 'a')
    self.assertEqual(m.message1.string1, 'b')
    self.assertEqual(m.message1.string2, 'c')
    self.assertEqual(m.message2.deeper_message.deep_string, 'd')
    self.assertEqual(m.repeated_message[0].string1, 'e')
    self.assertEqual(m.repeated_message[0].string2, 'f')

  @parameterized.named_parameters(
      ('InnerMessageInt',
       {'int1': 1},
       'message1',
       fm.FakeMessage(message1=fm.FakeMessage.InnerMessage(int1=1))),
      ('RepeatedMessage',
       [{'enum1': 'THING_ONE'}, {'enum1': 'THING_TWO'}],
       'repeated_message',
       fm.FakeMessage(repeated_message=[
           fm.FakeMessage.InnerMessage(enum1=fm.FakeMessage.FakeEnum.THING_ONE),
           fm.FakeMessage.InnerMessage(enum1=fm.FakeMessage.FakeEnum.THING_TWO)
       ])),
      ('InnerMessageEnum',
       {'enum1': 'THING_ONE'},
       'message1',
       fm.FakeMessage(message1=fm.FakeMessage.InnerMessage(
           enum1=fm.FakeMessage.FakeEnum.THING_ONE))),
      ('DeeperMessage',
       {'deeper_message': {'deep_string': 's'}},
       'message2',
       fm.FakeMessage(
           message2=fm.FakeMessage.InnerMessage2(
               deeper_message=fm.FakeMessage.InnerMessage2.DeeperMessage(
                   deep_string='s'))))
  )
  def testSetObjectFieldInMessage(self, obj, field, expected):
    m = fm.FakeMessage()
    arg_utils.SetFieldInMessage(m, field, obj)
    self.assertEqual(m, expected)

  @parameterized.named_parameters(
      ('Same level',
       fm.FakeMessage(int1=1),
       '',
       fm.FakeMessage(int1=1)),
      ('Field in top level message',
       fm.FakeMessage.InnerMessage(int1=1),
       'message1',
       fm.FakeMessage(message1=fm.FakeMessage.InnerMessage(int1=1))),
      ('Field in nested message',
       fm.FakeMessage.InnerMessage2.DeeperMessage(deep_string='s'),
       'message2',
       fm.FakeMessage(
           message2=fm.FakeMessage.InnerMessage2(
               deeper_message=fm.FakeMessage.InnerMessage2.DeeperMessage(
                   deep_string='s')))),
  )
  def testParseExistingMessageIntoMessage(self,
                                          existing_message,
                                          method_request_field,
                                          expected_message):
    message = fm.FakeMessage()
    method = mock.MagicMock(request_field=method_request_field)
    parsed_message = arg_utils.ParseExistingMessageIntoMessage(
        message, existing_message, method)
    self.assertEqual(parsed_message, expected_message)

  @parameterized.parameters(
      (['GOOD', 'YES'], ['GOOD', 'NO'], ['NO']),
      (['GOOD'], ['GOOD', 'EXTRA'], ['EXTRA']),
      (['GOOD', 'YES'], ['GOOD', 'YES', 'EXTRA', 'EXTRA2'], ['EXTRA, EXTRA2']),
  )
  def testValidEnumNamesErrors(self, api_names, choices, bad_choices):
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        '{} is/are not valid enum values.'.format(', '.join(bad_choices))):
      arg_utils.CheckValidEnumNames(api_names, choices)

  @parameterized.parameters(
      (['GOOD', 'YES'], ['GOOD', 'YES']),
      (['GOOD_ONE'], ['good-one']),
      (['GOOD_ONE'], ['good_one']),
      (['GOOD_ONE'], ['GOOD_ONE']),
      (['GOOD_ONE'], ['GOOD-ONE']),
  )
  def test_one_space(self, api_names, choices):
    self.assertIsNone(arg_utils.CheckValidEnumNames(api_names, choices))

  @parameterized.parameters(
      ('THING_ONE', 'thing-one'),
      ('THING-ONE', 'thing-one'),
      ('thing_one', 'thing-one'),
      ('thing-one', 'thing-one'),
  )
  def testEnumNameToChoice(self, enum_name, choice):
    self.assertEqual(choice,
                     arg_utils.EnumNameToChoice(enum_name))

  @parameterized.parameters(
      ('THING_ONE', fm.FakeMessage.FakeEnum.THING_ONE),
      ('THING-ONE', fm.FakeMessage.FakeEnum.THING_ONE),
      ('thing_one', fm.FakeMessage.FakeEnum.THING_ONE),
      ('thing-one', fm.FakeMessage.FakeEnum.THING_ONE),
      ('THING_TWO', fm.FakeMessage.FakeEnum.THING_TWO),
      ('THING-TWO', fm.FakeMessage.FakeEnum.THING_TWO),
      ('thing_two', fm.FakeMessage.FakeEnum.THING_TWO),
      ('thing-two', fm.FakeMessage.FakeEnum.THING_TWO),
      (None, None)
  )
  def testChoiceToEnum(self, choice, enum_type):
    self.assertEqual(enum_type,
                     arg_utils.ChoiceToEnum(choice, fm.FakeMessage.FakeEnum))

  def testChoiceToEnumErrors(self):
    # With valid choices specified, validate against those
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Invalid choice: badchoice. Valid choices are: \[a, b\].'):
      arg_utils.ChoiceToEnum('badchoice', fm.FakeMessage.FakeEnum,
                             valid_choices=['a', 'b'])

    # With valid choices specified, and custom item type
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Invalid sproket: badchoice. Valid choices are: \[a, b\].'):
      arg_utils.ChoiceToEnum('badchoice', fm.FakeMessage.FakeEnum,
                             item_type='sproket',
                             valid_choices=['a', 'b'])

    # With no valid choices specified, validate against the enum
    with self.assertRaisesRegex(
        arg_parsers.ArgumentTypeError,
        r'Invalid choice: badchoice. Valid choices are: \[thing-one, '
        r'thing-two\].'):
      arg_utils.ChoiceToEnum('badchoice', fm.FakeMessage.FakeEnum)

  def testConvertValueWithProcessor(self):

    def P(value):
      return '!' + value

    def Q(value):
      return ['!' + v for v in value]

    # Non-repeated.
    self.assertEqual(
        '!a',
        arg_utils.ConvertValue(fm.FakeMessage.string1, 'a', processor=P))
    # Repeated.
    self.assertEqual(
        ['!a', '!b'],
        arg_utils.ConvertValue(fm.FakeMessage.string2, ['a', 'b'], processor=Q))
    # Repeated field, but forced singular arg.
    self.assertEqual(
        ['!a'],
        arg_utils.ConvertValue(fm.FakeMessage.string2, 'a', processor=P,
                               repeated=False))

  def testConvertValueWithChoices(self):
    choices = [
        yaml_command_schema_util.Choice({'arg_value': 'a', 'enum_value': 'b'}),
        yaml_command_schema_util.Choice({'arg_value': 'c', 'enum_value': 'd'})]
    choices = yaml_command_schema_util.Choice.ToChoiceMap(choices)

    # Value not provided.
    self.assertEqual(
        None,
        arg_utils.ConvertValue(fm.FakeMessage.string1, None, choices=choices))

    # Non-repeated.
    self.assertEqual(
        'b',
        arg_utils.ConvertValue(fm.FakeMessage.string1, 'a', choices=choices))
    self.assertEqual(
        'd',
        arg_utils.ConvertValue(fm.FakeMessage.string1, 'c', choices=choices))
    # Make sure case insensitive works.
    self.assertEqual(
        'b',
        arg_utils.ConvertValue(fm.FakeMessage.string1, 'A', choices=choices))
    # Repeated.
    self.assertEqual(
        ['b', 'b', 'd', 'd'],
        arg_utils.ConvertValue(
            fm.FakeMessage.string2, ['a', 'b', 'c', 'd'], choices=choices))

    # Repeated field, but forced singular arg.
    self.assertEqual(
        ['b'],
        arg_utils.ConvertValue(
            fm.FakeMessage.string2, 'a', repeated=False, choices=choices))
    self.assertEqual(
        ['d'],
        arg_utils.ConvertValue(
            fm.FakeMessage.string2, 'c', repeated=False, choices=choices))

  def testConvertValueEnum(self):
    choices = [
        yaml_command_schema_util.Choice({'arg_value': 'a',
                                         'enum_value': 'thing-one'}),
        yaml_command_schema_util.Choice({'arg_value': 'c',
                                         'enum_value': 'thing-two'})]
    choices = yaml_command_schema_util.Choice.ToChoiceMap(choices)

    # Non-repeated.
    self.assertEqual(
        fm.FakeMessage.FakeEnum.THING_ONE,
        arg_utils.ConvertValue(fm.FakeMessage.enum1, 'a', choices=choices))
    self.assertEqual(
        fm.FakeMessage.FakeEnum.THING_TWO,
        arg_utils.ConvertValue(fm.FakeMessage.enum1, 'c', choices=choices))
    self.assertEqual(
        fm.FakeMessage.FakeEnum.THING_ONE,
        arg_utils.ConvertValue(fm.FakeMessage.enum1, 'thing-one',
                               choices=choices))
    self.assertEqual(
        fm.FakeMessage.FakeEnum.THING_TWO,
        arg_utils.ConvertValue(fm.FakeMessage.enum1, 'thing-two',
                               choices=choices))

    # Repeated.
    self.assertEqual(
        [fm.FakeMessage.FakeEnum.THING_ONE, fm.FakeMessage.FakeEnum.THING_TWO],
        arg_utils.ConvertValue(fm.FakeMessage.enum2, ['a', 'c'],
                               choices=choices))

    # Repeated field, but forced singular arg.
    self.assertEqual(
        [fm.FakeMessage.FakeEnum.THING_ONE],
        arg_utils.ConvertValue(
            fm.FakeMessage.enum2, 'a', repeated=False, choices=choices))
    self.assertEqual(
        [fm.FakeMessage.FakeEnum.THING_TWO],
        arg_utils.ConvertValue(
            fm.FakeMessage.enum2, 'c', repeated=False, choices=choices))
    self.assertEqual(
        [fm.FakeMessage.FakeEnum.THING_ONE],
        arg_utils.ConvertValue(
            fm.FakeMessage.enum2, 'thing-one', repeated=False, choices=choices))
    self.assertEqual(
        [fm.FakeMessage.FakeEnum.THING_TWO],
        arg_utils.ConvertValue(
            fm.FakeMessage.enum2, 'thing-two', repeated=False, choices=choices))

  def testHelpExtraction(self):
    help_texts = arg_utils.FieldHelpDocs(fm.FakeMessage.InnerMessage)
    self.assertEqual(
        help_texts,
        {'string1': 'the first string',
         'string2': 'The second string. It also happens to have a really long '
                    'description that wraps lines, which is convenient for '
                    'testing that capability.',
         'int1': 'an integer',
         'enum1': 'an enum',
        })

    help_texts = arg_utils.FieldHelpDocs(
        fm.FakeMessage.InnerMessage2.DeeperMessage)
    self.assertTrue(arg_utils.IsOutputField(help_texts['output_string']))
    self.assertTrue(arg_utils.IsOutputField(help_texts['output_string2']))
    self.assertFalse(arg_utils.IsOutputField(help_texts['deep_string']))

    help_texts = arg_utils.FieldHelpDocs(fm.FakeMessage.FakeEnum, 'Values')
    self.assertEqual(
        help_texts,
        {'THING_ONE': 'the first thing',
         'THING_TWO': 'the second thing'
        })

  def testGetRecursiveMessage(self):
    self.maxDiff = None  # pylint: disable=invalid-name
    message = arg_utils.GetRecursiveMessageSpec(fm.FakeMessage)
    self.assertEqual(
        message,
        {'bool1': {'description': 'a boolean', 'repeated': False,
                   'type': _messages.Variant.BOOL},
         'bytes1': {'description': 'a byte string', 'repeated': False,
                    'type': _messages.Variant.BYTES},
         'enum1': {'choices': {'THING_ONE': 'the first thing',
                               'THING_TWO': 'the second thing'},
                   'description': 'a FakeEnum', 'repeated': False,
                   'type': _messages.Variant.ENUM},
         'enum2': {'choices': {'THING_ONE': 'the first thing',
                               'THING_TWO': 'the second thing'},
                   'description': 'a repeated FakeEnum', 'repeated': True,
                   'type': _messages.Variant.ENUM},
         'float1': {'description': 'a float', 'repeated': False,
                    'type': _messages.Variant.DOUBLE},
         'int1': {'description': 'an int', 'repeated': False,
                  'type': _messages.Variant.INT64},
         'message1': {'description': 'an InnerMessage message',
                      'repeated': False,
                      'type': 'InnerMessage',
                      'fields': {
                          'string1': {
                              'description': 'the first string',
                              'repeated': False,
                              'type': _messages.Variant.STRING},
                          'string2': {
                              'description':
                                  'The second string. It also happens to have '
                                  'a really long description that wraps lines, '
                                  'which is convenient for testing that '
                                  'capability.',
                              'repeated': False,
                              'type': _messages.Variant.STRING},
                          'int1': {
                              'description': 'an integer',
                              'repeated': False,
                              'type': _messages.Variant.INT64},
                          'enum1': {
                              'choices': {'THING_ONE': 'the first thing',
                                          'THING_TWO': 'the second thing'},
                              'description': 'an enum',
                              'repeated': False,
                              'type': _messages.Variant.ENUM}}},
         'message2': {'description': 'an InnerMessage2 message',
                      'repeated': False,
                      'type': 'InnerMessage2',
                      'fields': {
                          'deeper_message': {
                              'description': 'a DeeperMessage message',
                              'repeated': False,
                              'type': 'DeeperMessage',
                              'fields': {
                                  'deep_string': {
                                      'description': 'a string',
                                      'repeated': False,
                                      'type': _messages.Variant.STRING},
                                  'output_string': {
                                      'description':
                                          '[Output Only] a string that cannot '
                                          'be set.',
                                      'repeated': False,
                                      'type': _messages.Variant.STRING},
                                  'output_string2': {
                                      'description':
                                          'another string that cannot be '
                                          'set.@OutputOnly',
                                      'repeated': False,
                                      'type': _messages.Variant.STRING}}}}},
         'repeated_message': {
             'description': 'a repeated InnerMessage message.',
             'repeated': True,
             'type': 'InnerMessage',
             'fields': {
                 'string1': {
                     'description': 'the first string',
                     'repeated': False,
                     'type': _messages.Variant.STRING},
                 'string2': {
                     'description':
                         'The second string. It also happens to have a really '
                         'long description that wraps lines, which is '
                         'convenient for testing that capability.',
                     'repeated': False,
                     'type': _messages.Variant.STRING},
                 'int1': {
                     'description': 'an integer',
                     'repeated': False,
                     'type': _messages.Variant.INT64},
                 'enum1': {
                     'choices': {'THING_ONE': 'the first thing',
                                 'THING_TWO': 'the second thing'},
                     'description': 'an enum',
                     'repeated': False,
                     'type': _messages.Variant.ENUM}}},
         'string1': {'description': 'the first string', 'repeated': False,
                     'type': _messages.Variant.STRING},
         'string2': {'description': 'a repeated string', 'repeated': True,
                     'type': _messages.Variant.STRING}})

  def _MakeKwargs(self, **kwargs):
    """Make Test keyword args to compare against arg_utils generated args."""
    k = {'category': None, 'action': 'store', 'completer': None,
         'help': 'foo help',
         'hidden': False, 'metavar': 'FOO', 'type': six.text_type,
         'choices': None, 'required': False}
    k.update(**kwargs)
    return k

  def testGenerateFlagBasics(self):
    a = yaml_command_schema.Argument('asdf', 'foo', 'foo help')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(arg.name, '--foo')
    self.assertEqual(self._MakeKwargs(), arg.kwargs)

    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a, category='ASDF')
    self.assertDictContainsSubset(self._MakeKwargs(category='ASDF'), arg.kwargs)

    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', default='junk')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(self._MakeKwargs(default='junk'), arg.kwargs)

    a = yaml_command_schema.Argument(
        'foo', 'foo', 'foo help',
        choices=[yaml_command_schema_util.Choice({'arg_value': 'a',
                                                  'enum_value': 'b'}),
                 yaml_command_schema_util.Choice({'arg_value': 'c',
                                                  'enum_value': 'd'})])
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(self._MakeKwargs(choices=['a', 'c']), arg.kwargs)

    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', completer='junk')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(self._MakeKwargs(completer='junk'), arg.kwargs)

    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', hidden=True)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(self._MakeKwargs(hidden=True), arg.kwargs)

    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', required=True)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(self._MakeKwargs(required=True), arg.kwargs)

    # No api_field
    a = yaml_command_schema.Argument(None, 'foo', 'foo help', repeated=False)
    arg = arg_utils.GenerateFlag(None, a)
    self.assertEqual(arg.kwargs['type'], None)

    # Unknown type
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help')
    with self.assertRaisesRegex(
        arg_utils.ArgumentGenerationError,
        r'Failed to generate argument for field \[message1\]: The field is of '
        r'an unknown type.'):
      arg_utils.GenerateFlag(fm.FakeMessage.message1, a)

  def testRepeated(self):
    # Repeated simple type gets wrapped.
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string2, a)
    self.assertTrue(isinstance(arg.kwargs['type'], arg_parsers.ArgList))
    self.assertEqual(arg.kwargs['type'].element_type, six.text_type)

    # Repeated complex type doesn't get re-wrapped.
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help',
                                     type=arg_parsers.ArgList())
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string2, a)
    self.assertIsNone(arg.kwargs['type'].element_type)

    # Repeated with flattened ArgDict.
    t = yaml_command_schema_util.ParseType(
        {'arg_dict': {'flatten': True, 'spec': [
            {'api_field': 'string1'}, {'api_field': 'string2'}]}})
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', type=t)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.repeated_message, a)
    result = arg.kwargs['type']('a=b,c=d')
    self.assertEqual(len(result), 2)
    self.assertEqual(result[0],
                     fm.FakeMessage.InnerMessage(string1='a', string2='b'))
    self.assertEqual(result[1],
                     fm.FakeMessage.InnerMessage(string1='c', string2='d'))

    # Repeated with ArgDict.
    t = yaml_command_schema_util.ParseType(
        {'arg_dict': {'spec': [
            {'api_field': 'string1', 'arg_name': 'a'},
            {'api_field': 'string2', 'arg_name': 'b'}]}})
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', type=t)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.repeated_message, a)
    result = arg.kwargs['type']('a=foo,b=bar')
    self.assertEqual(result,
                     fm.FakeMessage.InnerMessage(string1='foo', string2='bar'))

    # Not allowed to use ArgDict with non-repeated field.
    with self.assertRaisesRegex(
        arg_utils.ArgumentGenerationError,
        r'Failed to generate argument for field \[string1\]: The given type '
        r'can only be used on repeated fields.'):
      arg_utils.GenerateFlag(fm.FakeMessage.string1, a)

    # Force repeated arg to be singular.
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', repeated=False)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string2, a)
    self.assertEqual(arg.kwargs['type'], six.text_type)

    # Repeated with custom action is an error.
    a = yaml_command_schema.Argument('foo', 'foo', 'foo help', action='foo')
    with self.assertRaisesRegex(
        arg_utils.ArgumentGenerationError,
        r'Failed to generate argument for field \[string2\]: The field is '
        r'repeated but is using a custom action. You might want to set '
        r'repeated: False in your arg spec.'):
      arg_utils.GenerateFlag(fm.FakeMessage.string2, a)

  def testGenerateFlagBoolean(self):
    a = yaml_command_schema.Argument('asdf', 'foo', 'foo help')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.bool1, a)
    self.assertEqual(arg.name, '--foo')
    self.assertEqual(
        {'category': None, 'action': 'store_true', 'completer': None,
         'help': 'foo help', 'hidden': False, 'required': False}, arg.kwargs)

  def testGenerateUnspecifiedDefault(self):
    a = yaml_command_schema.Argument.FromData(
        {'help_text': 'foo help', 'api_field': 'asdf', 'arg_name': 'foo'})
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string2, a)
    self.assertEqual(a.default, arg_utils.UNSPECIFIED)
    self.assertNotIn('default', arg.kwargs)

  def testGenerateFlagEnumChoices(self):
    a = yaml_command_schema.Argument('asdf', 'foo', 'foo help')
    arg = arg_utils.GenerateFlag(fm.FakeMessage.enum1, a)
    self.assertEqual(arg.name, '--foo')
    self.assertEqual(
        self._MakeKwargs(choices=['thing-one', 'thing-two'],
                         type=arg_utils.EnumNameToChoice),
        arg.kwargs)

  def testGenerateFlagPositional(self):
    a = yaml_command_schema.Argument('asdf', 'foo', 'foo help',
                                     is_positional=True)
    arg = arg_utils.GenerateFlag(fm.FakeMessage.string1, a)
    self.assertEqual(arg.name, 'foo')
    kwargs = self._MakeKwargs()
    del kwargs['required']
    self.assertEqual(kwargs, arg.kwargs)

  def testParseBasicTypes(self):
    parser = util.ArgumentParser()
    def Add(field, name):
      a = yaml_command_schema.Argument('asdf', name, 'help')
      arg_utils.GenerateFlag(field, a).AddToParser(parser)

    Add(fm.FakeMessage.string1, 'string1')
    Add(fm.FakeMessage.enum1, 'enum1')
    Add(fm.FakeMessage.bool1, 'bool1')
    Add(fm.FakeMessage.int1, 'int1')
    Add(fm.FakeMessage.float1, 'float1')
    Add(fm.FakeMessage.bytes1, 'bytes1')

    result = parser.parse_args(
        ['--string1', 'foo',
         '--enum1', 'thing-one',
         '--bool1',
         '--int1', '1',
         '--float1', '1.5',
         '--bytes1', "¢συℓ∂η'т ѕαу ησ"])
    self.assertEqual(result.string1, 'foo')
    # Enums don't get converted until arg processing time.
    self.assertEqual(result.enum1, 'thing-one')
    self.assertEqual(result.bool1, True)
    self.assertEqual(result.int1, 1)
    self.assertEqual(result.float1, 1.5)
    self.assertEqual(result.bytes1,
                     b"\xc2\xa2\xcf\x83\xcf\x85\xe2\x84\x93\xe2\x88\x82\xce\xb7"
                     b"'\xd1\x82 \xd1\x95\xce\xb1\xd1\x83 \xce\xb7\xcf\x83")

  def testParseResourceIntoMessageGet(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', True))
    method = registry.GetMethod('foo.projects.locations.instances', 'get')
    message = method.GetRequestType()()
    ref = resources.REGISTRY.Parse(
        'projects/p/locations/l/instances/i',
        collection=method.request_collection.full_name)
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message)
    self.assertEqual('projects/p/locations/l/instances/i', message.name)

  def testParseResourceIntoMessageWithParams(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', False),
                         ('baz.projects.quxs.quuxs', False))
    method = registry.GetMethod('foo.projects.locations.instances', 'get')
    message = method.GetRequestType()()
    ref = resources.REGISTRY.Create(
        'baz.projects.quxs.quuxs',
        projectsId='p', quuxsId='quux', quxsId='qux')
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message,
        resource_method_params={
            'locationsId': 'quxsId',
            'instancesId': 'quuxsId'
        })
    self.assertEqual('p', message.projectsId)
    self.assertEqual('qux', message.locationsId)
    self.assertEqual('quux', message.instancesId)

  def testParseResourceIntoMessageWithParamsNonMethodParams(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', False))
    method = registry.GetMethod('foo.projects.locations.instances', 'get')
    method.params = []
    message = fm.FakeMessage()
    ref = resources.REGISTRY.Parse(
        'projects/p/locations/l/instances/i',
        collection=method.request_collection.full_name)
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message,
        resource_method_params={
            'string1': 'projectsId',
            'message1.string1': 'locationsId',
            'message1.string2': 'instancesId'
        })
    self.assertEqual('p', message.string1)
    self.assertEqual('l', message.message1.string1)
    self.assertEqual('i', message.message1.string2)

  def testParseResourceIntoMessageWithParamsNonMethodParamsRelativeName(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', False))
    method = registry.GetMethod('foo.projects.locations.instances', 'get')
    method.params = []
    message = fm.FakeMessage()
    ref = resources.REGISTRY.Parse(
        'projects/p/locations/l/instances/i',
        collection=method.request_collection.full_name)
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message,
        resource_method_params={
            'string1': '',
        })
    self.assertEqual('projects/p/locations/l/instances/i', message.string1)

  def testParseResourceIntoMessageList(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', True))
    method = registry.GetMethod('foo.projects.locations.instances', 'list')
    message = method.GetRequestType()()
    ref = resources.REGISTRY.Parse(
        'projects/p/locations/l',
        collection=method.request_collection.full_name)
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message)
    self.assertEqual('projects/p/locations/l', message.parent)

  def testParseResourceIntoMessageCreate(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', True))
    method = registry.GetMethod('foo.projects.locations.instances', 'create')
    message = method.GetRequestType()()
    message.field_by_name = mock.MagicMock()
    ref = resources.REGISTRY.Parse(
        'projects/p/locations/l/instances/i',
        collection=method.resource_argument_collection.full_name)
    arg_utils.ParseResourceIntoMessage(
        ref,
        method,
        message,
        request_id_field='name')
    self.assertEqual('projects/p/locations/l', message.parent)
    self.assertEqual('i', message.name)

  def testParseResourceIntoMessageCreateWithParentResource(self):
    self.MockCRUDMethods(('foo.projects.locations.instances', True))
    method = registry.GetMethod('foo.projects.locations.instances', 'create')
    message = method.GetRequestType()()
    parent_ref = resources.REGISTRY.Parse(
        'projects/p/locations/l',
        collection='foo.projects.locations')
    arg_utils.ParseResourceIntoMessage(parent_ref, method, message)
    self.assertEqual('projects/p/locations/l', message.parent)

  def testParseStaticFieldsIntoMessage(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'list')
    message_type = method.GetRequestType()
    message = message_type()
    static_fields = {'pageSize': 1}
    arg_utils.ParseStaticFieldsIntoMessage(message, static_fields)
    self.assertEqual(message.pageSize, 1)


class ChoiceEnumMapperTest(sdk_test_base.WithOutputCapture):
  """ChoiceEnumMapper Tests."""

  _TEST_ENUM_DICT = {
      'MY_ENUM_ONE': 1,
      'MY_ENUM_TWO': 2,
      'MY_ENUM_THREE': 3,
      'MY_ENUM_FOUR': 4
  }

  _LARGE_TEST_ENUM_DICT = {
      'ENUM_UNSPECIFIED': 0,
      'ENUM_V1_ONE': 1,
      'ENUM_V1_TWO': 2,
      'ENUM_V1_THREE': 3,
      'ENUM_V1_FOUR': 4,
      'ENUM_V1_FIVE': 5,
      'ENUM_V2_SIX': 6,
      'ENUM_V2_SEVEN': 7,
      'ENUM_V2_EIGHT': 8,
      'ENUM_V2_NINE': 9,
      'ENUM_V2_TEN': 10
  }

  def SetUp(self):
    self.parser = util.ArgumentParser()
    if six.PY2:
      my_enum_type = b'MY_ENUM'
      large_enum_type = b'LARGE_ENUM'
    else:
      my_enum_type = 'MY_ENUM'
      large_enum_type = 'LARGE_ENUM'

    self.test_enum = _messages.Enum.def_enum(self._TEST_ENUM_DICT, my_enum_type)
    self.large_enum = _messages.Enum.def_enum(self._LARGE_TEST_ENUM_DICT,
                                              large_enum_type)
    self.string_mapping = {
        x: arg_utils.EnumNameToChoice(x)
        for x in self._TEST_ENUM_DICT
    }

    self.tuple_mapping = {
        x: (x.split('_')[-1].lower(), 'Test Enum Help for {}'.format(x))
        for x in self._TEST_ENUM_DICT
    }

  def _AssertAllMappings(self, arg_name, enum_map, custom_dest=None):
    custom_dest = custom_dest or arg_name
    enum_map.choice_arg.AddToParser(self.parser)
    for choice in enum_map.choices:
      parse_result = self.parser.parse_args(['--{}'.format(arg_name), choice])
      self.assertEqual(choice, getattr(parse_result, custom_dest))

  def testDefaultMapping(self):  # Base Case #1
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, help_str='Auxilio aliis.')
    expected_choices = set(self.string_mapping.values())

    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertIsNone(mapper.custom_mappings)
    self._AssertAllMappings('test_arg', mapper)

  def testCustomMappings(self):  # Base Case #2
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, custom_mappings=self.string_mapping,
        help_str='Auxilio aliis.')
    expected_choices = set(self.string_mapping.values())

    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertEqual(mapper.custom_mappings, self.string_mapping)
    self._AssertAllMappings('test_arg', mapper)

  def testCustomMappingsWithDict(self):  # Base Case #3
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, custom_mappings=self.tuple_mapping,
        help_str='Auxilio aliis.')
    expected_choices = dict(list(self.tuple_mapping.values()))

    self.assertEqual(mapper.choices, expected_choices)
    self.assertEqual(mapper.custom_mappings, self.tuple_mapping)
    self._AssertAllMappings('test_arg', mapper)

  def testPartialCustomMappings(self):
    short_mapping = {
        'MY_ENUM_ONE': ('first', 'h1'),
        'MY_ENUM_TWO': ('second', 'h2'),
    }
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, custom_mappings=short_mapping,
        help_str='Auxilio aliis.')
    expected_choices = dict(list(short_mapping.values()))

    self.assertEqual(mapper.choices, expected_choices)
    self.assertEqual(mapper.custom_mappings, short_mapping)
    self._AssertAllMappings('test_arg', mapper)

  def testBadCustomMappingType(self):
    bad_mapping = ['foo']
    with self.assertRaisesRegex(
        TypeError,
        (r'custom_mappings must be a dict of enum string values to argparse '
         r'argument choices. Choices must be either a string or a string tuple '
         r'of \(choice, choice_help_text\)')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', self.test_enum, custom_mappings=bad_mapping,
          help_str='Auxilio aliis.')
    bad_mapping = {
        'MY_ENUM_ONE': ('one', 'h1', 'h2'),
        'MY_ENUM_TWO': ('two', 'h1', 'h2'),
        'MY_ENUM_THREE': ('three', 'h1', 'h2'),
        'MY_ENUM_FOUR': ('four', 'h1', 'h2')
    }
    with self.assertRaisesRegex(
        TypeError,
        (r'custom_mappings must be a dict of enum string values to argparse '
         r'argument choices. Choices must be either a string or a string tuple '
         r'of \(choice, choice_help_text\)')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', self.test_enum, custom_mappings=bad_mapping,
          help_str='Auxilio aliis.')

  def testBadCustomMappingValues(self):
    bad_mapping = {
        'MY_ENUM_ONE': ('one', 'h1'),
        'MY_ENUM_TWO': ('two', 'h2'),
        'MY_ENUM_THREE': ('three', 'h3'),
        'MY_ENUM_FIVE': ('five', 'h5'),
    }
    with self.assertRaisesRegex(
        ValueError, (r'custom_mappings \[.*\] may only contain mappings for '
                     r'enum values. invalid values:\[.*\]')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', self.test_enum, custom_mappings=bad_mapping,
          help_str='Auxilio aliis.')

  def testEnumFromChoiceString(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, help_str='Auxilio aliis.')
    for enum in self.test_enum:
      self.assertEqual(enum,
                       mapper.GetEnumForChoice(self.string_mapping[enum.name]))

  def testChoiceStringFromEnumValue(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, help_str='Auxilio aliis.')
    for enum_string, choice in six.iteritems(self.string_mapping):
      self.assertEqual(choice, mapper.GetChoiceForEnum(
          self.test_enum(enum_string)))

  def testBadEnum(self):
    with self.assertRaisesRegex(ValueError, (r'Invalid Message Enum: '
                                             r'\[None\]')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', None, help_str='Auxilio aliis.')
    with self.assertRaisesRegex(ValueError, (r'Invalid Message Enum: '
                                             r'\[NOT AN ENUM\]')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', 'NOT AN ENUM', help_str='Auxilio aliis.')

  def testEnumProperty(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, help_str='Auxilio aliis.')
    self.assertEqual(self.test_enum, mapper.enum)

  def testMappingProperty(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, help_str='Auxilio aliis.')
    expected_mapping = {
        y: arg_utils.ChoiceToEnum(
            x, self.test_enum) for x, y in six.iteritems(self.string_mapping)}
    self.assertEqual(expected_mapping, mapper.choice_mappings)

  def testDefaultMappingOptionalArgs(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg',
        self.test_enum,
        help_str='Custom Help',
        required=True,
        action='store',
        metavar='MY_TEST_ARG',
        dest='TEST_ARG_VAL',
        default='my-enum-three')
    expected_choices = set(self.string_mapping.values())
    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertIsNone(mapper.custom_mappings)
    self._AssertAllMappings('test_arg', mapper, custom_dest='TEST_ARG_VAL')
    with self.assertRaisesRegex(SystemExit, '0'):
      self.parser.parse_args(['-h'])
    self.AssertOutputContains(
        '--test_arg MY_TEST_ARG\nCustom Help', normalize_space=True)

  def testHidden(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg',
        self.test_enum,
        help_str='help',
        hidden=True)
    self._AssertAllMappings('test_arg', mapper)
    with self.assertRaisesRegex(SystemExit, '0'):
      self.parser.parse_args(['-h'])
    self.AssertOutputNotContains('--test_arg')

  def testFilter_IncludeList(self):
    def MyFilter(value):
      if value in ['ENUM_V1_ONE', 'ENUM_V1_TWO', 'ENUM_V1_THREE']:
        return True
      return False

    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.large_enum, help_str='Auxilio aliis.',
        include_filter=MyFilter)
    expected_choices = set(['enum-v1-one', 'enum-v1-two', 'enum-v1-three'])

    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertIsNone(mapper.custom_mappings)
    self._AssertAllMappings('test_arg', mapper)

  def testFilter_ExcludeRegex(self):
    def MyFilter(value):
      choice_re = re.compile(r'UNSPECIFIED')
      if choice_re.match(value):
        return False
      return True

    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.large_enum, help_str='Auxilio aliis.',
        include_filter=MyFilter)
    expected_choices = set([
        arg_utils.EnumNameToChoice(x)
        for x in self._LARGE_TEST_ENUM_DICT if MyFilter(x)
    ])
    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertIsNone(mapper.custom_mappings)
    self._AssertAllMappings('test_arg', mapper)

  def testFilter_IncludeRegex(self):
    def MyFilter(value):
      choice_re = re.compile(r'.*_V2_.*')
      if choice_re.match(value):
        return True
      return False

    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.large_enum, help_str='Auxilio aliis.',
        include_filter=MyFilter)
    expected_choices = set([
        arg_utils.EnumNameToChoice(x)
        for x in self._LARGE_TEST_ENUM_DICT if MyFilter(x)
    ])
    print('EXP: {}'.format(expected_choices))
    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertIsNone(mapper.custom_mappings)
    self._AssertAllMappings('test_arg', mapper)

  def testInvalidFilter(self):
    with self.assertRaisesRegex(TypeError,
                                (r'include_filter must be callable '
                                 r'received \[THIS SHOULD FAIL ROYALLY\]')):
      arg_utils.ChoiceEnumMapper(
          '--test_arg', self.test_enum, help_str='Auxilio aliis.',
          include_filter='THIS SHOULD FAIL ROYALLY')

  def testFilterCustomMappings(self):
    mapper = arg_utils.ChoiceEnumMapper(
        '--test_arg', self.test_enum, custom_mappings=self.string_mapping,
        help_str='Auxilio aliis.', include_filter=lambda x: True)
    expected_choices = set(self.string_mapping.values())

    self.assertEqual(set(mapper.choices), expected_choices)
    self.assertEqual(mapper.custom_mappings, self.string_mapping)
    self.assertEqual(mapper.filtered_enum, mapper.enum)
    self._AssertAllMappings('test_arg', mapper)


if __name__ == '__main__':
  sdk_test_base.main()
