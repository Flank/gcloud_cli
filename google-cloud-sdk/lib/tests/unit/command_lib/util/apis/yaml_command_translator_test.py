# -*- coding: utf-8 -*- #
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

"""Tests for the yaml command translator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import encoding
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope_cli
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.util.apis import arg_marshalling
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.command_lib.util.apis import base

import mock
from six.moves import range  # pylint: disable=redefined-builtin


class CommandBuilderTests(base.Base):
  """Tests of the command builder."""

  def SetUp(self):
    self.MockCRUDMethods(('foo.instances', False), ('foo.zones', False))

  def MakeCommandData(self, collection='foo.instances'):
    data = {
        'help_text': {'brief': 'brief help'},
        'request': {'collection': collection},
        'arguments': {
            'resource': {
                'help_text': 'help',
                'spec': {'name': 'instance', 'collection': 'foo.instances',
                         'attributes': [
                             {'parameter_name': 'instancesId',
                              'attribute_name': 'instance',
                              'help': 'the instance'}]}}}
    }
    return data

  def testDefaultGlobalAttributes(self):
    cb = yaml_command_translator.CommandBuilder(
        yaml_command_schema.CommandData('describe', self.MakeCommandData()),
        ['abc', 'xyz', 'describe'])

    class TempCommand(calliope_base.Command):
      pass

    cb._ConfigureGlobalAttributes(TempCommand)
    self.assertEqual(TempCommand.IsHidden(), False)
    self.assertEqual(TempCommand.ValidReleaseTracks(), None)
    self.assertEqual(
        TempCommand.detailed_help,
        {'brief': 'brief help',
         'API REFERENCE': 'This command uses the *foo/v1* API. The full '
                          'documentation for this API can be found at: '
                          'https://cloud.google.com/docs'})

  def testGlobalAttributes(self):
    d = yaml_command_schema.CommandData('describe', self.MakeCommandData())
    d.is_hidden = True
    d.release_tracks = [calliope_base.ReleaseTrack.GA,
                        calliope_base.ReleaseTrack.BETA]
    cb = yaml_command_translator.CommandBuilder(d, ['abc', 'xyz', 'describe'])

    class TempCommand(calliope_base.Command):
      pass

    cb._ConfigureGlobalAttributes(TempCommand)
    self.assertEqual(TempCommand.IsHidden(), True)
    self.assertEqual(
        TempCommand.ValidReleaseTracks(),
        {calliope_base.ReleaseTrack.GA, calliope_base.ReleaseTrack.BETA})
    self.assertEqual(
        TempCommand.detailed_help,
        {'brief': 'brief help',
         'API REFERENCE': 'This command uses the *foo/v1* API. The full '
                          'documentation for this API can be found at: '
                          'https://cloud.google.com/docs'})

  def testUnknownCommandType(self):
    cb = yaml_command_translator.CommandBuilder(
        yaml_command_schema.CommandData('describe', self.MakeCommandData()),
        ['abc', 'xyz', 'describe'])
    cb.spec.command_type = 'bogus'
    with self.assertRaisesRegex(
        ValueError,
        r'Command \[abc xyz describe] unknown command type \[bogus]\.'):
      cb.Generate()


class MockTranslator(command_loading.YamlCommandTranslator):
  """A sub that lets us run the generator without having to write command files.
  """

  def __init__(self, spec, name='describe'):
    self.spec = spec
    self.name = name

  def Translate(self, path, command_data):
    return yaml_command_translator.CommandBuilder(
        self.spec, ['abc', 'xyz', self.name]).Generate()


class CommandTestsBase(sdk_test_base.WithFakeAuth,
                       sdk_test_base.WithOutputCapture, test_case.WithInput):

  def SetUp(self):
    self.StartObjectPatch(time, 'sleep')
    client = apis.GetClientClass('compute', 'v1')
    self.mocked_client = apitools_mock.Client(client)
    self.messages = client.MESSAGES_MODULE
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    functions_client = apis.GetClientClass('cloudfunctions', 'v1')
    self.mocked_functions_client = apitools_mock.Client(functions_client)
    self.functions_messages = functions_client.MESSAGES_MODULE
    self.mocked_functions_client.Mock()
    self.addCleanup(self.mocked_functions_client.Unmock)

  def TearDown(self):
    # Wait for the ProgressTracker ticker thread to end.
    self.JoinAllThreads(timeout=2)

  def MakeCommandData(self,
                      collection='compute.instances',
                      is_create=False,
                      is_list=False,
                      is_async=None,
                      brief=None,
                      description=None):
    if is_list:
      spec = {'name': 'zone', 'collection': 'compute.zones', 'attributes': [
          {'parameter_name': 'zone',
           'attribute_name': 'zone',
           'help': 'the zone'}]}
    else:
      spec = {'name': 'instance', 'collection': 'compute.instances',
              'request_id_field': 'instance.name', 'attributes': [
                  {'parameter_name': 'zone',
                   'attribute_name': 'zone',
                   'help': 'the zone'},
                  {'parameter_name': 'instance',
                   'attribute_name': 'instance',
                   'help': 'the instance'}]}
    data = {
        'help_text': {
            'brief': brief or 'brief help'
        },
        'request': {
            'collection': collection
        },
        'arguments': {
            'resource': {
                'help_text': 'help',
                'spec': spec
            }
        }
    }
    if is_async:
      data['async'] = {
          'collection':
          '.'.join(collection.split('.')[:-1]) + '.zoneOperations'}
    return data

  @classmethod
  def _GetIoTSpec(cls):
    return {
        'name':
            'registry',
        'collection':
            'cloudiot.projects.locations.registries',
        'attributes': [
            {
                'parameter_name': 'locationsId',
                'attribute_name': 'region',
                'help': 'The name of the Cloud IoT region.',
            },
            {
                'parameter_name': 'registriesId',
                'attribute_name': 'registry',
                'help': 'The name of the Cloud IoT registry.',
            },
        ],
    }

  @classmethod
  def _GetMLSpec(cls):
    return {
        'name':
            'model',
        'collection':
            'ml.projects.models',
        'attributes': [{
            'parameter_name': 'projectsId',
            'attribute_name': 'project',
            'help': 'The name of the Project.',
        }, {
            'parameter_name': 'modelsId',
            'attribute_name': 'model',
            'help': 'The name of the Model.',
        }],
    }

  @classmethod
  def MakeIAMCommandData(cls,
                         help_text,
                         brief=None,
                         description=None,
                         notes=None,
                         params=None,
                         another_collection=False):
    spec = cls._GetIoTSpec()
    collection = 'cloudiot.projects.locations.registries'
    if another_collection:
      collection = 'ml.projects.models'
      spec = cls._GetMLSpec()
    data = {
        'help_text': {
            'brief': brief or '<brief>',
            'DESCRIPTION': description or '<DESCRIPTION>',
            'NOTES': notes,
        },
        'request': {
            'collection': collection,
        },
        'arguments': {
            'resource': {
                'help_text': 'The {resource} for which ' + help_text,
                'spec': spec,
            },
        },
    }
    if params is not None:
      data['arguments']['params'] = params

    return data

  def MakeCLI(self, spec, name='describe'):
    """Creates a  CLI with one command that implements the given spec."""
    test_cli_dir = self.Resource('tests', 'unit', 'command_lib', 'util', 'apis',
                                 'testdata', 'sdk1')
    loader = calliope_cli.CLILoader(
        name='gcloud',
        command_root_directory=test_cli_dir,
        allow_non_existing_modules=True,
        yaml_command_translator=MockTranslator(spec, name=name))
    return loader.Generate()

  def OperationResponses(self):
    running_response = self.messages.Operation(
        id=12345, name='operation-12345',
        selfLink='https://www.googleapis.com/compute/v1/projects/p/zones/z/'
                 'operations/operation-12345',
        error=None,
        status=self.messages.Operation.StatusValueValuesEnum.RUNNING)
    done_response = self.messages.Operation(
        id=12345, name='operation-12345',
        selfLink='https://www.googleapis.com/compute/v1/projects/p'
                 '/zones/z/operations/operation-12345',
        error=None,
        status=self.messages.Operation.StatusValueValuesEnum.DONE)
    return running_response, done_response

  def ExpectOperation(self):
    running_response, done_response = self.OperationResponses()
    self.mocked_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-12345', project='p', zone='z'),
        response=running_response)
    self.mocked_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-12345', project='p', zone='z'),
        response=done_response)

  def AssertArgs(self, cli, *args):
    positionals = {a for a in args if not a.startswith('-')}
    flags = {a for a in args if a.startswith('-')}
    # These are just always here so check for them automatically.
    flags.add('--document')
    flags.add('--help')
    flags.add('-h')

    c = cli.top_element.LoadSubElement('command')
    actual_positionals = {a.metavar for a in c.ai.positional_args}
    actual_flags = {a.option_strings[0] for a in c.ai.flag_args}
    self.assertEqual(actual_positionals, positionals)
    self.assertEqual(actual_flags, flags)

  def AssertErrorHandlingWithResponse(self,
                                      expect_func,
                                      command_data,
                                      execute_params=None):

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

    expect_func(response=Response)
    command_data.response = yaml_command_schema.Response({
        'error': {
            'field': 'b.error',
            'code': 'code',
            'message': 'message'
        }
    })
    cli = self.MakeCLI(command_data)
    with self.assertRaises(SystemExit):
      cli.Execute(execute_params or [])
    self.AssertErrContains('Code: [10] Message: [message]')


class DescribeCommandTests(CommandTestsBase,
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
    d.request.modify_request_hooks = [modify_request_mock1,
                                      modify_request_mock2]

    cli = self.MakeCLI(d)
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    self.assertEqual(
        str(modify_request_mock1.call_args[0][0]),
        'https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/i')
    self.assertEqual(modify_request_mock1.call_args[0][1].instance, 'i')
    self.assertEqual(
        str(modify_request_mock2.call_args[0][0]),
        'https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/i')
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
        'https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/i')
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
        'https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/i')
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

  @parameterized.named_parameters(
      ('WithExtra',
       ['command', '--project', 'p', '--location', 'l', '--registry', 'r',
        '--group', 'g', 'd'],
       'projects_locations_registries_groups_devices',
       'CloudiotProjectsLocationsRegistriesGroupsDevicesGetRequest',
       'projects/p/locations/l/registries/r/groups/g/devices/d'),
      ('NoExtra',
       ['command', '--project', 'p', '--location', 'l', '--registry', 'r', 'd'],
       'projects_locations_registries_devices',
       'CloudiotProjectsLocationsRegistriesDevicesGetRequest',
       'projects/p/locations/l/registries/r/devices/d'))
  def testRunWithMultitype_ExtraAttribute(
      self, arg_list, expected_service, expected_request_type,
      expected_name):
    iot_client = apis.GetClientClass('cloudiot', 'v1')
    mocked_iot_client = apitools_mock.Client(iot_client)
    iot_messages = iot_client.MESSAGES_MODULE
    mocked_iot_client.Mock()
    self.addCleanup(mocked_iot_client.Unmock)

    expected_msg = getattr(iot_messages, expected_request_type)(
        name=expected_name)
    service = getattr(mocked_iot_client, expected_service)
    service.Get.Expect(
        expected_msg, response={'foo': 'bar'}, enable_type_checking=False)

    # Set up the multitype resource - a device with or without a group.
    command_data = self.MakeCommandData(
        collection='cloudiot.projects.locations.registries.devices')
    command_data['request']['parse_resource_into_request'] = False
    project_attr = {
        'parameter_name': 'projectsId', 'attribute_name': 'project',
        'help': 'help'}
    location_attr = {
        'parameter_name': 'locationsId', 'attribute_name': 'location',
        'help': 'help'}
    registry_attr = {
        'parameter_name': 'registriesId', 'attribute_name': 'registry',
        'help': 'help'}
    group_attr = {
        'parameter_name': 'groupsId', 'attribute_name': 'group',
        'help': 'help'}
    device_attr = {
        'parameter_name': 'devicesId', 'attribute_name': 'device',
        'help': 'help'}
    sub_resources = [
        {'name': 'device',
         'collection': 'cloudiot.projects.locations.registries.devices',
         'attributes': [project_attr, location_attr, registry_attr,
                        device_attr]},
        {'name': 'device',
         'collection': 'cloudiot.projects.locations.registries.groups.devices',
         'attributes': [project_attr, location_attr, registry_attr,
                        group_attr, device_attr]}]
    command_data['arguments']['resource'] = {
        'arg_name': 'device',
        'help_text': 'group help',
        'spec': {'name': 'device', 'resources': sub_resources}}
    d = yaml_command_schema.CommandData('describe', command_data)

    # Set up the issue request hook (similar to what would be used in real
    # life, chooses service/request type based on result of parsing.)
    def request(ref, args):
      device = args.CONCEPTS.device.Parse()
      if device.type_.name == 'cloudiot.projects.locations.registries.devices':
        service = mocked_iot_client.projects_locations_registries_devices
        req = (iot_messages
               .CloudiotProjectsLocationsRegistriesDevicesGetRequest())
      else:
        service = (
            mocked_iot_client.projects_locations_registries_groups_devices)
        req = (iot_messages
               .CloudiotProjectsLocationsRegistriesGroupsDevicesGetRequest())
      req.name = ref.RelativeName()
      return service.Get(req)
    issue_request_mock = mock.MagicMock()
    d.request.issue_request_hook = issue_request_mock
    issue_request_mock.side_effect = request

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'DEVICE', '--location', '--registry', '--group')
    result = cli.Execute(arg_list)
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')


class ListCommandTests(CommandTestsBase):

  def Expect(self):
    response = self.messages.InstanceList(
        id='projcets/foo/zones/zone1/instances',
        items=[self.messages.Instance(name='instance-1'),
               self.messages.Instance(name='instance-2')]
    )
    self.mocked_client.instances.List.Expect(
        self.messages.ComputeInstancesListRequest(
            zone='z',
            project='p'
        ),
        response=response)
    return response

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'list'], self.MakeCommandData(is_list=True))
    self.assertTrue(issubclass(command, calliope_base.ListCommand))
    global_mock.assert_called_once_with(command)

  def testRun(self):
    self.Expect()
    d = yaml_command_schema.CommandData('list',
                                        self.MakeCommandData(is_list=True))
    d.output.format = 'table(name)'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, '--zone', '--filter', '--limit', '--page-size',
                    '--sort-by')
    cli.Execute(['command', '--project', 'p', '--zone', 'z'])
    self.AssertOutputEquals('NAME\ninstance-1\ninstance-2\n')

  def testRunURI(self):
    self.Expect()
    d = yaml_command_schema.CommandData('list',
                                        self.MakeCommandData(is_list=True))
    d.response.id_field = 'name'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, '--zone', '--filter', '--limit', '--page-size',
                    '--sort-by', '--uri', '--no-uri')
    cli.Execute(['command', '--project', 'p', '--zone', 'z', '--uri'])
    self.AssertOutputEquals("""
