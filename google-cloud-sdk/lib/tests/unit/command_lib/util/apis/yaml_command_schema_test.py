# Copyright 2017 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
import argparse
import re

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.calliope import util as calliope_util
from tests.lib.command_lib.util.apis import fake_messages as fm


class CompleterStub(object):
  pass


def ParserStub():
  pass


def ProcessorStub():
  pass


class CommandSchemaTests(sdk_test_base.SdkBase, parameterized.TestCase):
  """Tests of the command schema."""

  def testRequest(self):
    r = yaml_command_schema.Request(
        yaml_command_schema.CommandType.DESCRIBE,
        {'collection': 'foo.instances'})
    self.assertEqual(r.collection, 'foo.instances')
    self.assertEqual(r.api_version, None)
    self.assertEqual(r.method, 'get')

    r = yaml_command_schema.Request(
        yaml_command_schema.CommandType.LIST,
        {'collection': 'foo.instances',
         'api_version': 'v1'})
    self.assertEqual(r.collection, 'foo.instances')
    self.assertEqual(r.api_version, 'v1')
    self.assertEqual(r.method, 'list')

  def testRequestGeneric(self):
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        'request.method was not specified and there is no default for this '
        'command type.'):
      yaml_command_schema.Request(
          yaml_command_schema.CommandType.GENERIC,
          {'collection': 'foo.instances'})

    r = yaml_command_schema.Request(
        yaml_command_schema.CommandType.GENERIC,
        {'collection': 'foo.instances', 'method': 'custom'})
    self.assertEqual(r.collection, 'foo.instances')
    self.assertEqual(r.api_version, None)
    self.assertEqual(r.method, 'custom')

  def testResponse(self):
    r = yaml_command_schema.Response({})
    self.assertIsNone(r.error)
    r = yaml_command_schema.Response({'error': {}})
    self.assertEqual(r.error.field, 'error')
    self.assertIsNone(r.error.code)
    self.assertIsNone(r.error.message)
    r = yaml_command_schema.Response(
        {'id_field': 'name',
         'error': {'field': 'foo', 'code': 'code', 'message': 'message'},
         'result_attribute': 'asdf'})
    self.assertEqual(r.id_field, 'name')
    self.assertEqual(r.result_attribute, 'asdf')
    self.assertEqual(r.error.field, 'foo')
    self.assertEqual(r.error.code, 'code')
    self.assertEqual(r.error.message, 'message')

  def testAsyncStateField(self):
    a = yaml_command_schema.AsyncStateField({})
    self.assertEqual(a.field, 'done')
    self.assertEqual(a.success_values, [True])
    self.assertEqual(a.error_values, [])

    a = yaml_command_schema.AsyncStateField(
        {'field': 'state',
         'success_values': [True, 'yes'],
         'error_values': ['no']})
    self.assertEqual(a.field, 'state')
    self.assertEqual(a.success_values, [True, 'yes'])
    self.assertEqual(a.error_values, ['no'])

  def testAsyncErrorField(self):
    a = yaml_command_schema.AsyncErrorField({})
    self.assertEqual(a.field, 'error')

    a = yaml_command_schema.AsyncErrorField(
        {'field': 'error_message'})
    self.assertEqual(a.field, 'error_message')

  def testAsync(self):
    a = yaml_command_schema.Async({'collection': 'foo.instances'})
    self.assertEqual(a.collection, 'foo.instances')
    self.assertEqual(a.method, 'get')
    self.assertEqual(a.response_name_field, 'name')
    self.assertEqual(a.resource_get_method, 'get')
    self.assertEqual(a.state.field, 'done')
    self.assertEqual(a.error.field, 'error')

    a = yaml_command_schema.Async(
        {'collection': 'foo.instances',
         'api_version': 'v2',
         'method': 'custom',
         'response_name_field': 'selfLink',
         'resource_get_method': 'custom_resource',
         'extract_resource_result': True,
         'operation_get_method_params': {'name': 'foo'},
         'state': {'field': 'state_field'},
         'error': {'field': 'error_field'}})
    self.assertEqual(a.collection, 'foo.instances')
    self.assertEqual(a.api_version, 'v2')
    self.assertEqual(a.method, 'custom')
    self.assertEqual(a.response_name_field, 'selfLink')
    self.assertEqual(a.resource_get_method, 'custom_resource')
    self.assertEqual(a.extract_resource_result, True)
    self.assertEqual(a.operation_get_method_params, {'name': 'foo'})
    self.assertEqual(a.state.field, 'state_field')
    self.assertEqual(a.error.field, 'error_field')

  def testAsyncErrors(self):
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        'async.resource_get_method was specified but extract_resource_result is'
        ' False'):
      yaml_command_schema.Async(
          {'collection': 'foo.instances', 'extract_resource_result': False,
           'resource_get_method': 'get'})

  def testArguments(self):
    registry = resources.REGISTRY
    registry.registered_apis['foo'] = ['v1']
    zone_collection = resource_util.CollectionInfo(
        'foo', 'v1', '', '', 'projects.zones',
        'projects/{projectsId}/zones/{zonesId}',
        {'': 'projects/{projectsId}/zones/{zonesId}'},
        ['projectsId', 'zonesId'])
    # pylint:disable=protected-access
    registry._RegisterCollection(zone_collection)
    r = yaml_command_schema.Arguments({
        'resource': {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
        },
        'params': [
            {
                'help_text': 'foo-help',
                'api_field': 'foo',
                'arg_name': 'f',
            },
            {
                'help_text': 'bar-help',
                'api_field': 'bar',
                'arg_name': 'b',
                'choices': [
                    {'arg_value': 'w', 'enum_value': 'x'},
                    {'arg_value': 'y', 'enum_value': 'z'},
                ],
            },
            {
                'group': {
                    'required': True,
                    'mutex': True,
                    'params': [
                        {
                            'help_text': 'a-help',
                            'api_field': 'aaa',
                            'arg_name': 'a',
                        },
                        {
                            'help_text': 'b-help',
                            'api_field': 'bbb',
                            'arg_name': 'b',
                        },
                    ],
                },
            },
        ],
    })

    self.assertEqual(r.resource.group_help, 'group help')
    self.assertEqual(r.resource.removed_flags, ['zone'])
    spec = r.resource._GenerateResourceSpec(
        'foo.projects.zones', 'v1', ['projectsId', 'zonesId'])

    project_attr, zone_attr = spec.attributes[0], spec.attributes[1]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, concepts.ANCHOR_HELP)

    foo_flag = r.params[0]
    self.assertTrue(isinstance(foo_flag, yaml_command_schema.Argument))
    self.assertFalse(isinstance(foo_flag, yaml_command_schema.ArgumentGroup))
    self.assertEqual(foo_flag.arg_name, 'f')
    self.assertEqual(foo_flag.help_text, 'foo-help')
    self.assertEqual(foo_flag.choices, None)

    bar_flag = r.params[1]
    self.assertTrue(isinstance(bar_flag, yaml_command_schema.Argument))
    self.assertFalse(isinstance(bar_flag, yaml_command_schema.ArgumentGroup))
    self.assertEqual(bar_flag.arg_name, 'b')
    self.assertEqual(bar_flag.help_text, 'bar-help')
    self.assertEqual(bar_flag.choices[0].arg_value, 'w')
    self.assertEqual(bar_flag.choices[0].enum_value, 'x')
    self.assertEqual(bar_flag.choices[1].arg_value, 'y')
    self.assertEqual(bar_flag.choices[1].enum_value, 'z')

    group = r.params[2]
    self.assertFalse(isinstance(group, yaml_command_schema.Argument))
    self.assertTrue(isinstance(group, yaml_command_schema.ArgumentGroup))
    self.assertEqual(group.required, True)
    self.assertEqual(group.mutex, True)
    args = group.arguments
    self.assertEqual(args[0].arg_name, 'a')
    self.assertEqual(args[0].help_text, 'a-help')
    self.assertEqual(args[1].arg_name, 'b')
    self.assertEqual(args[1].help_text, 'b-help')

  def testArgument(self):
    a = yaml_command_schema.Argument.FromData(
        {'help_text': 'help', 'api_field': 'projectsId', 'arg_name': 'project'})
    self.assertEqual(a.help_text, 'help')
    self.assertEqual(a.arg_name, 'project')
    self.assertEqual(a.api_field, 'projectsId')
    self.assertEqual(a.completer, None)
    self.assertEqual(a.type, None)
    self.assertEqual(a.processor, None)
    self.assertEqual(a.required, False)
    self.assertEqual(a.hidden, False)
    self.assertEqual(a.action, None)
    self.assertEqual(a.repeated, None)

    data = {
        'api_field': 'projectsId',
        'help_text': 'help',
        'completer': ProcessorStub.__module__ + ':CompleterStub',
        'type': ProcessorStub.__module__ + ':ParserStub',
        'default': 'foo',
        'processor': ProcessorStub.__module__ + ':ProcessorStub',
        'required': True,
        'hidden': True,
        'metavar': 'FOO',
        'action': {'deprecated': {'warn': 'this is the warning'}},
        'repeated': False,
    }

    a = yaml_command_schema.Argument.FromData(data)
    self.assertEqual(a.help_text, 'help')
    self.assertEqual(a.arg_name, 'projectsId')
    self.assertEqual(a.completer, CompleterStub)
    self.assertEqual(a.type, ParserStub)
    self.assertEqual(a.default, 'foo')
    self.assertEqual(a.metavar, 'FOO')
    self.assertEqual(a.processor, ProcessorStub)
    self.assertEqual(a.required, True)
    self.assertEqual(a.hidden, True)
    self.assertTrue(issubclass(a.action, argparse.Action))
    self.assertEqual(a.repeated, False)

    a = yaml_command_schema.Argument.FromData(
        {'help_text': 'help', 'arg_name': 'project',
         'fallback': ProcessorStub.__module__ + ':ProcessorStub'})
    self.assertEqual(a.help_text, 'help')
    self.assertEqual(a.arg_name, 'project')
    self.assertEqual(a.api_field, None)
    self.assertEqual(a.completer, None)
    self.assertEqual(a.type, None)
    self.assertEqual(a.fallback, ProcessorStub)
    self.assertEqual(a.processor, None)
    self.assertEqual(a.required, False)
    self.assertEqual(a.hidden, False)
    self.assertEqual(a.action, None)
    self.assertEqual(a.repeated, None)

  @parameterized.parameters(
      ({'help_text': 'help!'}, 'at least one of [api_field, arg_name]'),
      ({'arg_name': 'arg'}, 'must have help_text'),
      ({'help_text': 'help!',
        'arg_name': 'arg',
        'default': 'default',
        'fallback': ProcessorStub.__module__ + ':ProcessorStub'},
       'at most one of [default, fallback]'),
  )
  def testArgumentErrors(self, data, message):
    with self.assertRaisesRegex(util.InvalidSchemaError, re.escape(message)):
      yaml_command_schema.Argument.FromData(data)

  @parameterized.parameters(
      ('store', 'store'),
      ('store_true', 'store_true'),
      (ProcessorStub.__module__ + ':ProcessorStub', ProcessorStub),
  )
  def testArgumentAction(self, action, result):
    a = yaml_command_schema.Argument.FromData(
        {'help_text': 'h', 'api_field': 'x', 'arg_name': 'x',
         'action': action})
    self.assertEqual(a.action, result)

  def testInput(self):
    o = yaml_command_schema.Input(yaml_command_schema.CommandType.GENERIC,
                                  {'confirmation_prompt': 'asdf'})
    self.assertEqual(o.confirmation_prompt, 'asdf')
    o = yaml_command_schema.Input(yaml_command_schema.CommandType.DELETE, {})
    self.assertTrue(o.confirmation_prompt.startswith('You are about to delete'))

  def testOutput(self):
    o = yaml_command_schema.Output({'format': 'asdf'})
    self.assertEqual(o.format, 'asdf')

  def testCommandData(self):
    c = yaml_command_schema.CommandData(
        'describe',
        {'help_text': {},
         'request': {'collection': 'foo.instances'},
         'response': {},
         'arguments': {'params': []},
         'input': {'confirmation_prompt': 'asdf'},
         'output': {'format': 'yaml'}})
    self.assertEqual(c.is_hidden, False)
    self.assertEqual(c.release_tracks, [])
    self.assertEqual(c.command_type, yaml_command_schema.CommandType.DESCRIBE)
    self.assertEqual(c.help_text, {})
    self.assertEqual(c.request.collection, 'foo.instances')
    self.assertEqual(c.response.result_attribute, None)
    self.assertEqual(c.response.error, None)
    self.assertEqual(c.async, None)
    self.assertEqual(c.arguments.params, [])
    self.assertEqual(c.input.confirmation_prompt, 'asdf')
    self.assertEqual(c.output.format, 'yaml')

    c = yaml_command_schema.CommandData(
        'describe',
        {'is_hidden': True,
         'release_tracks': ['GA', 'BETA'],
         'help_text': {},
         'request': {'collection': 'foo.instances'},
         'async': {'collection': 'operations'},
         'arguments': {'params': []},
         'output': {'format': 'yaml'}})
    self.assertEqual(c.is_hidden, True)
    self.assertEqual(
        c.release_tracks,
        [calliope_base.ReleaseTrack.GA, calliope_base.ReleaseTrack.BETA])
    self.assertEqual(c.async.method, 'get')

  def testCommandDataErrors(self):
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        'Wait commands must include an async section.'):
      yaml_command_schema.CommandData(
          'wait',
          {'help_text': {}, 'request': {'collection': 'foo.instances'}})

  def testIamData(self):
    o = yaml_command_schema.IamData({
        'message_type_overrides': {
            'policy': 'MyOtherPolicy'
        },
        'set_iam_policy_request_path':
            'setMyOtherIamPolicyRequest.myotherpolicy'
    })
    self.assertEqual(o.message_type_overrides['policy'], 'MyOtherPolicy')
    self.assertEqual(o.set_iam_policy_request_path,
                     'setMyOtherIamPolicyRequest.myotherpolicy')


