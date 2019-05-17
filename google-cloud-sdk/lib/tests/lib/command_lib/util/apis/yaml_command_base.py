# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Helpers for declarative commands tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import cli as calliope_cli
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib import sdk_test_base
from tests.lib import test_case


class MockTranslator(command_loading.YamlCommandTranslator):
  """A sub that lets us run the generator without having to write command files."""

  def __init__(self, spec, name='describe'):
    self.spec = spec
    self.name = name

  def Translate(self, path, command_data):
    return yaml_command_translator.CommandBuilder(
        self.spec, ['abc', 'xyz', self.name]).Generate()


class CommandTestsBase(sdk_test_base.WithFakeAuth,
                       sdk_test_base.WithOutputCapture, test_case.WithInput):
  """Test base for first class support declarative commands."""

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
      spec = {
          'name':
              'zone',
          'collection':
              'compute.zones',
          'attributes': [{
              'parameter_name': 'zone',
              'attribute_name': 'zone',
              'help': 'the zone'
          }]
      }
    else:
      spec = {
          'name':
              'instance',
          'collection':
              'compute.instances',
          'request_id_field':
              'instance.name',
          'attributes': [
              {
                  'parameter_name': 'zone',
                  'attribute_name': 'zone',
                  'help': 'the zone'},
              {
                  'parameter_name': 'instance',
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
          'collection': '.'.join(collection.split('.')[:-1]) + '.zoneOperations'
      }
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
        },
                       {
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
        id=12345,
        name='operation-12345',
        selfLink='https://www.googleapis.com/compute/v1/projects/p/zones/z/'
        'operations/operation-12345',
        error=None,
        status=self.messages.Operation.StatusValueValuesEnum.RUNNING)
    done_response = self.messages.Operation(
        id=12345,
        name='operation-12345',
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
    command_data.response = yaml_command_schema.Response(
        {'error': {
            'field': 'b.error',
            'code': 'code',
            'message': 'message'
        }})
    cli = self.MakeCLI(command_data)
    with self.assertRaises(SystemExit):
      cli.Execute(execute_params or [])
    self.AssertErrContains('Code: [10] Message: [message]')