https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/instance-1
https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/instance-2
""".lstrip('\n'), normalize_space=True)


class DeleteCommandTests(CommandTestsBase):

  def Expect(self, is_async=False):
    running_response, done_response = self.OperationResponses()
    self.mocked_client.instances.Delete.Expect(
        self.messages.ComputeInstancesDeleteRequest(
            instance='i', zone='z', project='p'),
        response=running_response)
    if not is_async:
      self.ExpectOperation()
    return running_response, done_response

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'delete'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.DeleteCommand))
    global_mock.assert_called_once_with(command)

  def testRunSync(self):
    _, done_response = self.Expect()
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    self.WriteInput('y\n')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You are about to delete instance [i]')
    self.AssertErrContains('Delete request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [operation-12345] to complete')
    self.AssertErrContains('Deleted instance [i]')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    self.WriteInput('y\n')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z', 'i', '--async'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You are about to delete instance [i]')
    self.AssertErrContains(
        'Delete request issued for: [i]\n'
        'Check operation [operation-12345] for status.')
    self.AssertErrNotContains('Deleted instance [i]')
    self.assertEqual(result, running_response)

  def testRunNoOperationMethod(self):
    """Test for when the API doesn't return an LRO."""
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'delete',
        self.MakeCommandData())
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    self.WriteInput('y\n')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You are about to delete instance [i]')
    self.AssertErrContains('Deleted instance [i]')
    self.assertEqual(result, running_response)

  def testDisplayName(self):
    self.Expect()
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.arguments.resource.display_name_hook = lambda x, y: 'display name'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.WriteInput('y\n')
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('You are about to delete instance [display name]')
    self.AssertErrContains('Delete request issued for: [display name]')
    self.AssertErrContains('Deleted instance [display name]')


