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


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.apis import arg_marshalling
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib import parameterized
from tests.lib.command_lib.util.apis import yaml_command_base
import mock


class DescribeCommandTests(yaml_command_base.CommandTestsBase,
                           parameterized.TestCase):

  def Expect(self, instance='i', response=None):
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance=instance, zone='z', project='p'),
        response=response or {'foo': 'bar'},
        enable_type_checking=False)

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'describe'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.DescribeCommand))
    global_mock.assert_called_once_with(command)

  def testAdditionalArgsHook(self):
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    additional_args_mock = mock.MagicMock()
    side_effect = [calliope_base.Argument('--foo', help='Auxilio aliis.')]
    additional_args_mock.side_effect = lambda: side_effect
    d.arguments.additional_arguments_hook = additional_args_mock
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--foo')

  def testRun(self):
    self.Expect()
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')

  def testRunDeprecated(self):
    self.Expect()
    command = self.MakeCommandData()
    command['deprecate'] = {
        'is_removed': False,
        'warning': 'warning for the test'
    }
    d = yaml_command_schema.CommandData('describe', command)
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    self.AssertErrEquals('WARNING: warning for the test\n')

  def testRunDeprecatedRemoved(self):
    command = self.MakeCommandData()
    command['deprecate'] = {
        'is_removed': True,
    }
    d = yaml_command_schema.CommandData('describe', command)
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('This command has been removed.')

  def testRunWithPrompt(self):
    self.Expect()
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.input.confirmation_prompt = 'PROMPT!'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    self.WriteInput('y\n')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    self.AssertErrEquals('{"ux": "PROMPT_CONTINUE", "message": "PROMPT!"}\n')

  def testRunWithModifyRequestHooks(self):
    self.Expect(instance='iiiiiii')
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    modify_request_mock1 = mock.MagicMock()
    modify_request_mock2 = mock.MagicMock()

    def augment(unused_ref, unused_args, req):
      req.instance += 'iii'
      return req

    modify_request_mock1.side_effect = augment
    modify_request_mock2.side_effect = augment
    d.request.modify_request_hooks = [
        modify_request_mock1, modify_request_mock2
    ]

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    self.assertEqual(
        str(modify_request_mock1.call_args[0][0]),
        'https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/i'
    )
    self.assertEqual(modify_request_mock1.call_args[0][1].instance, 'i')
    self.assertEqual(
        str(modify_request_mock2.call_args[0][0]),
        'https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/i'
    )
    self.assertEqual(modify_request_mock2.call_args[0][1].instance, 'i')

  def testRunWithParseResourceFalse(self):
    self.Expect(instance=None)
    command_data = self.MakeCommandData()
    command_data['request']['parse_resource_into_request'] = False
    d = yaml_command_schema.CommandData('describe', command_data)
    modify_request_mock1 = mock.MagicMock()
    def augment(unused_ref, args, req):
      req.project = args.project
      req.zone = args.zone
      return req
    modify_request_mock1.side_effect = augment
    d.request.modify_request_hooks = [modify_request_mock1]

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')

  def testRunWithCreateRequestHook(self):
    self.Expect(instance='CHANGED')
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    create_request_mock = mock.MagicMock()
    create_request_mock.return_value = self.messages.ComputeInstancesGetRequest(
        instance='CHANGED', zone='z', project='p')
    d.request.create_request_hook = create_request_mock
    gen_mock = self.StartObjectPatch(
        arg_marshalling.DeclarativeArgumentGenerator, 'CreateRequest')

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    self.assertEqual(
        str(create_request_mock.call_args[0][0]),
        'https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/i'
    )
    self.assertEqual(create_request_mock.call_args[0][1].project, 'p')
    gen_mock.assert_not_called()

  def testRunWithIssueRequestHook(self):
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    issue_request_mock = mock.MagicMock()
    issue_request_mock.return_value = {'custom': 'response'}
    d.request.issue_request_hook = issue_request_mock
    gen_mock = self.StartObjectPatch(
        arg_marshalling.DeclarativeArgumentGenerator, 'CreateRequest')
    call_mock = self.StartObjectPatch(registry.APIMethod, 'Call')

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'custom': 'response'})
    self.AssertOutputEquals('custom: response\n')
    self.assertEqual(
        str(issue_request_mock.call_args[0][0]),
        'https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/i'
    )
    self.assertEqual(issue_request_mock.call_args[0][1].project, 'p')
    gen_mock.assert_not_called()
    call_mock.assert_not_called()

  def testRunWithResponseErrorHandler(self):
    class Good(object):
      c = 2
      d = 3

    class Error(object):
      code = 10
      message = 'message'

    class Bad(object):
      error = Error

    class Response(object):
      a = 1
      b = [Good, Bad]

    self.Expect(response=Response)
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.response = yaml_command_schema.Response(
        {'error': {'field': 'b.error',
                   'code': 'code',
                   'message': 'message'}})
    cli = self.MakeCLI(d)
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('Code: [10] Message: [message]')

  def testRunWithResponseAttribute(self):
    class Good(object):

      def __init__(self):
        self.b = 1

    class Response(object):

      def __init__(self, a):
        self.a = a

    response = Response(Good())
    self.Expect(response=response)
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.response.result_attribute = 'a'
    cli = self.MakeCLI(d)
    self.assertEqual(
        response.a,
        cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i']))

    self.Expect(response=Response(None))
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.response.result_attribute = 'a.b'
    cli = self.MakeCLI(d)
    self.assertEqual(
        None,
        cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i']))

  def testRunWithModifyResponseHooks(self):
    self.Expect()
    def get_modify_response_hook(attr_to_change, value):
      def hook(resource, unused_args):
        resource[attr_to_change] = value
        return resource
      return hook
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.response.modify_response_hooks = [get_modify_response_hook('a', 1),
                                        get_modify_response_hook('b', 2),
                                        get_modify_response_hook('a', 3),]

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar', 'a': 3, 'b': 2})

  def testRunWithModifyResponseHooks_WithArgs(self):
    self.Expect()
    def hook(resource, args):
      resource['a'] = args.project
      resource['b'] = args.zone
      return resource
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.response.modify_response_hooks = [hook]

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar', 'a': 'p', 'b': 'z'})

  def testRunWithCommandFallthroughs(self):
    self.Expect()
    data = self.MakeCommandData()
    data['arguments']['resource']['command_level_fallthroughs'] = {
        'zone': [{'arg_name': 'foo'}]}
    additional_args_mock = mock.MagicMock()
    side_effect = [calliope_base.Argument('--foo', help='Auxilio aliis.')]
    additional_args_mock.side_effect = lambda: side_effect
    d = yaml_command_schema.CommandData('describe', data)
    d.arguments.additional_arguments_hook = additional_args_mock

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--foo', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})

  def testRunWithCommandFallthroughsPositional(self):
    self.Expect()
    data = self.MakeCommandData()
    data['arguments']['resource']['command_level_fallthroughs'] = {
        'zone': [{'arg_name': 'foo', 'is_positional': True}]}
    additional_args_mock = mock.MagicMock()
    side_effect = [calliope_base.Argument('FOO', help='Auxilio aliis.')]
    additional_args_mock.side_effect = lambda: side_effect
    d = yaml_command_schema.CommandData('describe', data)
    d.arguments.additional_arguments_hook = additional_args_mock

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', 'i', 'z'])
    self.assertEqual(result, {'foo': 'bar'})

  @parameterized.named_parameters(
      ('Region', ['command', '--project', 'p', '--region', 'r', 'd'],
       'regionDisks', 'ComputeRegionDisksGetRequest', 'region', 'r'),
      ('Zone', ['command', '--project', 'p', '--zone', 'z', 'd'],
       'disks', 'ComputeDisksGetRequest', 'zone', 'z'))
  def testRunWithMultitype_ZoneOrRegion(
      self, arg_list, expected_service, expected_request_type,
      expected_field_name, expected_field_value):
    expected_msg = getattr(self.messages, expected_request_type)(
        disk='d', project='p', **{expected_field_name: expected_field_value})
    service = getattr(self.mocked_client, expected_service)
    service.Get.Expect(
        expected_msg, response={'foo': 'bar'}, enable_type_checking=False)

    # Set up the multitype resource - a regional or zonal disk.
    command_data = self.MakeCommandData(collection='compute.disks')
    command_data['request']['parse_resource_into_request'] = False
    attrs = {
        parameter: {'parameter_name': parameter, 'attribute_name': parameter,
                    'help': 'help'}
        for parameter in ['project', 'zone', 'region', 'disk']}
    sub_resources = [
        {'name': 'disk',
         'collection': 'compute.disks',
         'attributes': [attrs['project'], attrs['zone'], attrs['disk']]},
        {'name': 'disk',
         'collection': 'compute.regionDisks',
         'attributes': [attrs['project'], attrs['region'], attrs['disk']]}]
    command_data['arguments']['resource'] = {
        'arg_name': 'disk',
        'help_text': 'group help',
        'spec': {'name': 'disk', 'resources': sub_resources}}
    d = yaml_command_schema.CommandData('describe', command_data)

    # Set up the issue request hook (similar to what would be used in real
    # life, chooses service/request type based on result of parsing.)
    def request(ref, args):
      disk = args.CONCEPTS.disk.Parse()
      if disk.type_.name == 'compute.disks':
        service = self.mocked_client.disks
        req = self.messages.ComputeDisksGetRequest()
        req.zone = ref.zone
      else:
        service = self.mocked_client.regionDisks
        req = self.messages.ComputeRegionDisksGetRequest()
        req.region = ref.region
      req.disk = ref.Name()
      req.project = ref.project
      return service.Get(req)
    issue_request_mock = mock.MagicMock()
    d.request.issue_request_hook = issue_request_mock
    issue_request_mock.side_effect = request

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'DISK', '--zone', '--region')
    result = cli.Execute(arg_list)
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')


class DescribeComplexObjectCommandTests(yaml_command_base.CommandTestsBase,
                                        parameterized.TestCase):

  def Expect(self, instance='i', response=None):
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance=instance, zone='z', project='p'),
        response=response or {'foo': [{'bar': {'key': 'value1'}},
                                      {'bar': {'key': 'value2'}},
                                      {'bar': {'key': 'value3'}}]},
        enable_type_checking=False)

  def testRunWithDefaultFlatten(self):
    # Command with default flattener should run the flattener on the output
    self.Expect()
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.output.flatten = ['foo[].bar']
    cli = self.MakeCLI(d)
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals(
        """
---
key: value1
---
key: value2
---
key: value3
""".lstrip('\n'))

  def testRunWithDefaultAndFlagFlatten(self):
    # Command with default flattener should use the flattener specified via flag
    self.Expect()
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.output.flatten = ['foo[].bar']
    cli = self.MakeCLI(d)
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i',
                 "--flatten=['foo']"])
    self.AssertOutputEquals(
        """
---
foo:
  bar:
    key: value1
---
foo:
  bar:
    key: value2
---
foo:
  bar:
    key: value3
""".lstrip('\n'))

  def testRunWithFlattenAndFormat(self):
    # Check flattener applied with format
    self.Expect()
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.output.flatten = ['foo[].bar']
    d.output.format = 'table(key)'
    cli = self.MakeCLI(d)
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals(
        """
KEY
value1
value2
value3
""".lstrip('\n'))
