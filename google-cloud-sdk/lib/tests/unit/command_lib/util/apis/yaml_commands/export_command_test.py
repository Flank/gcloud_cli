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


import os
import tempfile

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class ExportCommandTests(yaml_command_base.CommandTestsBase):

  def Expect(self, instance='i', response=None):
    """Sets client mock to expect Get request and return compute instance."""
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance=instance, zone='z', project='p'),
        response=self.messages.Instance(name='test'),
        enable_type_checking=False)

  def StartExportMocking(self):
    """Mocks GetSchemaPath method to prevent not finding file."""
    get_schema_mock = self.StartObjectPatch(export_util, 'GetSchemaPath')
    get_schema_mock.side_effect = [None]

  def testGeneration(self):
    """Tests export command generation."""
    global_mock = self.StartObjectPatch(yaml_command_translator.CommandBuilder,
                                        '_ConfigureGlobalAttributes')
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'export'], self.MakeCommandData())
    self.assertTrue(issubclass(command, calliope_base.ExportCommand))
    global_mock.assert_called_once_with(command)

  def testRunNoDestination(self):
    """Tests command exporting to stdout."""
    self.Expect()
    self.StartExportMocking()

    data = self.MakeCommandData('compute.instances')
    d = yaml_command_schema.CommandData('export', data)

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--destination')

    cli.Execute(['command', '--project', 'p', '--zone', 'z', 'i'])
    self.AssertOutputEquals('name: test\n')

  def testRunWithDestination(self):
    """Tests command using --destinatoin flag."""
    self.Expect()
    self.StartExportMocking()
    data = self.MakeCommandData('compute.instances')
    d = yaml_command_schema.CommandData('export', data)

    # Set up output file for command to export to.
    temp_path = tempfile.mkdtemp(dir=self.root_path)
    self.Touch(temp_path, 'test.yaml')
    output_path = os.path.join(temp_path, 'test.yaml')

    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'INSTANCE', '--zone', '--destination')

    cli.Execute([
        'command', '--project', 'p', '--zone', 'z', '--destination',
        output_path, 'i'
    ])
    self.AssertErrContains('Exported [test] to \'{}\''.format(output_path))
    self.AssertFileContains('name: test', output_path)
