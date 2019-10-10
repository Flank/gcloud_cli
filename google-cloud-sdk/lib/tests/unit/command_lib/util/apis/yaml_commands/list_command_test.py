# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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


class ListCommandTests(yaml_command_base.CommandTestsBase):

  def Expect(self):
    response = self.messages.InstanceList(
        id='projcets/foo/zones/zone1/instances',
        items=[
            self.messages.Instance(name='instance-1'),
            self.messages.Instance(name='instance-2')
        ])
    self.mocked_client.instances.List.Expect(
        self.messages.ComputeInstancesListRequest(zone='z', project='p'),
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
    self.AssertOutputEquals(
        """
https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/instance-1
https://compute.googleapis.com/compute/v1/projects/p/zones/z/instances/instance-2
""".lstrip('\n'),
        normalize_space=True)
