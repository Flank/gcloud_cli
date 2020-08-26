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
"""Tests for gcloud meta generate-command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
import tests.unit.surface.meta.testdata.compute_api_message_module as compute_api_message_module
import tests.unit.surface.meta.testdata.fake_api_message_module as fake_api_message_module
import tests.unit.surface.meta.testdata.fake_small_api_message_module as fake_small_api_message_module


FakeCollectionInfo = collections.namedtuple('FakeCollectionInfo', [
    'api_name', 'api_version', 'base_url', 'docs_url', 'name', 'path',
    'flat_paths', 'params', 'enable_uri_parsing'
])

COMPUTE_INSTANCES_INFO = FakeCollectionInfo(
    api_name='compute',
    api_version='v1',
    base_url='https://compute.googleapis.com/compute/v1/',
    docs_url='https://developers.google.com/compute/docs/reference/latest/',
    name='instances',
    path='projects/{project}/zones/{zone}/instances/{instance}',
    flat_paths={},
    params=['project', 'zone', 'instance'],
    enable_uri_parsing=True
)

FAKEAPI_ICECREAM_INFO = FakeCollectionInfo(
    api_name='fakeapi',
    api_version='v1',
    base_url='https://fakeapi.googleapis.com/v1',
    docs_url='https://cloud.google.com/fake-api/',
    name='icecreams',
    path='{+name}',
    flat_paths={'': 'projects/{projectsId}/icecreams/{icecreamsId}'},
    params=['name'],
    enable_uri_parsing=True
    )

FAKEAPI_ICECREAM_INFO_ALPHA = FakeCollectionInfo(
    api_name='fakeapi',
    api_version='v1alpha',
    base_url='https://fakeapi.googleapis.com/v1alpha',
    docs_url='https://cloud.google.com/fake-api/',
    name='icecreams',
    path='{+name}',
    flat_paths={'': 'projects/{projectsId}/icecreams/{icecreamsId}'},
    params=['name'],
    enable_uri_parsing=True
    )

SUPPORTED_COMMANDS = [
    'get-iam-policy', 'set-iam-policy', 'list', 'describe', 'create', 'delete'
]


class GenerateCommandTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_prompt = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)

  def testGenerateCommandNone(self):
    mock_file_writer = self.StartObjectPatch(files, 'FileWriter')
    command = ['meta', 'generate-command']
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(command)
    mock_file_writer.assert_not_called()

  def testGenerateCommandBadArgs(self):
    output_dir = self.temp_path
    mock_file_writer = self.StartObjectPatch(files, 'FileWriter')
    command = [
        'meta', 'generate-command', 'a.collection.that.does.not.exist',
                '--output-dir', output_dir
    ]
    with self.assertRaises(apis_util.UnknownAPIError):
      self.Run(command)
    self.mock_prompt.assert_not_called()
    mock_file_writer.assert_not_called()

  def testGenerateExistingCommandFilesOverwrite(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances', '--output-dir',
        output_dir
    ]
    # iterate through all the possible templates here
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    with files.FileWriter(yaml_filepath, create_path=True) as f:
      f.write('throwaway')
    self.Run(command)
    self.assertEqual(self.mock_prompt.call_count, 1)
    self.AssertFileExists(yaml_filepath)

  def testGenerateExistingCommandsNoOverwrite(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances',
        '--output-dir', output_dir
    ]
    file_contents = 'throwaway'
    for command_type in SUPPORTED_COMMANDS:  # make all command types pre-exist
      yaml_filename = command_type.replace('-', '_') + '.yaml'
      yaml_filepath = os.path.join(output_dir, yaml_filename)
      with files.FileWriter(yaml_filepath, create_path=True) as f:
        f.write(file_contents)
    mock_file_writer = self.StartObjectPatch(files, 'FileWriter')
    self.mock_prompt.return_value = False
    self.Run(command)
    self.assertEqual(self.mock_prompt.call_count, len(SUPPORTED_COMMANDS))
    if mock_file_writer.call_count > 0:
      self.assertEqual(mock_file_writer.call_count,
                       1)  # only write should be survey response
    else:
      self.assertEqual(self.mock_prompt.call_count, 0)  # no survey, no write
    self.AssertFileEquals(file_contents, yaml_filepath)

  def testGenerateNewCommandsSomeSupported(self):
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_small_api_message_module)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    api_support_commands = ['get-iam-policy', 'list']
    commands_should_not_exist = []
    commands_should_exist = []
    self.Run(command)
    for command_type in SUPPORTED_COMMANDS:
      yaml_filename = command_type.replace('-', '_') + '.yaml'
      yaml_filepath = os.path.join(output_dir, yaml_filename)
      if command_type not in api_support_commands:
        commands_should_not_exist.append(yaml_filepath)
      else:
        commands_should_exist.append(yaml_filepath)
    self.Run(command)
    for yaml_filepath in commands_should_exist:
      self.AssertFileExists(yaml_filepath)
    for yaml_filepath in commands_should_not_exist:
      self.AssertFileNotExists(yaml_filepath)

  def testGenerateNewCommandsAllSupported(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    commands_should_exist = []
    self.Run(command)
    for command_type in SUPPORTED_COMMANDS:
      yaml_filename = command_type.replace('-', '_') + '.yaml'
      yaml_filepath = os.path.join(output_dir, yaml_filename)
      commands_should_exist.append(yaml_filepath)
    self.Run(command)
    for yaml_filepath in commands_should_exist:
      self.AssertFileExists(yaml_filepath)

  def testGenerateScenarioTestSkeleton(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.scenario.yaml')
    self.Run(command)
    self.AssertFileExists(yaml_filepath)

  def testGenerateGetIamPolicy(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances', '--output-dir',
        output_dir
    ]
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=COMPUTE_INSTANCES_INFO)
    self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=compute_api_message_module)
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Get the IAM policy for the instance.'
    expected_example_command = '$ {command} my-instance --zone=my-zone'
    expected_request_lines = [
        'request:', 'collection: compute.instances',
        'api_version: v1',
        'use_relative_name: false'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: The instance for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.compute.resources:instance'
    ]
    expected_iam_lines = [
        'iam:', 'enable_condition: true', 'policy_version: 3',
        'get_iam_policy_version_path: '
        'getIamPolicyRequest.options.requestedPolicyVersion'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)
    for expected_iam_line in expected_iam_lines:
      self.AssertFileContains(expected_iam_line, yaml_filepath)

  def testGenerateGetIamPolicyAlpha(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO_ALPHA)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    get_iam_yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA]'
    expected_help_text = 'brief: Get the IAM policy for the icecream.'
    expected_example_command = '$ {command} my-icecream'
    expected_request_lines = [
        'request:', 'collection: fakeapi.projects.icecream',
        'api_version: v1alpha',
        'use_relative_name: true'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: The icecream for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.fakeapi.resources:icecream'
    ]
    expected_iam_lines = [
        'iam:', 'enable_condition: true', 'policy_version: 3',
        'get_iam_policy_version_path: '
        'getIamPolicyRequest.options.requestedPolicyVersion'
    ]
    self.AssertFileContains(release_tracks, get_iam_yaml_filepath)
    self.AssertFileContains(expected_help_text, get_iam_yaml_filepath)
    self.AssertFileContains(expected_example_command, get_iam_yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, get_iam_yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, get_iam_yaml_filepath)
    for expected_iam_line in expected_iam_lines:
      self.AssertFileContains(expected_iam_line, get_iam_yaml_filepath)

  def testGenerateSetIamPolicy(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances', '--output-dir',
        output_dir
    ]
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=COMPUTE_INSTANCES_INFO)
    self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=compute_api_message_module)
    yaml_filepath = os.path.join(output_dir, 'set_iam_policy.yaml')
    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Set the IAM policy for the instance.'
    expected_example_command = ('$ {command} my-instance --zone=my-zone '
                                'policy.json')
    expected_request_lines = [
        'request:', 'collection: compute.instances', 'api_version: v1',
        'use_relative_name: false'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: The instance for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.compute.resources:instance'
    ]
    expected_iam_lines = [
        'iam:', 'enable_condition: true', 'policy_version: 3'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)
    for expected_iam_line in expected_iam_lines:
      self.AssertFileContains(expected_iam_line, yaml_filepath)

  def testGenerateDescribe(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances', '--output-dir',
        output_dir
    ]
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=COMPUTE_INSTANCES_INFO)
    self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=compute_api_message_module)
    yaml_filepath = os.path.join(output_dir, 'describe.yaml')
    self.Run(command)
    self.AssertFileExists(yaml_filepath)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Show details about the instance.'
    expected_example_command = '$ {command} my-instance --zone=my-zone'
    expected_request_lines = [
        'request:', 'collection: compute.instances',
        'api_version: v1'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: The instance you want to describe.',
        'spec: !REF googlecloudsdk.command_lib.compute.resources:instance'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)

  def testGenerateList(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    yaml_filepath = os.path.join(output_dir, 'list.yaml')
    self.Run(command)
    self.AssertFileExists(yaml_filepath)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: List Fakeapi icecreams.'
    expected_example_command = '$ {command}'
    expected_request_lines = [
        'request:', 'fakeapi.projects.icecreams',
        'api_version: v1'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: Parent Fakeapi project to list all contained Fakeapi '
        'icecreams.',
        'spec: !REF googlecloudsdk.command_lib.fakeapi.resources:project'
    ]
    expected_output_lines = [
        'output:', 'format:', 'table(', 'name.basename():label=NAME',
        'createTime:label=CREATETIME', 'labels:label=LABELS',
        'replication:label=REPLICATION'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)
    for expected_output_line in expected_output_lines:
      self.AssertFileContains(expected_output_line, yaml_filepath)

  def testGenerateCreate(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    yaml_filepath = os.path.join(output_dir, 'create.yaml')
    self.Run(command)
    self.AssertFileExists(yaml_filepath)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Create a Fakeapi icecream.'
    expected_example_command = '$ {command} my-icecream'
    expected_request_lines = [
        'request:', 'fakeapi.projects.icecreams',
        'api_version: v1'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: Fakeapi icecream to create.',
        'spec: !REF googlecloudsdk.command_lib.fakeapi.resources:icecream'
    ]
    expected_create_params = [
        '- arg_name: create-time', 'api_field: icecream.createTime',
        'Default createTime used by this icecream.',
        '- arg_name: labels', 'api_field: icecream.labels',
        'Default labels used by this icecream.',
        '- arg_name: replication', 'api_field: icecream.replication',
        'Default replication used by this icecream.',
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)
    for expected_create_param in expected_create_params:
      self.AssertFileContains(expected_create_param, yaml_filepath)

  def testGenerateDelete(self):
    self.fake_message_module = self.StartObjectPatch(
        apis, 'GetMessagesModule', return_value=fake_api_message_module)
    self.fake_collection_info = self.StartObjectPatch(
        resources.Registry,
        'GetCollectionInfo',
        return_value=FAKEAPI_ICECREAM_INFO)
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'fakeapi.projects.icecreams',
        '--output-dir', output_dir
    ]
    yaml_filepath = os.path.join(output_dir, 'delete.yaml')
    self.Run(command)
    self.AssertFileExists(yaml_filepath)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Delete a Fakeapi icecream.'
    expected_example_command = '$ {command} my-icecream'
    expected_request_lines = [
        'request:', 'fakeapi.projects.icecreams',
        'api_version: v1'
    ]
    expected_resource_lines = [
        'resource:',
        'help_text: Fakeapi icecream to delete.',
        'spec: !REF googlecloudsdk.command_lib.fakeapi.resources:icecream'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)

if __name__ == '__main__':
  cli_test_base.main()
