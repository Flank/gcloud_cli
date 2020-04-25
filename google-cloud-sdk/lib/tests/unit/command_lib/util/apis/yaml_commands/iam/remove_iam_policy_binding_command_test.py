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
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class RemoveIamPolicyBindingCommandTests(yaml_command_base.CommandTestsBase):

  def _MakePolicy(self, bindings=None, etag=b'ACAB', messages=None):
    msgs = messages or self.messages
    return msgs.Policy(bindings=bindings or [], etag=etag)

  def _MakeBinding(self, role, members=None, messages=None):
    msgs = messages or self.messages
    return msgs.Binding(role=role, members=members)

  def SetUp(self):
    self.client = apis.GetClientClass('cloudiot', 'v1')
    self.mocked_client = apitools_mock.Client(self.client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.start_policy = self._MakePolicy(
        [self._MakeBinding('roles/viewer', ['user:admin@foo.com'])])
    self.updated_policy = self._MakePolicy()

  def _ExpectGetIamPolicy(self):
    req = self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
        resource='projects/p/locations/r/registries/i')

    self.mocked_client.projects_locations_registries.GetIamPolicy.Expect(
        request=req, response=self.start_policy)

  def _ExpectSetUpdatedIamPolicy(self, response=None):
    req = self.messages.SetIamPolicyRequest(policy=self.updated_policy)
    self.mocked_client.projects_locations_registries.SetIamPolicy.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/p/locations/r/registries/i',
            setIamPolicyRequest=req),
        response=response or self.updated_policy,
        enable_type_checking=False)

  def Expect(self, response=None):
    self._ExpectGetIamPolicy()
    self._ExpectSetUpdatedIamPolicy(response=response)

  @classmethod
  def GetRemoveIamPolicyBindingCommandTranslator(cls,
                                                 brief=None,
                                                 description=None):
    return yaml_command_translator.Translator().Translate(
        ['foo', 'remove_iam_policy_binding'],
        cls.MakeIAMCommandData(
            help_text='to remove IAM policy binding from',
            brief=brief,
            description=description))

  def GetRemoveIamPolicyBindingCLI(self):
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to remove IAM policy binding from'))
    return self.MakeCLI(command_data)

  def testGenerationExplicitHelp(self):
    brief = 'explicit brief'
    description = 'explicit description'
    translator = self.GetRemoveIamPolicyBindingCommandTranslator(
        brief, description)
    self.assertTrue(issubclass(translator, calliope_base.Command))
    self.assertEqual(brief, translator.detailed_help.get('brief'))
    self.assertEqual(description, translator.detailed_help.get('DESCRIPTION'))

  def testGenerationDefaultHelp(self):
    translator = self.GetRemoveIamPolicyBindingCommandTranslator()
    self.assertTrue(issubclass(translator, calliope_base.Command))
    self.assertEqual('<brief>', translator.detailed_help.get('brief'))
    self.assertEqual('<DESCRIPTION>',
                     translator.detailed_help.get('DESCRIPTION'))

  def testRun(self):
    self.Expect()
    cli = self.GetRemoveIamPolicyBindingCLI()
    self.AssertArgs(cli, 'REGISTRY', '--region', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ])
    self.assertEqual(result, self.updated_policy)
    self.AssertErrContains(
        """
    Updated IAM policy for registry [i].
    """.lstrip('\n'),
        normalize_space=True)
    self.AssertOutputEquals(
        """
    etag: QUNBQg==
    """.lstrip('\n'), normalize_space=True)

  def testRunWithOverrides(self):
    client = apis.GetClientClass('ml', 'v1')
    mocked_client = apitools_mock.Client(client)
    mocked_client.Mock()
    self.addCleanup(mocked_client.Unmock)
    messages = client.MESSAGES_MODULE
    policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': [
            'user:mike@example.com',
            'group:admins@example.com',
        ]
    }])
    updated_policy = messages.GoogleIamV1Policy(bindings=[{
        'role': 'roles/owner',
        'members': ['user:mike@example.com']
    }])
    self.StartObjectPatch(
        iam_util,
        'ParsePolicyFileWithUpdateMask',
        return_value=(updated_policy, 'bindings,etag,version'))

    mocked_client.projects_models.GetIamPolicy.Expect(
        messages.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/p/models/m'),
        policy)

    set_iam_policy_request = messages.GoogleIamV1SetIamPolicyRequest(
        policy=updated_policy)
    mocked_client.projects_models.SetIamPolicy.Expect(
        messages.MlProjectsModelsSetIamPolicyRequest(
            resource='projects/p/models/m',
            googleIamV1SetIamPolicyRequest=set_iam_policy_request),
        updated_policy)
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(
            help_text='to remove IAM policy binding from',
            another_collection=True))
    command_data.iam = yaml_command_schema.IamData({
        'set_iam_policy_request_path': 'googleIamV1SetIamPolicyRequest',
        'message_type_overrides': {
            'policy': 'GoogleIamV1Policy',
            'set_iam_policy_request': 'GoogleIamV1SetIamPolicyRequest'
        }
    })
    cli = self.MakeCLI(command_data)
    self.AssertArgs(cli, 'MODEL', '--member', '--role')
    result = cli.Execute([
        'command', '--project', 'p', '--project', 'p', 'm', '--role',
        'roles/owner', '--member', 'group:admins@example.com'
    ])
    self.assertEqual(result, policy)
    self.AssertErrContains(
        'Updated IAM policy for model [m].', normalize_space=True)
    self.AssertOutputEquals(
        """
      bindings:
      - members:
      - user:mike@example.com
      role: roles/owner
      """.lstrip('\n'),
        normalize_space=True)

  def testRunWithResponseErrorHandler(self):
    command_data = yaml_command_schema.CommandData(
        'remove_iam_policy_binding',
        self.MakeIAMCommandData(help_text='to remove IAM policy binding from'))
    execute_params = [
        'command', '--project', 'p', '--region', 'r', 'i', '--role',
        'roles/viewer', '--member', 'user:admin@foo.com'
    ]
    self.AssertErrorHandlingWithResponse(self.Expect, command_data,
                                         execute_params)
