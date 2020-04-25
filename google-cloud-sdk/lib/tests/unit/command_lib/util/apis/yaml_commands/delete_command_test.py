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
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class DeleteCommandTests(yaml_command_base.CommandTestsBase):

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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    self.WriteInput('y\n')
    result = cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You are about to delete instance [i]')
    self.AssertErrContains('Delete request issued for: [i]')
    self.AssertErrContains(
        'Waiting for operation [projects/p/zones/z/operations/operation-12345] '
        'to complete')
    self.AssertErrContains('Deleted instance [i]')
    self.assertEqual(result, done_response)

  def testRunAsync(self):
    running_response, _ = self.Expect(is_async=True)
    d = yaml_command_schema.CommandData(
        'delete', self.MakeCommandData(is_async='zoneOperations'))
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--async', '--no-async')
    self.WriteInput('y\n')
    result = cli.Execute(
        ['command', '--project', 'p', '--zone', 'z', 'i', '--async'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You are about to delete instance [i]')
    self.AssertErrContains(
        'Delete request issued for: [i]\n'
        'Check operation [projects/p/zones/z/operations/operation-12345] for '
        'status.')
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
    d.async_.response_name_field = 'selfLink'
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    cli = self.MakeCLI(d)
    self.WriteInput('y\n')
    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertErrContains('You are about to delete instance [display name]')
    self.AssertErrContains('Delete request issued for: [display name]')
    self.AssertErrContains('Deleted instance [display name]')