class CreateCommandTests(CommandTestsBase):

  def Expect(self, is_async=False):
    running_response, _ = self.OperationResponses()
    self.mocked_client.instances.Insert.Expect(
        self.messages.ComputeInstancesInsertRequest(
            instance=self.messages.Instance(name='i'), zone='z', project='p'),
        response=running_response)

    if not is_async:
      self.ExpectOperation()
      self.mocked_client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='i', zone='z', project='p'),
          response={'foo': 'bar'},
          enable_type_checking=False)
    return running_response, {'foo': 'bar'}

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    d = self.MakeCommandData(is_create=True)
    d['request']['method'] = 'insert'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'create'], d)
    self.assertTrue(issubclass(command, calliope_base.CreateCommand))
    global_mock.assert_called_once_with(command)

  def testRunSync(self):
    _, done_response = self.Expect()
    d = yaml_command_schema.CommandData(
        'create', self.MakeCommandData(is_create=True,
                                       is_async='zoneOperations'))
    d.request.method = 'insert'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Create request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [operation-12345] to complete')
    self.AssertErrContains('Created instance [i]')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'create', self.MakeCommandData(is_create=True,
                                       is_async='zoneOperations'))
    d.request.method = 'insert'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z', 'i', '--async'])
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Create request issued for: [i]\n'
        'Check operation [operation-12345] for status.')
    self.AssertErrNotContains('Created instance [i]')
    self.assertEqual(result, running_response)

  def testRunMultitype_ParseResourceFalse_DisplayName(self):
    # This is a long test, but it tests the expected use case of a multitype
    # resource in a create command: the resource could either be a child or
    # the parent. Thus, we need a hook for parsing the resource into the
    # request (and parse_resource_into_request=False); and a hook for the
    # display name so the log messages make sense.
    running_response, _ = self.OperationResponses()
    self.mocked_client.instances.Insert.Expect(
        self.messages.ComputeInstancesInsertRequest(
            zone='z', project='p'),
        response=running_response)
    running_response, done_response = self.OperationResponses()
    done_response.targetLink = 'projects/p/zones/z/instances/i'
    self.mocked_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-12345', project='p', zone='z'),
        response=running_response)
    self.mocked_client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-12345', project='p', zone='z'),
        response=done_response)

    command_data = self.MakeCommandData(
        is_create=True,
        is_async='zoneOperations')
    command_data['request']['parse_resource_into_request'] = False
    command_data['request']['request_string'] = 'Create request issued'
    sub_resources = [
        {'name': 'zone',
         'collection': 'compute.zones',
         'attributes': [
             {'parameter_name': 'project',
              'attribute_name': 'project',
              'help': 'help1'},
             {'parameter_name': 'zone',
              'attribute_name': 'zone',
              'help': 'help2'}]},
        {'name': 'instance',
         'collection': 'compute.instances',
         'attributes': [
             {'parameter_name': 'project',
              'attribute_name': 'project',
              'help': 'help1'},
             {'parameter_name': 'zone',
              'attribute_name': 'zone',
              'help': 'help2'},
             {'parameter_name': 'instance',
              'attribute_name': 'instance',
              'help': 'help3'}]}]
    command_data['arguments']['resource'] = {
        'arg_name': 'instance',
        'help_text': 'group help',
        'spec': {'name': 'zone-or-instance', 'resources': sub_resources}}

    d = yaml_command_schema.CommandData(
        'create', command_data)
    modify_request_mock1 = mock.MagicMock()

    def augment(ref, args, req):
      instance_or_zone = args.CONCEPTS.instance.Parse()
      if instance_or_zone.type_.name == 'instance':
        req.instance.name = ref.Name()
      req.project = ref.project
      req.zone = ref.zone
      return req

    modify_request_mock1.side_effect = augment
    d.request.modify_request_hooks = [modify_request_mock1]
    d.request.method = 'insert'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    d.async.extract_resource_result = False
    d.async.result_attribute = 'targetLink'

    def get_name(resource_ref, args):
      if args.CONCEPTS.instance.Parse().type_.name == 'zone':
        return 'name not specified'
      return resource_ref.Name()
    d.arguments.resource.display_name_hook = get_name

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Create request issued for: [name not specified]\n')
    self.assertEqual(result, 'projects/p/zones/z/instances/i')

  def testRunNoOperationMethod(self):
    """Test for when the API doesn't return an LRO."""
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'create', self.MakeCommandData(is_create=True))
    d.request.method = 'insert'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Created instance [i]')
    self.assertEqual(result, running_response)

  def testDisplayName(self):
    self.Expect()
    d = yaml_command_schema.CommandData(
        'create', self.MakeCommandData(is_create=True,
                                       is_async='zoneOperations'))
    d.request.method = 'insert'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    d.arguments.resource.display_name_hook = lambda x, y: 'display name'
    cli = self.MakeCLI(d)
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('Create request issued for: [display name]')
    self.AssertErrContains('Created instance [display name]')

  def testWithParentResource(self):
    m = self.functions_messages
    done_response = m.Operation(done=True)
    self.mocked_functions_client.projects_locations_functions.Create.Expect(
        m.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location='projects/p/locations/l'),
        response=done_response)

    command_data = self.MakeCommandData(
        is_create=True,
        collection='cloudfunctions.projects.locations.functions')
    command_data['arguments']['resource'] = {
        'arg_name': 'location',
        'help_text': 'group help',
        'is_parent_resource': True,
        'spec': {
            'name': 'location',
            'collection': 'cloudfunctions.projects.locations',
            'attributes': [
                {'parameter_name': 'projectsId',
                 'attribute_name': 'project',
                 'help': 'help1'},
                {'parameter_name': 'locationsId',
                 'attribute_name': 'location',
                 'help': 'help2'}]}}

    d = yaml_command_schema.CommandData(
        'create', command_data)

    d.request.method = 'create'

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'LOCATION')
    result = cli.Execute(
        ['command', '--project', 'p', 'l'])
    self.assertEqual(done_response, result)
    self.AssertErrNotContains('Created')
    self.AssertErrNotContains('issued for')

  def testWithParentResourceAsync(self):
    m = self.functions_messages
    expected_function = m.CloudFunction(name='myfunction')
    expected_result = encoding.DictToMessage(
        encoding.MessageToDict(expected_function),
        m.Operation.ResponseValue)
    running_response = m.Operation(name='operations/12345', done=False)
    done_response = m.Operation(name='operations/12345', done=True,
                                response=expected_result)

    self.mocked_functions_client.projects_locations_functions.Create.Expect(
        m.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location='projects/p/locations/l'),
        response=running_response)
    self.mocked_functions_client.operations.Get.Expect(
        m.CloudfunctionsOperationsGetRequest(
            name='operations/12345'),
        response=done_response)

    command_data = self.MakeCommandData(
        is_create=True,
        collection='cloudfunctions.projects.locations.functions')
    command_data['async'] = {
        'collection': 'cloudfunctions.operations',
        'extract_resource_result': False,
        'result_attribute': 'response'}
    command_data['arguments']['resource'] = {
        'arg_name': 'location',
        'help_text': 'group help',
        'is_parent_resource': True,
        'spec': {
            'name': 'location',
            'collection': 'cloudfunctions.projects.locations',
            'attributes': [
                {'parameter_name': 'projectsId',
                 'attribute_name': 'project',
                 'help': 'help1'},
                {'parameter_name': 'locationsId',
                 'attribute_name': 'location',
                 'help': 'help2'}]}}

    d = yaml_command_schema.CommandData(
        'create', command_data)

    d.request.method = 'create'

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'LOCATION', '--async', '--no-async')
    result = cli.Execute(
        ['command', '--project', 'p', 'l'])
    result_function = encoding.DictToMessage(
        encoding.MessageToDict(result),
        m.CloudFunction)
    self.assertEqual(expected_function, result_function)
    self.AssertErrContains('Create')
    self.AssertErrContains('issued')
    self.AssertErrNotContains('Created')
    self.AssertErrNotContains('issued for')


