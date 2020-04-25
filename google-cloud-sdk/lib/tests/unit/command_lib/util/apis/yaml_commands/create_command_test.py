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

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base

import mock


class CreateCommandTests(yaml_command_base.CommandTestsBase):

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

  def testCreateWithLabels(self):
    running_response, _ = self.OperationResponses()
    labels_cls = self.messages.Instance.LabelsValue
    additional_property_cls = labels_cls.AdditionalProperty
    self.mocked_client.instances.Insert.Expect(
        self.messages.ComputeInstancesInsertRequest(
            instance=self.messages.Instance(
                name='i',
                labels=labels_cls(additionalProperties=[
                    additional_property_cls(key='k1', value='v1')
                ])),
            zone='z',
            project='p'),
        response=running_response)
    command_data = self.MakeCommandData(
        is_create=True, is_async='zoneOperations')
    command_data['arguments']['labels'] = {'api_field': 'instance.labels'}
    d = yaml_command_schema.CommandData('create', command_data)
    d.request.method = 'insert'
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    result = cli.Execute([
        'command', '--project', 'p', '--zone', 'z', 'i', '--async', '--labels',
        'k1=v1'
    ])
    self.AssertOutputEquals('')
    self.AssertErrContains('Create request issued for: [i]\n'
                           'Check operation [projects/p/zones/z/operations/'
                           'operation-12345] for status.')
    self.AssertErrNotContains('Created instance [i]')
    self.assertEqual(result, running_response)

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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Create request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [projects/p/zones/z/operations/operation-12345] '
        'to complete')
    self.AssertErrContains('Created instance [i]')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'create', self.MakeCommandData(is_create=True,
                                       is_async='zoneOperations'))
    d.request.method = 'insert'
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z', 'i', '--async'])
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Create request issued for: [i]\n'
        'Check operation [projects/p/zones/z/operations/operation-12345] '
        'for status.')
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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    d.async_.extract_resource_result = False
    d.async_.result_attribute = 'targetLink'

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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    d.arguments.resource.display_name_hook = lambda x, y: 'display name'
    cli = self.MakeCLI(d)
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('Create request issued for: [display name]')
    self.AssertErrContains('Created instance [display name]')

  def testWithParentResource(self):
    m = self.functions_messages
    expected_function = m.CloudFunction(name='myfunction')
    expected_result = encoding.DictToMessage(
        encoding.MessageToDict(expected_function),
        m.Operation.ResponseValue)
    done_response = m.Operation(done=True, response=expected_result)
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
    d.request.display_resource_type = 'function'

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'LOCATION')
    result = cli.Execute(
        ['command', '--project', 'p', 'l'])
    self.assertEqual(done_response, result)
    self.AssertErrContains('Created {} [{}].'.format(
        d.request.display_resource_type, expected_function.name))
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
        'extract_resource_result': False}
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
    d.request.display_resource_type = 'function'
    d.response.result_attribute = 'response'

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'LOCATION', '--async', '--no-async')
    result = cli.Execute(
        ['command', '--project', 'p', 'l'])
    result_function = encoding.DictToMessage(
        encoding.MessageToDict(result),
        m.CloudFunction)
    self.assertEqual(expected_function, result_function)
    self.AssertErrContains('Create request issued')
    self.AssertErrContains('Created {} [{}].'.format(
        d.request.display_resource_type, expected_function.name))
    self.AssertErrNotContains('issued for')
