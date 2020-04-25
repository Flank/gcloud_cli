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

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class UpdateCommandTests(yaml_command_base.CommandTestsBase):

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
        'name': 'instance',
        'collection': 'spanner.projects.instances',
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

  def _ExpectUpdate(
      self,
      field_mask,
      is_async=False,
      full_update=False,
      labels=False):
    instance = self.messages.Instance(
        displayName='dn' if full_update else None,
        name='projects/p/instances/i' if full_update else None,
        nodeCount=2,
    )
    if labels:
      labels_cls = self.messages.Instance.LabelsValue
      additional_property_cls = labels_cls.AdditionalProperty
      instance.labels = labels_cls(
          additionalProperties=[additional_property_cls(key='k1', value='v1')])

    running_response, _ = self._OperationResponses()
    req = self.messages.SpannerProjectsInstancesPatchRequest(
        name='projects/p/instances/i',
        updateInstanceRequest=self.messages.UpdateInstanceRequest(
            instance=instance, fieldMask=field_mask))
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
    d.async_.state.field = 'done'
    d.async_.state.success_values = [True]
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
    self.AssertErrContains('Check operation [projects/p/instances/i/'
                           'operations/o] for status.')
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
    data['update']['read_modify_update'] = True
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    d.async_.state.field = 'done'
    d.async_.state.success_values = [True]
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
    self.AssertErrContains('Check operation [projects/p/instances/i/'
                           'operations/o] for status.')
    self.AssertErrContains('Updated instance [i].\n')

  def testUpdateLabels(self):
    self._ExpectGet()
    self._ExpectUpdate(
        field_mask='nodeCount,labels',
        is_async=True,
        full_update=True,
        labels=True)
    data = self._MakeUpdateCommandData()
    data['async'] = {'collection': 'spanner.projects.instances.operations'}
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }]
    data['arguments']['labels'] = {
        'api_field': 'updateInstanceRequest.instance.labels'
    }
    data['update']['read_modify_update'] = True
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    d.async_.state.field = 'done'
    d.async_.state.success_values = [True]
    cli = self.MakeCLI(d)
    cli.Execute([
        'command', 'i', '--project', 'p', '--async', '--nodes', '2',
        '--update-labels', 'k1=v1'
    ])

    self.AssertOutputEquals(
        """
done: false
name: projects/p/instances/i/operations/o
""".lstrip('\n'),
        normalize_space=True)
    self.AssertErrContains('Request issued for: [i]')
    self.AssertErrContains('Check operation [projects/p/instances/i/'
                           'operations/o] for status.')
    self.AssertErrContains('Updated instance [i].\n')

  def testRunDisableAutoFieldMask(self):
    self._ExpectUpdate(field_mask='', is_async=True)
    data = self._MakeUpdateCommandData()
    data['async'] = {'collection': 'spanner.projects.instances.operations'}
    data['request']['method'] = 'patch'
    data['arguments']['params'] = [{
        'api_field': 'updateInstanceRequest.instance.nodeCount',
        'arg_name': 'nodes',
        'help_text': 'the number of the nodes of the instance to update'
    }]
    data['update']['disable_auto_field_mask'] = True
    d = yaml_command_schema.CommandData('update', data)
    d.request.method = 'patch'
    d.async_.state.field = 'done'
    d.async_.state.success_values = [True]
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
    self.AssertErrContains('Check operation [projects/p/instances/i/'
                           'operations/o] for status.')
    self.AssertErrContains('Updated instance [i].\n')
