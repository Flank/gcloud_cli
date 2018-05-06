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
from __future__ import unicode_literals
import time

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
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.command_lib.util.apis import base

import mock
from six.moves import range  # pylint: disable=redefined-builtin


class CommandBuilderTests(base.Base):
  """Tests of the command builder."""

  def SetUp(self):
    self.MockGetListCreateMethods(('foo.instances', False))

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

  def MakeCommandData(self, collection='compute.instances', is_create=False,
                      is_list=False, is_async=None):
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
        'help_text': {'brief': 'brief help'},
        'request': {'collection': collection},
        'arguments': {
            'resource': {
                'help_text': 'help',
                'spec': spec}}
    }
    if is_async:
      data['async'] = {
          'collection':
          '.'.join(collection.split('.')[:-1]) + '.zoneOperations'}
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


class DescribeCommandTests(CommandTestsBase):

  def Expect(self, instance='i', response=None):
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance=instance, zone='z', project='p'),
        response=response or {'foo': 'bar'})

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
    self.AssertErrContains('PROMPT!\n')

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
          response={'foo': 'bar'})
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
          response={'foo': 'bar'})
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
          response=response)

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
          response=response)

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

  def Expect(self, instance='i', response=None):
    client = apis.GetClientClass('cloudiot', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    mocked_client.projects_locations_registries.GetIamPolicy.Expect(
        messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i'),
        response=response or {'etag': 'ACAB'})

  def MakeCommandData(self, brief=None, description=None, notes=None):
    collection = 'cloudiot.projects.locations.registries'
    spec = {
        'name': 'registry',
        'collection': collection,
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
                'help_text': 'The {resource} for which to get the IAM policy.',
                'spec': spec,
            },
        },
    }
    return data

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'],
        self.MakeCommandData(brief=brief, description=description))
    self.assertTrue(issubclass(command, calliope_base.ListCommand))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.ListCommand))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testAdditionalArgsHook(self):
    d = yaml_command_schema.CommandData(
        'get_iam_policy', self.MakeCommandData())
    additional_args_mock = mock.MagicMock()
    side_effect = [calliope_base.Argument('--foo', help='Auxilio aliis.')]
    additional_args_mock.side_effect = lambda: side_effect
    d.arguments.additional_arguments_hook = additional_args_mock
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'REGISTRY', '--region', '--filter', '--sort-by',
                    '--page-size', '--limit', '--foo')

  def testRun(self):
    self.Expect()
    d = yaml_command_schema.CommandData(
        'get_iam_policy', self.MakeCommandData())
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'REGISTRY', '--region', '--filter', '--sort-by',
                    '--page-size', '--limit')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i'])
    self.assertEqual(result, {'etag': 'ACAB'})
    self.AssertOutputEquals('etag: ACAB\n')

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
    d = yaml_command_schema.CommandData(
        'get_iam_policy', self.MakeCommandData())
    d.response = yaml_command_schema.Response(
        {'error': {'field': 'b.error',
                   'code': 'code',
                   'message': 'message'}})
    cli = self.MakeCLI(d)
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i'])
    self.AssertErrContains('Code: [10] Message: [message]')


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

  def Expect(self, instance='i', response=None):
    set_iam_policy_request = self.messages.SetIamPolicyRequest(
        policy=self.policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=set_iam_policy_request),
        response=response or self.policy)

  def MakeCommandData(self, brief=None, description=None, notes=None,
                      params=None):
    collection = 'cloudiot.projects.locations.registries'
    spec = {
        'name': 'registry',
        'collection': collection,
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

  def MakeMlCommandData(self, brief=None, description=None, notes=None,
                        params=None):
    collection = 'ml.projects.models'
    spec = {
        'name': 'model',
        'collection': collection,
        'attributes': [
            {
                'parameter_name': 'projectsId',
                'attribute_name': 'project',
                'help': 'The name of the Project.',
            },
            {
                'parameter_name': 'modelsId',
                'attribute_name': 'model',
                'help': 'The name of the Model.',
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

  def testRun(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))
    self.Expect()
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeCommandData())
    cli = self.MakeCLI(d)
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
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeCommandData())
    cli = self.MakeCLI(d)
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
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeCommandData())
    cli = self.MakeCLI(d)
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
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeMlCommandData())
    o = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    d.iam = o
    cli = self.MakeCLI(d)
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
        'set_iam_policy', self.MakeCommandData())

    o = yaml_command_schema.IamData(
        {'message_type_overrides': {'policy': 'FuBarPolicy'}})
    d.iam = o
    cli = self.MakeCLI(d)
    with self.assertRaisesRegex(ValueError,
                                r'Policy type \[FuBarPolicy\] not found.'):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'],
        self.MakeCommandData(brief=brief, description=description))
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'get_iam_policy'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testRunWithResponseErrorHandler(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))

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
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeCommandData())
    d.response = yaml_command_schema.Response(
        {'error': {'field': 'b.error',
                   'code': 'code',
                   'message': 'message'}})
    cli = self.MakeCLI(d)
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])
    self.AssertErrContains('Code: [10] Message: [message]')

if __name__ == '__main__':
  base.main()