class WaitCommandTests(CommandTestsBase):

  def Expect(self, is_async=False):
    running_response, done_response = self.OperationResponses()
    self.ExpectOperation()
    return running_response, done_response

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'wait'], self.MakeCommandData(is_async='zoneOperations'))
    self.assertTrue(issubclass(command, calliope_base.Command))
    global_mock.assert_called_once_with(command)

  def testRun(self):
    _, done_response = self.Expect()
    spec = {'name': 'operation', 'collection': 'compute.zoneOperations',
            'attributes': [
                {'parameter_name': 'zone', 'attribute_name': 'zone',
                 'help': 'the zone'},
                {'parameter_name': 'operation', 'attribute_name': 'operation',
                 'help': 'the op'}]}
    data = {
        'help_text': {'brief': 'brief help'},
        'request': {'collection': 'compute.zoneOperations'},
        'arguments': {
            'resource': {
                'help_text': 'help',
                'spec': spec}},
        'async': {'collection': 'compute.zoneOperations',
                  'state': {'field': 'status', 'success_values': ['DONE']}}
    }
    d = yaml_command_schema.CommandData('wait', data)
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'OPERATION', '--zone')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z', 'operation-12345'])
    self.AssertErrContains(
        'Waiting for operation [operation-12345] to complete')
    self.AssertOutputEquals("""
id: '12345'
name: operation-12345
selfLink: https://www.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
status: DONE
""".lstrip('\n'), normalize_space=True)
    self.assertEqual(result, done_response)


class GenericCommandTests(CommandTestsBase):

  def Expect(self, is_async=False):
    running_response, _ = self.OperationResponses()
    self.mocked_client.instances.SetTags.Expect(
        self.messages.ComputeInstancesSetTagsRequest(
            instance='i', zone='z', project='p',
            tags=self.messages.Tags(items=['foo', 'bar'])),
        response=running_response)

    if not is_async:
      self.ExpectOperation()
      self.mocked_client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='i', zone='z', project='p'),
          response={'foo': 'bar'},
          enable_type_checking=False)
    return running_response, {'foo': 'bar'}

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'delete'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.Command))
    global_mock.assert_called_once_with(command)

  def testRunSync(self):
    _, done_response = self.Expect()
    data = self.MakeCommandData(is_async='zoneOperations')
    data['request']['method'] = 'setTags'
    data['arguments']['params'] = [
        {'api_field': 'tags.items', 'arg_name': 'tags',
         'help_text': 'the tags'}]
    d = yaml_command_schema.CommandData('set-tags', data)
    d.request.method = 'setTags'
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async',
                    '--tags')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i',
                          '--tags', 'foo,bar'])
    self.AssertOutputEquals('foo: bar\n')
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [operation-12345] to complete')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    data = self.MakeCommandData(is_async='zoneOperations')
    data['request']['method'] = 'setTags'
    data['arguments']['params'] = [
        {'api_field': 'tags.items', 'arg_name': 'tags',
         'help_text': 'the tags'}]
    d = yaml_command_schema.CommandData('set-tags', data)
    d.async.response_name_field = 'selfLink'
    d.async.state.field = 'status'
    d.async.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async',
                    '--tags')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i',
                          '--async', '--tags', 'foo,bar'])
    self.AssertOutputEquals("""
id: '12345'
name: operation-12345
selfLink: https://www.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
status: RUNNING
""".lstrip('\n'), normalize_space=True)
    self.AssertErrContains(
        'Request issued for: [i]\n'
        'Check operation [operation-12345] for status.')
    self.assertEqual(result, running_response)

  def testRunNoOperationMethod(self):
    """Test for when the API doesn't return an LRO."""
    running_response, _ = self.Expect(is_async=True)
    data = self.MakeCommandData()
    data['request']['method'] = 'setTags'
    data['arguments']['params'] = [
        {'api_field': 'tags.items', 'arg_name': 'tags',
         'help_text': 'the tags'}]
    d = yaml_command_schema.CommandData('set-tags', data)
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--tags')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i',
                          '--tags', 'foo,bar'])
    self.AssertOutputEquals("""
id: '12345'
name: operation-12345
selfLink: https://www.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
status: RUNNING
""".lstrip('\n'), normalize_space=True)
    self.assertEqual(result, running_response)


