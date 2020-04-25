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
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class SetIamPolicyCommandTests(yaml_command_base.CommandTestsBase):

  def _MakePolicy(self, bindings=None, etag=b'ACAB', messages=None):
    m = messages or self.messages
    return m.Policy(bindings=bindings or [], etag=etag)

  def SetUp(self):
    self.client = apis.GetClientClass('cloudiot', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.policy = self._MakePolicy()

  def Expect(self, response=None):
    set_iam_policy_request = self.messages.SetIamPolicyRequest(
        policy=self.policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=set_iam_policy_request),
        response=response or self.policy,
        enable_type_checking=False)

  def MakeProjectCommandData(
      self,
      brief=None,
      description=None,
      notes=None,
      params=None):
    collection = 'cloudresourcemanager.projects'
    spec = {
        'name': 'project',
        'collection': collection,
        'attributes': [
            {
                'parameter_name': 'projectId',
                'attribute_name': 'project_id',
                'help': 'The name of the Project.',
            }
        ],
    }
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
                'help_text': 'The {resource} for which to set the IAM policy.',
                'spec': spec,
            },
        },
    }
    if params:
      data['arguments']['params'] = params

    return data

  @classmethod
  def SetIamPolicyTranslator(cls, brief=None, description=None):
    return yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        cls.MakeIAMCommandData(
            help_text='to set IAM policy to',
            brief=brief,
            description=description))

  def GetSetIamPolicyCLI(self):
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    return self.MakeCLI(command_data)

  def testRun(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))
    self.Expect()
    cli = self.GetSetIamPolicyCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i',
                          'myfile'])
    self.assertEqual(result, self.policy)
    self.AssertErrContains("""
    Updated IAM policy for registry [i].
    """.lstrip('\n'), normalize_space=True)
    self.AssertOutputEquals("""
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunFullPolicy(self):
    self.policy = self._MakePolicy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}])
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(self.policy, 'bindings,etag,version'))
    self.Expect()
    cli = self.GetSetIamPolicyCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', '--region', 'r', 'i',
                          'myfile'])
    self.assertEqual(result, self.policy)
    self.AssertErrContains("""
    Updated IAM policy for registry [i].
    """.lstrip('\n'), normalize_space=True)
    self.AssertOutputEquals("""
    bindings:
    - members:
    - user:mike@example.com
    - group:admins@example.com
    - domain:google.com
    role: roles/owner
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunWithUpdateMask(self):
    client = apis.GetClientClass('cloudresourcemanager', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = self._MakePolicy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}],
        messages=messages)
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(policy, 'bindings,etag,version'))
    policy.version = 0
    set_iam_policy_request = messages.SetIamPolicyRequest(
        policy=policy, updateMask='bindings,etag,version')
    mocked_client.projects.SetIamPolicy.Expect(
        messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='projects/p',
            setIamPolicyRequest=set_iam_policy_request),
        policy)
    d = yaml_command_schema.CommandData(
        'set_iam_policy', self.MakeProjectCommandData())
    cli = self.MakeCLI(d)
    self.AssertArgs(cli, 'PROJECT_ID', 'POLICY_FILE')
    result = cli.Execute(['command', 'p', 'myfile'])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for project [p].',
        normalize_space=True)
    self.AssertOutputEquals("""
      bindings:
      - members:
      - user:mike@example.com
      - group:admins@example.com
      - domain:google.com
      role: roles/owner
      etag: QUNBQg==
      version: 0
    """.lstrip('\n'), normalize_space=True)

  def testRunBadFile(self):
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          side_effect=gcloud_exceptions.BadFileException(
                              'Bad Policy File'))
    cli = self.GetSetIamPolicyCLI()
    with self.assertRaises(SystemExit):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])
    self.AssertErrContains('Bad Policy File')

  def testRunWithOverrides(self):
    client = apis.GetClientClass('ml', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = messages.GoogleIamV1Policy(
        bindings=[{'role': 'roles/owner',
                   'members': [
                       'user:mike@example.com',
                       'group:admins@example.com',
                       'domain:google.com']}],
        etag=b'ACAB',
        version=0)
    self.StartObjectPatch(iam_util, 'ParsePolicyFileWithUpdateMask',
                          return_value=(policy, 'bindings,etag,version'))
    set_iam_policy_request = messages.GoogleIamV1SetIamPolicyRequest(
        policy=policy, updateMask='bindings,etag,version')
    mocked_client.projects_models.SetIamPolicy.Expect(
        messages.MlProjectsModelsSetIamPolicyRequest(
            resource='projects/p/models/m',
            googleIamV1SetIamPolicyRequest=set_iam_policy_request),
        policy)
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(
            help_text='to set IAM policy to', another_collection=True))
    command_data.iam = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'MODEL', 'POLICY_FILE')
    result = cli.Execute(['command', '--project', 'p', 'm', 'myfile'])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for model [m].',
        normalize_space=True)
    self.AssertOutputEquals("""
      bindings:
      - members:
      - user:mike@example.com
      - group:admins@example.com
      - domain:google.com
      role: roles/owner
      etag: QUNBQg==
      version: 0
      """.lstrip('\n'), normalize_space=True)

  def testRunBadOverride(self):
    d = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))

    d.iam = yaml_command_schema.IamData({
        'message_type_overrides': {
            'policy': 'FuBarPolicy'
        }
    })
    cli = self.MakeCLI(d)
    with self.assertRaisesRegex(ValueError,
                                r'Policy type \[FuBarPolicy\] not found.'):
      cli.Execute(['command', '--project', 'p', '--region', 'r', 'i', 'myfile'])

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        self.MakeIAMCommandData(
            help_text='to set IAM policy to',
            brief=brief,
            description=description))
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual(brief, command.detailed_help.get('brief'))
    self.assertEqual(description, command.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    command = yaml_command_translator.Translator().Translate(
        ['foo', 'set_iam_policy'],
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    self.assertTrue(issubclass(command, calliope_base.Command))
    self.assertEqual('<brief>', command.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>', command.detailed_help.get('DESCRIPTION'))

  def testRunWithResponseErrorHandler(self):
    self.StartObjectPatch(
        iam_util,
        'ParsePolicyFileWithUpdateMask',
        return_value=(self.policy, 'bindings,etag,version'))
    command_data = yaml_command_schema.CommandData(
        'set_iam_policy',
        self.MakeIAMCommandData(help_text='to set IAM policy to'))
    execute_params = [
        'command', '--project', 'p', '--region', 'r', 'i', 'myfile'
    ]
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)
