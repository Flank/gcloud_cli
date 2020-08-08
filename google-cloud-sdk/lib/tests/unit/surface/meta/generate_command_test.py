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

from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base


FakeCollectionInfo = collections.namedtuple(
    'FakeCollectionInfo',
    ['api_name', 'api_version', 'base_url', 'docs_url', 'name', 'path',
     'flat_paths', 'params', 'enable_uri_parsing'])


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
    mock_file_writer = self.StartObjectPatch(files, 'FileWriter')
    command = [
        'meta', 'generate-command', 'a.collection.that.does.not.exist'
    ]
    with self.assertRaises(apis_util.UnknownAPIError):
      self.Run(command)
    self.mock_prompt.assert_not_called()
    mock_file_writer.assert_not_called()

  def testGenerateExistingCommandOverwrite(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances',
        '--output-dir', output_dir
    ]
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    with files.FileWriter(yaml_filepath, create_path=True) as f:
      f.write('throwaway')
    self.Run(command)
    self.assertEqual(self.mock_prompt.call_count, 1)
    self.AssertFileExists(yaml_filepath)

  def testGenerateExistingCommandNoOverwrite(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances',
        '--output-dir', output_dir
    ]
    file_contents = 'throwaway'
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    with files.FileWriter(yaml_filepath, create_path=True) as f:
      f.write(file_contents)
    mock_file_writer = self.StartObjectPatch(files, 'FileWriter')
    self.mock_prompt.return_value = False
    self.Run(command)
    if self.mock_prompt.call_count > 0:
      self.assertEqual(self.mock_prompt.call_count, 1)
      self.assertEqual(mock_file_writer.call_count,
                       1)  # only write should be survey response
    else:
      self.assertEqual(self.mock_prompt.call_count, 0)  # no survey, no write
    self.AssertFileEquals(file_contents, yaml_filepath)

  def testGenerateNewCommandContents(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'compute.instances', '--output-dir',
        output_dir
    ]
    compute_collection_info = FakeCollectionInfo(
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
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=compute_collection_info)
    yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')
    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Get the IAM policy for the instance.'
    expected_example_command = '$ {command} my-instance --zone=my-zone'
    expected_request_lines = [
        'request:', 'collection: compute.instances', 'use_relative_name: false',
        'api_version: v1'
    ]
    expected_resource_lines = [
        ' resource:',
        'help_text: The instance for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.compute.resources:instance'
    ]
    self.AssertFileContains(release_tracks, yaml_filepath)
    self.AssertFileContains(expected_help_text, yaml_filepath)
    self.AssertFileContains(expected_example_command, yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, yaml_filepath)

  def testGenerateAnotherNewCommandContents(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'secretmanager.projects.secrets',
        '--output-dir', output_dir
    ]
    secret_collection_info = FakeCollectionInfo(
        api_name='secretmanager',
        api_version='v1',
        base_url='https://secretmanager.googleapis.com/v1/',
        docs_url='https://cloud.google.com/secret-manager/',
        name='projects.secrets',
        path='{+name}',
        flat_paths={'': 'projects/{projectsId}/secrets/{secretsId}'},
        params=['name'],
        enable_uri_parsing=True
        )
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=secret_collection_info)
    get_iam_yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')

    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA, BETA, GA]'
    expected_help_text = 'brief: Get the IAM policy for the secret.'
    expected_example_command = '$ {command} my-secret'
    expected_request_lines = [
        'request:', 'collection: secretmanager.projects.secrets',
        # 'use_relative_name: true',
        'api_version: v1'
    ]
    expected_resource_lines = [
        ' resource:',
        'help_text: The secret for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.secretmanager.resources:secret'
    ]
    self.AssertFileContains(release_tracks, get_iam_yaml_filepath)
    self.AssertFileContains(expected_help_text, get_iam_yaml_filepath)
    self.AssertFileContains(expected_example_command, get_iam_yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, get_iam_yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, get_iam_yaml_filepath)

  def testGenerateNewAlphaCommandContents(self):
    output_dir = self.temp_path
    command = [
        'meta', 'generate-command', 'candyshop.projects.lollipops',
        '--output-dir', output_dir
    ]
    candy_collection_info = FakeCollectionInfo(
        api_name='candyshop',
        api_version='v1alpha',
        base_url='https://candyshop.googleapis.com/v1alpha',
        docs_url='https://cloud.google.com/candy-shop/',
        name='lollipops',
        path='{+name}',
        flat_paths={'': 'projects/{projectsId}/secrets/{secretsId}'},
        params=['name'],
        enable_uri_parsing=True
        )
    self.StartObjectPatch(resources.Registry,
                          'GetCollectionInfo',
                          return_value=candy_collection_info)
    get_iam_yaml_filepath = os.path.join(output_dir, 'get_iam_policy.yaml')

    self.Run(command)
    self.AssertDirectoryExists(output_dir)
    release_tracks = '[ALPHA]'
    expected_help_text = 'brief: Get the IAM policy for the lollipop.'
    expected_example_command = '$ {command} my-lollipop'
    expected_request_lines = [
        'request:', 'collection: candyshop.projects.lollipop',
        # 'use_relative_name: true',
        'api_version: v1alpha'
    ]
    expected_resource_lines = [
        ' resource:',
        'help_text: The lollipop for which to display the IAM policy.',
        'spec: !REF googlecloudsdk.command_lib.candyshop.resources:lollipop'
    ]
    self.AssertFileContains(release_tracks, get_iam_yaml_filepath)
    self.AssertFileContains(expected_help_text, get_iam_yaml_filepath)
    self.AssertFileContains(expected_example_command, get_iam_yaml_filepath)
    for expected_request_line in expected_request_lines:
      self.AssertFileContains(expected_request_line, get_iam_yaml_filepath)
    for expected_resource_line in expected_resource_lines:
      self.AssertFileContains(expected_resource_line, get_iam_yaml_filepath)

if __name__ == '__main__':
  cli_test_base.main()