class AsyncPollerTests(CommandTestsBase):

  def testIsDone(self):
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.async.state.field = 'status'
    d.async.error.field = 'error'
    d.async.state.success_values = ['DONE']
    d.async.state.error_values = ['ERROR']

    class Op(object):

      def __init__(self):
        self.status = None
        self.error = None

    op = Op()
    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    self.assertFalse(poller.IsDone(op))
    op.status = 'FOO'
    self.assertFalse(poller.IsDone(op))
    op.status = 'DONE'
    self.assertTrue(poller.IsDone(op))
    op.status = 'ERROR'
    with self.assertRaisesRegex(waiter.OperationError,
                                'The operation failed.'):
      poller.IsDone(op)

    # This is sort of an invalid state, but respect the status first, even if
    # there is an error.
    op.status = None
    op.error = 'custom error'
    self.assertFalse(poller.IsDone(op))
    # Error even on a success value if error field is set.
    op.status = 'DONE'
    with self.assertRaisesRegex(waiter.OperationError, 'custom error'):
      poller.IsDone(op)
    op.status = 'ERROR'
    with self.assertRaisesRegex(waiter.OperationError, 'custom error'):
      poller.IsDone(op)

  def testPoll(self):
    running_response = self.messages.Operation(
        id=12345, name='operation-12345',
        selfLink='https://www.googleapis.com/compute/v1/projects/p/zones/z/'
                 'operations/operation-12345',
        error=None,
        status=self.messages.Operation.StatusValueValuesEnum.RUNNING)
    for _ in range(3):
      self.mocked_client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-12345', project='p', zone='z'),
          response=running_response)

    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    op_ref = resources.REGISTRY.Parse(
        'operation-12345', params={'project': 'p', 'zone': 'z'},
        collection='compute.zoneOperations')
    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

    # Test operations api version override.
    d.request.api_version = 'v2'
    d.async.api_version = 'v1'
    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

    # Intentionally swapping zone and project to test the remapping.
    d.async.operation_get_method_params = {
        'project': 'zone', 'zone': 'project', 'operation': 'operation'}
    # Swap project and zone in the reference as well so it ends up being the
    # same request.
    op_ref = resources.REGISTRY.Parse(
        'operation-12345', params={'project': 'z', 'zone': 'p'},
        collection='compute.zoneOperations')
    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

  def testGetResultNoExtract(self):
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))

    class Result(object):

      name = 'foo'

    o = Result()

    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    self.assertEqual(o, poller.GetResult(o))

    # Doesn't return result when explicitly disabled even if resource ref is
    # valid.
    d.async.extract_resource_result = False
    poller = yaml_command_translator.AsyncOperationPoller(d, object())
    self.assertEqual(o, poller.GetResult(o))

    # Test extracting a specific attribute from the operation.
    d.async.result_attribute = 'name'
    poller = yaml_command_translator.AsyncOperationPoller(d, None)
    self.assertEqual(o.name, poller.GetResult(o))

  def testGetResult(self):
    class Result(object):

      class Foo(object):

        name = 'bar'

      foo = Foo

    response = Result()

    for _ in range(3):
      self.mocked_client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='i', zone='z', project='p'),
          response=response,
          enable_type_checking=False)

    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    resource_ref = resources.REGISTRY.Parse(
        'i', params={'zone': 'z', 'project': 'p'},
        collection='compute.instances')
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    self.assertEqual(response, poller.GetResult(None))

    # Test extracting a specific attribute from the result.
    d.async.result_attribute = 'foo.name'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    self.assertEqual('bar', poller.GetResult(None))

    # Test invalid attribute on the result.
    d.async.result_attribute = 'foo.junk'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    with self.assertRaisesRegex(AttributeError,
                                r'Attribute path \[foo.junk\] not found'):
      poller.GetResult(None)

  def testGetResult_NameInGetRequest(self):
    """Tests the same scenario as testGetResult with a relative name Get."""

    class Result(object):

      class Foo(object):

        name = 'bar'

      foo = Foo

    response = Result()

    m = self.functions_messages
    get_req_type = m.CloudfunctionsProjectsLocationsFunctionsGetRequest
    for _ in range(3):
      self.mocked_functions_client.projects_locations_functions.Get.Expect(
          get_req_type(name='projects/p/locations/l/functions/f'),
          response=response,
          enable_type_checking=False)

    data = {
        'help_text': {'brief': 'brief help'},
        'request': {
            'collection': 'cloudfunctions.projects.locations.functions'
        },
        'arguments': {
            'resource': {
                'help_text': 'help',
                'spec': {
                    'name': 'function',
                    'collection': 'cloudfunctions.projects.locations.functions',
                    'request_id_field': 'function.name',
                    'attributes': [
                        {
                            'parameter_name': 'function',
                            'attribute_name': 'function',
                            'help': 'the function'
                        },
                        {
                            'parameter_name': 'location',
                            'attribute_name': 'location',
                            'help': 'the location'
                        },
                    ]
                }
            }
        },
        'async': {'collection': 'cloudfunctions.operations'}
    }
    d = yaml_command_schema.CommandData('delete', data)

    resource_ref = resources.REGISTRY.Parse(
        'f', params={'locationsId': 'l', 'projectsId': 'p'},
        collection='cloudfunctions.projects.locations.functions')
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    self.assertEqual(response, poller.GetResult(None))

    # Test extracting a specific attribute from the result.
    d.async.result_attribute = 'foo.name'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    self.assertEqual('bar', poller.GetResult(None))

    # Test invalid attribute on the result.
    d.async.result_attribute = 'foo.junk'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref)
    with self.assertRaisesRegex(AttributeError,
                                r'Attribute path \[foo.junk\] not found'):
      poller.GetResult(None)


