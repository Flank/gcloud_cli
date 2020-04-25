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
import mock


class GetIamPolicyCommandTests(yaml_command_base.CommandTestsBase):

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
