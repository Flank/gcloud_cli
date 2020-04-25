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


"""Tests for the yaml command translator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import resources
from tests.lib.command_lib.util.apis import base
from tests.lib.command_lib.util.apis import yaml_command_base

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
    d.hidden = True
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

  def testCommandBuilerWithGoogleAuth(self):
    # google-auth is not used by default.
    cd = self.MakeCommandData()
    yaml_command_translator.CommandBuilder(
        yaml_command_schema.CommandData('describe', cd),
        ['abc', 'xyz', 'describe'])
    self.methods_mock.assert_called_once_with(
        'foo.instances', api_version=None, use_google_auth=False)
    self.methods_mock.reset_mock()

    # google-auth will be used if the command data demands so.
    cd['request']['use_google_auth'] = True
    yaml_command_translator.CommandBuilder(
        yaml_command_schema.CommandData('describe', cd),
        ['abc', 'xyz', 'describe'])
    self.methods_mock.assert_called_once_with(
        'foo.instances', api_version=None, use_google_auth=True)

  def testUnknownCommandType(self):
    cb = yaml_command_translator.CommandBuilder(
        yaml_command_schema.CommandData('describe', self.MakeCommandData()),
        ['abc', 'xyz', 'describe'])
    cb.spec.command_type = 'bogus'
    with self.assertRaisesRegex(
        ValueError,
        r'Command \[abc xyz describe] unknown command type \[bogus]\.'):
      cb.Generate()


class GenericCommandTests(yaml_command_base.CommandTestsBase):

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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async',
                    '--tags')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i',
                          '--tags', 'foo,bar'])
    self.AssertOutputEquals('foo: bar\n')
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [projects/p/zones/z/operations/operation-12345] '
        'to complete')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    data = self.MakeCommandData(is_async='zoneOperations')
    data['request']['method'] = 'setTags'
    data['arguments']['params'] = [
        {'api_field': 'tags.items', 'arg_name': 'tags',
         'help_text': 'the tags'}]
    d = yaml_command_schema.CommandData('set-tags', data)
    d.async_.request_issued_message = 'Test message: [{__name__}]'
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
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
        'Test message: [i]\n'
        'Check operation [projects/p/zones/z/operations/operation-12345] for '
        'status.')
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


class AsyncPollerTests(yaml_command_base.CommandTestsBase):

  def testIsDone(self):
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.async_.state.field = 'status'
    d.async_.error.field = 'error'
    d.async_.state.success_values = ['DONE']
    d.async_.state.error_values = ['ERROR']

    class Op(object):

      def __init__(self):
        self.status = None
        self.error = None

    op = Op()
    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
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
        selfLink='https://compute.googleapis.com/compute/v1/projects/p/zones/z/'
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
    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

    # Test operations api version override.
    d.request.api_version = 'v2'
    d.async_.api_version = 'v1'
    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

    # Intentionally swapping zone and project to test the remapping.
    d.async_.operation_get_method_params = {
        'project': 'zone', 'zone': 'project', 'operation': 'operation'}
    # Swap project and zone in the reference as well so it ends up being the
    # same request.
    op_ref = resources.REGISTRY.Parse(
        'operation-12345', params={'project': 'z', 'zone': 'p'},
        collection='compute.zoneOperations')
    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
    result = poller.Poll(op_ref)
    self.assertEqual(result, running_response)

  def testGetResultNoExtract(self):
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))

    class Result(object):

      name = 'foo'

    o = Result()

    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
    self.assertEqual(o, poller.GetResult(o))

    # Doesn't return result when explicitly disabled even if resource ref is
    # valid.
    d.async_.extract_resource_result = False
    poller = yaml_command_translator.AsyncOperationPoller(d, object(), None)
    self.assertEqual(o, poller.GetResult(o))

    # Test extracting a specific attribute from the operation.
    d.async_.result_attribute = 'name'
    poller = yaml_command_translator.AsyncOperationPoller(d, None, None)
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
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
    self.assertEqual(response, poller.GetResult(None))

    # Test extracting a specific attribute from the result.
    d.async_.result_attribute = 'foo.name'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
    self.assertEqual('bar', poller.GetResult(None))

    # Test invalid attribute on the result.
    d.async_.result_attribute = 'foo.junk'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
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
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
    self.assertEqual(response, poller.GetResult(None))

    # Test extracting a specific attribute from the result.
    d.async_.result_attribute = 'foo.name'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
    self.assertEqual('bar', poller.GetResult(None))

    # Test invalid attribute on the result.
    d.async_.result_attribute = 'foo.junk'
    poller = yaml_command_translator.AsyncOperationPoller(d, resource_ref, None)
    with self.assertRaisesRegex(AttributeError,
                                r'Attribute path \[foo.junk\] not found'):
      poller.GetResult(None)


class ModifyMethodHookTests(yaml_command_base.CommandTestsBase):

  def Expect(self, instance='i', response=None):
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance=instance, zone='z', project='p'),
        response=response or {'foo': 'bar'},
        enable_type_checking=False)

  def testModifyMethodHook(self):
    self.Expect()
    command_data = self.MakeCommandData()
    d = yaml_command_schema.CommandData('describe', command_data)
    modify_method_hook = mock.MagicMock()
    modify_method_hook.return_value = 'get'
    d.request.modify_method_hook = modify_method_hook
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.assertEqual(result, {'foo': 'bar'})
    self.AssertOutputEquals('foo: bar\n')
    modify_method_hook.assert_called_once()


class ExcludeTests(yaml_command_base.CommandTestsBase):

  def testExcludeFromArguments(self):
    command_data = self.MakeCommandData(is_list=True)
    d = yaml_command_schema.CommandData('list', command_data)
    d.arguments.exclude = ['limit', 'filter']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, '--zone', '--page-size', '--sort-by')

if __name__ == '__main__':
  base.main()