class GetIamPolicyCommandTests(CommandTestsBase):

  def GetIamPolicyCLI(self):
    command_data = yaml_command_schema.CommandData(
        'get_iam_policy',
        self.MakeIAMCommandData(help_text='to get IAM policy of'))
    return self.MakeCLI(command_data)

  def Expect(self, response=None):
    client = apis.GetClientClass('cloudiot', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    mocked_client.projects_locations_registries.GetIamPolicy.Expect(
        messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i'),
        response=response or {'etag': 'ACAB'},
        enable_type_checking=False)

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'],
        self.MakeIAMCommandData(
            help_text='to get IAM policy of',
            brief=brief,
            description=description))
    self.assertTrue(issubclass(command, calliope_base.ListCommand))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'],
        self.MakeIAMCommandData(help_text='to get IAM policy of'))
    self.assertTrue(issubclass(command, calliope_base.ListCommand))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testAdditionalArgsHook(self):
    command_data = yaml_command_schema.CommandData(
        'get_iam_policy',
        self.MakeIAMCommandData(help_text='to get IAM policy of'))
    additional_args_mock = mock.MagicMock()
    side_effect = [calliope_base.Argument('--foo', help='Auxilio aliis.')]
    additional_args_mock.side_effect = lambda: side_effect
    command_data.arguments.additional_arguments_hook = additional_args_mock
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'REGISTRY', '--region', '--filter', '--sort-by',
                    '--page-size', '--limit', '--foo')

  def testRun(self):
    self.Expect()
    cli = self.GetIamPolicyCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', '--filter', '--sort-by',
                    '--page-size', '--limit')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i'])
    self.assertEqual(result, {'etag': 'ACAB'})
    self.AssertOutputEquals('etag: ACAB\n')

  def testRunWithResponseErrorHandler(self):
    command_data = yaml_command_schema.CommandData(
        'get_iam_policy',
        self.MakeIAMCommandData(help_text='to get IAM policy of'))
    execute_params = ['command', '--project', 'p', '--region', 'r', 'i']
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)


class SetIamPolicyCommandTests(CommandTestsBase):

  def _MakePolicy(self, bindings=None, etag=b'ACAB', messages=None):
    m = messages or self.messages
    return m.Policy(bindings=bindings or [], etag=etag)

  def SetUp(self):
    self.client = apis.GetClientClass('cloudiot', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.policy = self._MakePolicy()

  def Expect(self, response=None):
    set_iam_policy_request = self.messages.SetIamPolicyRequest(
        policy=self.policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=set_iam_policy_request),
        response=response or self.policy,
        enable_type_checking=False)

  def MakeProjectCommandData(self, brief=None, description=None, notes=None,
                             params=None):
    collection = 'cloudresourcemanager.projects'
    spec = {
        'name': 'project',
        'collection': collection,
        'attributes': [
            {
                'parameter_name': 'projectId',
                'attribute_name': 'project_id',
                'help': 'The name of the Project.',
            }
        ],
    }
    data = {
        'help_text': {
            'brief': brief or '<brief>',
            'DESCRIPTION': description or '<DESCRIPTION>',
            'NOTES': notes,
        },
        'request': {
            'collection': collection,
        },
        'arguments': {
            'resource': {
                'help_text': 'The {resource} for which to set the IAM policy.',
                'spec': spec,
            },
        },
    }
    if params:
      data['arguments']['params'] = params

    return data

  @classmethod
  def SetIamPolicyTranslator(cls, brief=None, description=None):
    return yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        cls.MakeIAMCommandData(
            help_text='to set IAM policy to',
            brief=brief,
            description=description))

  def GetSetIamPolicyCLI(self):
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    return self.MakeCLI(command_data)

  def testRun(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))
    self.Expect()
    cli = self.GetSetIamPolicyCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i',
                          'myfile'])
    self.assertEqual(result, self.policy)
    self.AssertErrContains("""
    Updated IAM policy for registry [i].
    """.lstrip('\n'), normalize_space=True)
    self.AssertOutputEquals("""
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunFullPolicy(self):
    self.policy = self._MakePolicy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}])
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))
    self.Expect()
    cli = self.GetSetIamPolicyCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i',
                          'myfile'])
    self.assertEqual(result, self.policy)
    self.AssertErrContains("""
    Updated IAM policy for registry [i].
    """.lstrip('\n'), normalize_space=True)
    self.AssertOutputEquals("""
    bindings:
    - members:
    - user:mike@example.com
    - group:admins@example.com
    - domain:google.com
    role: roles/owner
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunWithUpdateMask(self):
    client = apis.GetClientClass('cloudresourcemanager', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = self._MakePolicy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}],
        messages=messages)
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(policy, 'bindings,etag,version'))
    policy.version = 0
    set_iam_policy_request = messages.SetIamPolicyRequest(
        policy=policy, updateMask='bindings,etag,version')
    mocked_client.projects.SetIamPolicy.Expect(
        messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='projects/p',
            setIamPolicyRequest=set_iam_policy_request),
        policy)
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeProjectCommandData())
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'PROJECT_ID', 'POLICY_FILE')
    result = cli.Execute(['command', 'p', 'myfile'])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for project [p].',
        normalize_space=True)
    self.AssertOutputEquals("""
      bindings:
      - members:
      - user:mike@example.com
      - group:admins@example.com
      - domain:google.com
      role: roles/owner
      etag: QUNBQg==
      version: 0
    """.lstrip('\n'), normalize_space=True)

  def testRunBadFile(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          side_effect=gcloud_exceptions.BadFileException(
                              'Bad Policy File'))
    cli = self.GetSetIamPolicyCLI()
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])
    self.AssertErrContains('Bad Policy File')

  def testRunWithOverrides(self):
    client = apis.GetClientClass('ml', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = messages.GoogleIamV1Policy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}],
        etag=b'ACAB',
        version=0)
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(policy, 'bindings,etag,version'))
    set_iam_policy_request = messages.GoogleIamV1SetIamPolicyRequest(
        policy=policy, updateMask='bindings,etag,version')
    mocked_client.projects_models.SetIamPolicy.Expect(
        messages.MlProjectsModelsSetIamPolicyRequest(
            resource='projects/p/models/m',
            googleIamV1SetIamPolicyRequest=set_iam_policy_request),
        policy)
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(
            help_text='to set IAM policy to', another_collection=True))
    command_data.iam = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'MODEL', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', 'm', 'myfile'])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for model [m].',
        normalize_space=True)
    self.AssertOutputEquals("""
      bindings:
      - members:
      - user:mike@example.com
      - group:admins@example.com
      - domain:google.com
      role: roles/owner
      etag: QUNBQg==
      version: 0
      """.lstrip('\n'), normalize_space=True)

  def testRunBadOverride(self):
    d = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))

    d.iam = yaml_command_schema.IamData({
        'message_type_overrides': {
            'policy': 'FuBarPolicy'
        }
    })
    cli = self.MakeCLI(d)
    with self.assertRaisesRegex(ValueError,
                                r'Policy type \[FuBarPolicy\] not found.'):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        self.MakeIAMCommandData(
            help_text='to set IAM policy to',
            brief=brief,
            description=description))
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testRunWithResponseErrorHandler(self):
    self.StartObjectPatch(
        iam_util,
        'ParsePolicyFileWithUpdateMask',
        return_value=(self.policy, 'bindings,etag,version'))
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    execute_params = [
        'command', '--project', 'p', '--region', 'r', 'i', 'myfile'
    ]
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)


