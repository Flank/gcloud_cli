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


class WaitCommandTests(yaml_command_base.CommandTestsBase):

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
        'Waiting for operation [projects/p/zones/z/operations/operation-12345] '
        'to complete')
    self.AssertOutputEquals("""
id: '12345'
name: operation-12345
selfLink: https://www.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
status: DONE
""".lstrip('\n'), normalize_space=True)
    self.assertEqual(result, done_response)