class ArgGenParseTests(sdk_test_base.SdkBase, parameterized.TestCase):

  def Check(self, arg_spec, cmdline_args, api_field, field_value):
    arg = arg_spec.Generate(fm.FakeMessage)
    namespace = self._Parse([arg], cmdline_args)
    request = fm.FakeMessage()
    arg_spec.Parse(request, namespace)
    self.assertEqual(yaml_command_translator._GetAttribute(request, api_field),
                     field_value)

  def _Parse(self, args, cmdline):
    parser = calliope_util.ArgumentParser()
    for arg in args:
      arg.AddToParser(parser)
    namespace = parser.parse_args(cmdline)
    return namespace

  @parameterized.named_parameters(
      ('String', 'string1', 'foo', ['--foo=a'], 'a'),
      ('Int', 'int1', 'foo', ['--foo=1'], 1),
      ('Float', 'float1', 'foo', ['--foo=1.5'], 1.5),
      ('Bool', 'bool1', 'foo', ['--foo'], True),
      ('BoolUnspecifiedDefault', 'bool1', 'foo', [], False),
      ('Enum', 'enum1', 'foo', ['--foo=thing-one'],
       fm.FakeMessage.FakeEnum.THING_ONE),
      ('Message', 'message1.string1', 'foo', ['--foo=b'], 'b'),
      # Repeated args
      ('RepeatedStringNoValue', 'string2', 'foo', ['--foo='], []),
      ('RepeatedStringSingleValue', 'string2', 'foo', ['--foo=a'], ['a']),
      ('RepeatedStringMultiValue', 'string2', 'foo', ['--foo=a,b'], ['a', 'b']),
      ('RepeatedEnumSingleValue', 'enum2', 'foo', ['--foo=thing-one'],
       [fm.FakeMessage.FakeEnum.THING_ONE]),
      ('RepeatedEnumMultiValue', 'enum2', 'foo', ['--foo=thing-one,thing-two'],
       [fm.FakeMessage.FakeEnum.THING_ONE, fm.FakeMessage.FakeEnum.THING_TWO]),
  )
  def testArg(self, api_field, arg_name, cmdline_args, field_value):
    arg_spec = yaml_command_schema.Argument(api_field, arg_name, 'help')
    self.Check(arg_spec, cmdline_args, api_field, field_value)

  @parameterized.named_parameters(
      ('StringNoArg', 'string1', 'foo', ['--foo']),
      ('IntNoArg', 'int1', 'foo', ['--foo']),
      ('FloatNoArg', 'float1', 'foo', ['--foo']),
      ('BoolNoArg', 'bool1', 'foo', ['--foo=a']),
      ('EnumNoArg', 'enum1', 'foo', ['--foo']),
      ('MessageNoArg', 'message1.string1', 'foo', ['--foo']),
      ('IntAsString', 'int1', 'foo', ['--foo=a']),
      ('EnumBadChoice', 'enum1', 'foo', ['--foo=asdf']),
      ('RepeatedEnumBadChoice', 'enum2', 'foo', ['--foo=asdf']),
  )
  def testArgErrors(self, api_field, arg_name, cmdline_args):
    arg_spec = yaml_command_schema.Argument(api_field, arg_name, 'help')
    with self.assertRaises(SystemExit):
      self.Check(arg_spec, cmdline_args, api_field, None)

  @parameterized.named_parameters(
      ('SingleInt', 'int1', ['--foo', 'string1=a,int1=1'],
       [fm.FakeMessage.InnerMessage(string1='a', int1=1)]),
      ('MultiInt', 'int1', ['--foo', 'string1=a,int1=1',
                            '--foo', 'string1=c,int1=2'],
       [fm.FakeMessage.InnerMessage(string1='a', int1=1),
        fm.FakeMessage.InnerMessage(string1='c', int1=2)]),
      ('SingleEnum', 'enum1', ['--foo', 'string1=a,enum1=thing-one'],
       [fm.FakeMessage.InnerMessage(string1='a',
                                    enum1=fm.FakeMessage.FakeEnum.THING_ONE)]),
      ('MultiEnum', 'enum1',
       ['--foo', 'string1=a,enum1=thing-one',
        '--foo', 'string1=c,enum1=thing-two'],
       [fm.FakeMessage.InnerMessage(string1='a',
                                    enum1=fm.FakeMessage.FakeEnum.THING_ONE),
        fm.FakeMessage.InnerMessage(string1='c',
                                    enum1=fm.FakeMessage.FakeEnum.THING_TWO)]),
  )
  def testArgDict(self, second_field, cmdline_args, field_value):
    arg_spec = yaml_command_schema.Argument(
        'repeated_message', 'foo', 'help', type=util.ArgDict(
            [util.ArgDictField.FromData({'api_field': 'string1'}),
             util.ArgDictField.FromData({'api_field': second_field})]))
    self.Check(arg_spec, cmdline_args, 'repeated_message', field_value)

  @parameterized.named_parameters(
      ('SingleInt', 'int1', ['--foo', 'a=1'],
       [fm.FakeMessage.InnerMessage(string1='a', int1=1)]),
      ('MultiInt', 'int1', ['--foo', 'a=1,b=2'],
       [fm.FakeMessage.InnerMessage(string1='a', int1=1),
        fm.FakeMessage.InnerMessage(string1='b', int1=2)]),
      ('SingleEnum', 'enum1', ['--foo', 'a=thing-one'],
       [fm.FakeMessage.InnerMessage(string1='a',
                                    enum1=fm.FakeMessage.FakeEnum.THING_ONE)]),
      ('MultiEnum', 'enum1', ['--foo', 'a=thing-one,b=thing-two'],
       [fm.FakeMessage.InnerMessage(string1='a',
                                    enum1=fm.FakeMessage.FakeEnum.THING_ONE),
        fm.FakeMessage.InnerMessage(string1='b',
                                    enum1=fm.FakeMessage.FakeEnum.THING_TWO)]),
  )
  def testArgDictFlattened(self, second_field, cmdline_args, field_value):
    arg_spec = yaml_command_schema.Argument(
        'repeated_message', 'foo', 'help', type=util.FlattenedArgDict(
            util.ArgDictField.FromData({'api_field': 'string1'}),
            util.ArgDictField.FromData({'api_field': second_field})))
    self.Check(arg_spec, cmdline_args, 'repeated_message', field_value)


if __name__ == '__main__':
  sdk_test_base.main()