class AddIamPolicyBindingCommandTests(CommandTestsBase):

  def _MakePolicy(self, bindings=None, etag=b'ACAB', messages=None):
    m = messages or self.messages
    return m.Policy(bindings=bindings or [], etag=etag)

  def _MakeBinding(self, role, members=None, messages=None):
    m = messages or self.messages
    return m.Binding(role=role, members=members)

  def SetUp(self):
    self.client = apis.GetClientClass('cloudiot', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.start_policy = self._MakePolicy()
    self.updated_policy = self._MakePolicy(
        [self._MakeBinding('roles/viewer', ['user:admin@foo.com'])])

  def _ExpectGetIamPolicy(self):
    req = self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
        resource='projects/p/locations/r/registries/i')

    self.mocked_client.projects_locations_registries.GetIamPolicy.Expect(
        request=req, response=self.start_policy)

  def _ExpectSetUpdatedIamPolicy(self, response=None):
    req = self.messages.SetIamPolicyRequest(policy=self.updated_policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=req),
        response=response or self.updated_policy,
        enable_type_checking=False)

  def Expect(self, response=None):
    self._ExpectGetIamPolicy()
    self._ExpectSetUpdatedIamPolicy(response=response)

  @classmethod
  def GetAddIamPolicyBindingCommandTranslator(cls, brief=None,
                                              description=None):
    return yaml_command_translator.Translator().Translate(
        ['foo', 'add_iam_policy_binding'],
        cls.MakeIAMCommandData(
            help_text='to add IAM policy binding to',
            brief=brief,
            description=description))

  def GetAddIamPolicyBindingCLI(self):
    command_data = yaml_command_schema.CommandData(
        'add_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to add IAM policy binding to'))
    return self.MakeCLI(command_data)

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = self.GetAddIamPolicyBindingCommandTranslator(brief, description)
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = self.GetAddIamPolicyBindingCommandTranslator()
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testRun(self):
    self.Expect()
    cli = self.GetAddIamPolicyBindingCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ])
    self.assertEqual(result, self.updated_policy)
    self.AssertErrContains(
        """
    Updated IAM policy for registry [i].
    """.lstrip('\n'),
        normalize_space=True)
    self.AssertOutputEquals(
        """
    bindings:
    - members:
    - user:admin@foo.com
    role: roles/viewer
    etag: QUNBQg==
    """.lstrip('\n'),
        normalize_space=True)

  def testRunWithOverrides(self):
    client = apis.GetClientClass('ml', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': ['user:mike@example.com']
    }])

    updated_policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': [
            'user:mike@example.com',
            'group:admins@example.com',
        ]
    }])
    self.StartObjectPatch(
        iam_util,
        'ParsePolicyFileWithUpdateMask',
        return_value=(updated_policy, 'bindings,etag,version'))

    mocked_client.projects_models.GetIamPolicy.Expect(
        messages.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/p/models/m'),
        policy)

    set_iam_policy_request = messages.GoogleIamV1SetIamPolicyRequest(
        policy=updated_policy)
    mocked_client.projects_models.SetIamPolicy.Expect(
        messages.MlProjectsModelsSetIamPolicyRequest(
            resource='projects/p/models/m',
            googleIamV1SetIamPolicyRequest=set_iam_policy_request),
        updated_policy)
    command_data = yaml_command_schema.CommandData(
        'add_iam_policy_binding',
        self.MakeIAMCommandData(
            help_text='to add IAM policy binding to', another_collection=True))
    command_data.iam = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'MODEL', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--project', 'p', 'm', '--role',
        'roles/owner', '--member', 'group:admins@example.com'
    ])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for model [m].', normalize_space=True)
    self.AssertOutputEquals(
        """
      bindings:
      - members:
      - user:mike@example.com
      - group:admins@example.com
      role: roles/owner
      """.lstrip('\n'),
        normalize_space=True)

  def testRunWithResponseErrorHandler(self):
    command_data = yaml_command_schema.CommandData(
        'add_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to add IAM policy binding to'))
    execute_params = [
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ]
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)


class RemoveIamPolicyBindingCommandTests(CommandTestsBase):

  def _MakePolicy(self, bindings=None, etag=b'ACAB', messages=None):
    msgs = messages or self.messages
    return msgs.Policy(bindings=bindings or [], etag=etag)

  def _MakeBinding(self, role, members=None, messages=None):
    msgs = messages or self.messages
    return msgs.Binding(role=role, members=members)

  def SetUp(self):
    self.client = apis.GetClientClass('cloudiot', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.start_policy = self._MakePolicy(
        [self._MakeBinding('roles/viewer', ['user:admin@foo.com'])])
    self.updated_policy = self._MakePolicy()

  def _ExpectGetIamPolicy(self):
    req = self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
        resource='projects/p/locations/r/registries/i')

    self.mocked_client.projects_locations_registries.GetIamPolicy.Expect(
        request=req, response=self.start_policy)

  def _ExpectSetUpdatedIamPolicy(self, response=None):
    req = self.messages.SetIamPolicyRequest(policy=self.updated_policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=req),
        response=response or self.updated_policy,
        enable_type_checking=False)

  def Expect(self, response=None):
    self._ExpectGetIamPolicy()
    self._ExpectSetUpdatedIamPolicy(response=response)

  @classmethod
  def GetRemoveIamPolicyBindingCommandTranslator(cls,
                                                 brief=None,
                                                 description=None):
    return yaml_command_translator.Translator().Translate(
        ['foo', 'remove_iam_policy_binding'],
        cls.MakeIAMCommandData(
            help_text='to remove IAM policy binding from',
            brief=brief,
            description=description))

  def GetRemoveIamPolicyBindingCLI(self):
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to remove IAM policy binding from'))
    return self.MakeCLI(command_data)

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    translator = self.GetRemoveIamPolicyBindingCommandTranslator(
        brief, description)
    self.assertTrue(issubclass(translator, calliope_base.Command))
    self.assertEqual(brief, translator.detailed_help.get('brief'))
    self.assertEqual(description, translator.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    translator = self.GetRemoveIamPolicyBindingCommandTranslator()
    self.assertTrue(issubclass(translator, calliope_base.Command))
    self.assertEqual('<brief>', translator.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>',
                     translator.detailed_help.get('DESCRIPTION'))

  def testRun(self):
    self.Expect()
    cli = self.GetRemoveIamPolicyBindingCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ])
    self.assertEqual(result, self.updated_policy)
    self.AssertErrContains(
        """
    Updated IAM policy for registry [i].
    """.lstrip('\n'),
        normalize_space=True)
    self.AssertOutputEquals(
        """
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunWithOverrides(self):
    client = apis.GetClientClass('ml', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': [
            'user:mike@example.com',
            'group:admins@example.com',
        ]
    }])
    updated_policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': ['user:mike@example.com']
    }])
    self.StartObjectPatch(
        iam_util,
        'ParsePolicyFileWithUpdateMask',
        return_value=(updated_policy, 'bindings,etag,version'))

    mocked_client.projects_models.GetIamPolicy.Expect(
        messages.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/p/models/m'),
        policy)

    set_iam_policy_request = messages.GoogleIamV1SetIamPolicyRequest(
        policy=updated_policy)
    mocked_client.projects_models.SetIamPolicy.Expect(
        messages.MlProjectsModelsSetIamPolicyRequest(
            resource='projects/p/models/m',
            googleIamV1SetIamPolicyRequest=set_iam_policy_request),
        updated_policy)
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(
            help_text='to remove IAM policy binding from',
            another_collection=True))
    command_data.iam = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'MODEL', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--project', 'p', 'm', '--role',
        'roles/owner', '--member', 'group:admins@example.com'
    ])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for model [m].', normalize_space=True)
    self.AssertOutputEquals(
        """
      bindings:
      - members:
      - user:mike@example.com
      role: roles/owner
      """.lstrip('\n'),
        normalize_space=True)

  def testRunWithResponseErrorHandler(self):
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to remove IAM policy binding from'))
    execute_params = [
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ]
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)


class UpdateCommandTests(CommandTestsBase):

  def SetUp(self):
    self.client = apis.GetClientClass('spanner', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def _OperationResponses(self):
    running_response = self.messages.Operation(
        done=False, name='projects/p/instances/i/operations/o')
    done_response = self.messages.Operation(
        done=True, name='projects/p/instances/i/operations/o')

    return running_response, done_response

  def _MakeUpdateCommandData(self):
    spec = {
        'name':
            'instance',
        'collection':
            'spanner.projects.instances',
        'attributes': [{
            'parameter_name': 'instancesId',
            'attribute_name': 'instance',
            'help': 'The name of Cloud Spanner instance.'
        }]
    }

    return {
        'help_text': {
            'brief': '<brief>',
            'DESCRIPTION': '<DESCRIPTION>',
            'NOTES': '<NOTES>'
        },
        'request': {
            'collection': 'spanner.projects.instances'
        },
        'arguments': {
            'resource': {
                'help_text': 'The {resource} to update.',
                'spec': spec,
            }
        },
        'update': {}
    }

  def _ExpectUpdate(self, field_mask, is_async=False, full_update=False):
    running_response, _ = self._OperationResponses()
    req = self.messages.SpannerProjectsInstancesPatchRequest(
        name='projects/p/instances/i',
        updateInstanceRequest=self.messages.UpdateInstanceRequest(
            instance=self.messages.Instance(
                displayName='dn' if full_update else None,
                name='projects/p/instances/i' if full_update else None,
                nodeCount=2,
            ),
            fieldMask=field_mask))
    self.mocked_client.projects_instances.Patch.Expect(
        request=req, response=running_response)

    updated_instance = self.messages.Instance(
        name='projects/p/instances/i', nodeCount=2)

    if not is_async:
      self._ExpectOperation()
      self.mocked_client.projects_instances.Get.Expect(
          request=self.messages.SpannerProjectsInstancesGetRequest(
              name='projects/p/instances/i'),
          response=updated_instance)

    return running_response, updated_instance

  def _ExpectGet(self):
    req = self.messages.SpannerProjectsInstancesGetRequest(
        name='projects/p/instances/i')
    ins = self.messages.Instance(
        displayName='dn', name='projects/p/instances/i', nodeCount=1)
    self.mocked_client.projects_instances.Get.Expect(request=req, response=ins)

  def _ExpectOperation(self):
    running_response, done_response = self._OperationResponses()
    self.mocked_client.projects_instances_operations.Get.Expect(
        self.messages.SpannerProjectsInstancesOperationsGetRequest(
            name='projects/p/instances/i/operations/o'),
        response=running_response)
    self.mocked_client.projects_instances_operations.Get.Expect(
        self.messages.SpannerProjectsInstancesOperationsGetRequest(
            name='projects/p/instances/i/operations/o'),
        response=done_response)

  def testGeneration(self):
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'delete'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.Command))
    global_mock.assert_called_once_with(command)

  def testRunAsync(self):
    self._ExpectUpdate(field_mask='nodeCount', is_async=True)
    data = self._MakeUpdateCommandData()
    data['async'] = {'collection': 'spanner.projects.instances.operations'}
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }]
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    d.async.state.field = 'done'
    d.async.state.success_values = [True]
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--nodes', '--async', '--no-async')
    cli.Execute(['command', 'i', '--project', 'p', '--async', '--nodes', '2'])
    self.AssertOutputEquals(
        """
done: false
name: projects/p/instances/i/operations/o
""".lstrip('\n'),
        normalize_space=True)
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains('Check operation [o] for status.')
    self.AssertErrContains('Updated instance [i].\n')

  def testRunSync(self):
    _, done_response = self._ExpectUpdate(
        field_mask='nodeCount', is_async=False)
    data = self._MakeUpdateCommandData()
    data['async'] = {'collection': 'spanner.projects.instances.operations'}
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }]
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--nodes', '--async', '--no-async')
    result = cli.Execute(['command', 'i', '--project', 'p', '--nodes', '2'])
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains('Updated instance [i].\n')
    self.assertEqual(result, done_response)

  def testRunNoOperationMethod(self):
    """Test for when the API doesn't return an LRO."""
    self.mocked_client.projects_instances.Patch.Expect(
        request=(self.messages.SpannerProjectsInstancesPatchRequest(
            name='projects/p/instances/i',
            updateInstanceRequest=self.messages.UpdateInstanceRequest(
                instance=self.messages.Instance(
                    nodeCount=2, displayName='aaaa'),
                fieldMask='displayName,nodeCount'))),
        response='new instance',
        enable_type_checking=False)

    data = self._MakeUpdateCommandData()
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }, {
        'api_field': 'updateInstanceRequest.instance.displayName',
        'arg_name': 'description',
        'help_text': 'the description of the instance'
    }]
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--nodes', '--description')
    result = cli.Execute([
        'command', 'i', '--project', 'p', '--nodes', '2', '--description',
        'aaaa'
    ])
    self.assertEqual(result, 'new instance')
    self.AssertErrContains('Updated instance [i].\n')

  def testRunReadModifyUpdate(self):
    self._ExpectGet()
    self._ExpectUpdate(field_mask='nodeCount', is_async=True, full_update=True)
    data = self._MakeUpdateCommandData()
    data['async'] = {'collection': 'spanner.projects.instances.operations'}
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }]
    data['update']['mask_field'] = 'updateInstanceRequest.fieldMask'
    data['update']['read_modify_update'] = True
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    d.async.state.field = 'done'
    d.async.state.success_values = [True]
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--nodes', '--async', '--no-async')
    cli.Execute(['command', 'i', '--project', 'p', '--async', '--nodes', '2'])

    self.AssertOutputEquals(
        """
done: false
name: projects/p/instances/i/operations/o
""".lstrip('\n'),
        normalize_space=True)
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains('Check operation [o] for status.')
    self.AssertErrContains('Updated instance [i].\n')


if __name__ == '__main__':
  base.main()
