# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for command_lib.iam.iam_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import copy
import json

from apitools.base.py import encoding

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from surface.config import set as surface_config_set
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case
from tests.lib.calliope import util


class AccountNameValidatorTest(subtests.Base):

  def Good(self, name):
    self.Run(name, name, depth=2)

  def Bad(self, name):
    self.Run(None, name, depth=2, exception=arg_parsers.ArgumentTypeError)

  def RunSubTest(self, name):
    return iam_util.AccountNameValidator()(name)

  def testInvalidNames(self):
    self.Bad('0cannotstartwithnumber')
    self.Bad('a' * 5)  # Must have at least 6 characters
    self.Bad('a' * 31)  # Must have at most 30 characters
    self.Bad('cannotendwithhyphen-')
    self.Bad('-cannotstartwithhyphen')

  def testValidNames(self):
    self.Good('a' * 6)  # May have 6 characters
    self.Good('a' * 30)  # May have 30 characters
    self.Good('a-aa-a')  # May have hyphens in the middle
    self.Good('aaaaa1')  # May end with a number


class GetIamAccountFormatValidatorTest(subtests.Base):

  def Good(self, name):
    self.Run(name, name, depth=2)

  def Bad(self, name):
    self.Run(None, name, depth=2, exception=arg_parsers.ArgumentTypeError)

  def RunSubTest(self, name):
    return iam_util.GetIamAccountFormatValidator()(name)

  def testInvalidNames(self):
    self.Bad('a1')
    self.Bad('1a')
    self.Bad('1a1')
    self.Bad('a.c')
    self.Bad('a@a')
    self.Bad('a@a.')
    self.Bad('@a.c')
    self.Bad('@.')

  def testValidNames(self):
    self.Good('123456789876543212345')
    self.Good('example@email.com')


class IAMUtilTest(cli_test_base.CliTestBase, parameterized.TestCase):

  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1beta1')

  TEST_IAM_POLICY = messages.Policy(
      bindings=[
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/owner')],
      version=0)

  TEST_IAM_POLICY_MULTI_CONDITIONS = messages.Policy(
      bindings=[
          messages.Binding(
              members=['user:tester@gmail.com'],
              role='roles/owner',
              condition=messages.Expr(
                  expression='ip=whitelist_ip',
                  title='whitelist ip',
                  description='whitelist ip description',
              )),
          messages.Binding(
              members=['user:tester@gmail.com'],
              role='roles/tester',
              condition=messages.Expr(
                  expression='ip=blacklist_ip',
                  title='blacklist ip',
                  description='blacklist ip description',
              ))],
      version=0)

  def _GetTestIAMPolicy(self, etag=None):
    policy_msg = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                members=['user:tester@gmail.com', 'user:slick@gmail.com'],
                role='roles/owner')
        ],
        version=0)

    if etag:
      policy_msg.etag = etag

    return policy_msg

  def SetUp(self):
    self.dir = files.TemporaryDirectory()

  def _CreateIAMPolicyFile(self, etag=None, as_json=False):
    """Create a JSON or Yaml(default) IAM policy file for testing.

    Args:
      etag: boolean, If true output policy file will include an etag key.
      as_json: boolean, If true output policy file in JSON format,
      if false output Yaml

    Returns:
      The policy file name.
    """
    policy_json = json.loads(
        encoding.MessageToJson(self._GetTestIAMPolicy(etag)))

    file_name = self.RandomFileName()

    if as_json:
      policy_file_name = self.Touch(
          self.dir.path,
          name=file_name,
          contents=json.dumps(policy_json, indent=2))
    else:
      policy_file_name = self.Touch(
          self.dir.path,
          name=file_name,
          contents=yaml.dump(policy_json))

    return policy_file_name

  class DummyData(object):
    defaults = {}
    dests = []
    flag_args = []
    is_global = False
    required = []

  @staticmethod
  def getDummyArgumentInterceptor(parser):
    # Don't ask, it's magic.
    return parser_arguments.ArgumentInterceptor(
        parser=parser,
        cli_generator=surface_config_set.Set.GetCLIGenerator(),
        allow_positional=True,
        data=IAMUtilTest.DummyData())

  def testConstructUpdateMaskFromPolicy(self):
    json_str = encoding.MessageToJson(self.TEST_IAM_POLICY)
    policy_file_path = self.Touch(
        files.TemporaryDirectory().path, 'good.json', contents=json_str)
    self.assertEqual('bindings,version',
                     iam_util.ConstructUpdateMaskFromPolicy(policy_file_path))

  def testFailureConstructUpdateMaskFromPolicy(self):
    policy_file_path = self.Touch(
        files.TemporaryDirectory().path, 'bad', contents='{foo} bad {{foo}}')
    with self.assertRaises(exceptions.Error):
      iam_util.ConstructUpdateMaskFromPolicy(policy_file_path)

  def testAddArgsForAddIamPolicyBinding_Editor(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForAddIamPolicyBinding(ai)
    res = parser.parse_args(['--role=roles/editor', '--member=etest'])
    self.assertEqual(res.role, 'roles/editor')
    self.assertEqual(res.member, 'etest')

  def testAddArgsForAddIamPolicyBinding_Viewer(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForAddIamPolicyBinding(ai)
    res = parser.parse_args(['--role=roles/viewer', '--member=vtest'])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'vtest')

  def testAddArgsForRemoveIamPolicyBinding_Editor(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(ai)
    res = parser.parse_args(['--role=roles/editor', '--member=etest'])
    self.assertEqual(res.role, 'roles/editor')
    self.assertEqual(res.member, 'etest')

  def testAddArgsForRemoveIamPolicyBinding_Viewer(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(ai)
    res = parser.parse_args(['--role=roles/viewer', '--member=vtest'])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'vtest')

  def testAddArgsForAddIamPolicyBindingAddCondition(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args([
        '--role=roles/viewer', '--member=guest',
        '--condition=expression=ip=whitelist_ip,title=title_value,'
        'description=description_value'
    ])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertEqual(res.condition.get('expression'), 'ip=whitelist_ip')
    self.assertEqual(res.condition.get('title'), 'title_value')
    self.assertEqual(res.condition.get('description'), 'description_value')

  def testAddArgsForAddIamPolicyBindingAddCondition_NoneCondition(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args(
        ['--role=roles/viewer', '--member=guest', '--condition=None'])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertTrue('None' in res.condition)
    self.assertFalse('expression' in res.condition)
    self.assertFalse('title' in res.condition)
    self.assertFalse('description' in res.condition)

  def testAddArgsForAddIamPolicyBindingAddCondition_FromFile(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    condition_file = self.Touch(
        self.temp_path,
        'condition',
        contents='expression=ip=whitelist_ip,title=title_value,'
        'description=description_value')
    res = parser.parse_args([
        '--role=roles/viewer', '--member=guest',
        '--condition-from-file={}'.format(condition_file)
    ])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertEqual(
        res.condition_from_file, 'expression=ip=whitelist_ip,title=title_value,'
        'description=description_value')

  def testAddArgsForRemoveIamPolicyBindingAddCondition(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args([
        '--role=roles/viewer', '--member=guest',
        '--condition=expression=ip=whitelist_ip,title=title_value,'
        'description=description_value'
    ])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertEqual(res.condition.get('expression'), 'ip=whitelist_ip')
    self.assertEqual(res.condition.get('title'), 'title_value')
    self.assertEqual(res.condition.get('description'), 'description_value')

  def testAddArgsForRemoveIamPolicyBindingAddCondition_FromFile(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)
    condition_file = self.Touch(
        self.temp_path,
        'condition',
        contents='expression=ip=whitelist_ip,title=title_value,'
        'description=description_value')
    res = parser.parse_args([
        '--role=roles/viewer', '--member=guest',
        '--condition-from-file={}'.format(condition_file)
    ])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertEqual(
        res.condition_from_file, 'expression=ip=whitelist_ip,title=title_value,'
        'description=description_value')

  def testAddArgsForRemoveIamPolicyBindingAddCondition_All(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args(['--role=roles/viewer', '--member=guest', '--all'])
    self.assertEqual(res.role, 'roles/viewer')
    self.assertEqual(res.member, 'guest')
    self.assertEqual(res.all, True)

  @parameterized.named_parameters(
      ('condition-none', {'None': None}),
      ('condition', {'expression': 'expr_value', 'title': 'title_value'}))
  def testValidateConditionArgument_Correct(self, condition):
    iam_util.ValidateConditionArgument(condition,
                                       iam_util.CONDITION_FORMAT_EXCEPTION)

  @parameterized.named_parameters(
      ('condition_conflict', {'None': None, 'expression': 'expr_value'}),
      ('condition_incomplete', {'expression': 'expr_value'}))
  def testValidateConditionArgument_Wrong(self, condition):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*condition must be either `None` or a list of key=value pairs.*'):
      iam_util.ValidateConditionArgument(condition,
                                         iam_util.CONDITION_FORMAT_EXCEPTION)

  def testPromptChoicesForRemoveBindingFromIamPolicy(self):
    choices = iam_util.PromptChoicesForRemoveBindingFromIamPolicy(
        self.TEST_IAM_POLICY_MULTI_CONDITIONS, 'user:tester@gmail.com',
        'roles/owner')
    expected_choices = [
        'expression=ip=whitelist_ip,title=whitelist ip,'
        'description=whitelist ip description', 'all conditions'
    ]
    self.assertEqual(choices, expected_choices)

  def testPromptChoicesForAddBindingToIamPolicy(self):
    choice = iam_util.PromptChoicesForAddBindingToIamPolicy(
        self.TEST_IAM_POLICY_MULTI_CONDITIONS)
    expected_choice = ['expression=ip=blacklist_ip,title=blacklist ip,'
                       'description=blacklist ip description',
                       'expression=ip=whitelist_ip,title=whitelist ip,'
                       'description=whitelist ip description',
                       'None',
                       'Specify a new condition']
    self.assertEqual(choice, expected_choice)

  def testAddBindingToIamPolicy(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForAddIamPolicyBinding(ai)
    args = parser.parse_args(['--role=roles/editor',
                              '--member=user:etest@gmail.com'])

    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY)
    expected_policy.bindings.append(self.messages.Binding(
        members=['user:etest@gmail.com'],
        role='roles/editor'))

    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY)
    iam_util.AddBindingToIamPolicy(self.messages.Binding, actual_policy,
                                   args.member, args.role)

    self.assertEqual(actual_policy, expected_policy)

  def testBindingInPolicy(self):
    self.assertTrue(
        iam_util.BindingInPolicy(
            self.TEST_IAM_POLICY,
            'user:slick@gmail.com',
            'roles/owner'))
    self.assertFalse(
        iam_util.BindingInPolicy(
            self.TEST_IAM_POLICY,
            'user:not_in_policy@gmail.com',
            'roles/owner'))
    self.assertFalse(
        iam_util.BindingInPolicy(
            self.TEST_IAM_POLICY,
            'user:slick@gmail.com',
            'roles/not_owner'))

  def testRemoveBindingFromIamPolicy(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(ai)
    args = parser.parse_args(['--role=roles/owner',
                              '--member=user:slick@gmail.com'])

    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY)
    expected_policy.bindings[0].members.remove('user:slick@gmail.com')

    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY)
    iam_util.RemoveBindingFromIamPolicy(actual_policy,
                                        args.member, args.role)

    self.assertEqual(actual_policy, expected_policy)

  def testRemoveNonExistingBindingFromIamPolicy(self):
    policy = copy.deepcopy(self.TEST_IAM_POLICY)
    message = 'Policy binding with the specified member and role not found!'
    with self.assertRaisesRegex(iam_util.IamPolicyBindingNotFound, message):
      iam_util.RemoveBindingFromIamPolicy(policy,
                                          'user:lick@gmail.com',
                                          'roles/owner')

  def testSetIamPolicyJson(self):
    policy_file = self._CreateIAMPolicyFile(etag=b'abcd', as_json=True)
    expected_policy = self._GetTestIAMPolicy(etag=b'abcd')
    policy = iam_util.ParsePolicyFile(policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)

  def testParseIamPolicyYaml(self):
    policy_file = self._CreateIAMPolicyFile(etag=b'abcd')
    expected_policy = self._GetTestIAMPolicy(etag=b'abcd')
    policy = iam_util.ParsePolicyFile(policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)

  def testParseIamPolicyMissingEtag(self):
    policy_file = self._CreateIAMPolicyFile()
    expected_policy = self._GetTestIAMPolicy()

    self.WriteInput('Y\n')
    policy = iam_util.ParsePolicyFile(policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)

  def testParseIamPolicyMissingPolicyFile(self):
    with self.assertRaisesRegex(
        exceptions.Error,
        r'Failed to load YAML from \[fake_policy.json\]'):
      iam_util.ParsePolicyFile('fake_policy.json', self.messages.Policy)

  def testParseIamPolicyInvalidYaml(self):
    bad_file = self.Touch(self.dir.path,
                          name='bad_yaml.json',
                          contents='NOT YAML OR JSON')
    with self.assertRaisesRegex(
        gcloud_exceptions.BadFileException, r'Policy file \[.*\] is not a '
                                            'properly formatted YAML or JSON '
                                            'policy file.'):
      iam_util.ParsePolicyFile(bad_file, self.messages.Policy)

  def testParseIamPolicyInvalidEtag(self):
    bad_contents = """\
    {
    "bindings": [
    {
        "role": "roles/ml.modelOwner",
        "members": [
            "user:ibelle@google.com",
            "user:zjn@google.com"
        ]
    }],
    "etag": "ua000"
  }
    """
    bad_file = self.Touch(self.dir.path,
                          name='bad_yaml.json',
                          contents=bad_contents)
    with self.assertRaisesRegex(iam_util.IamEtagReadError,
                                r'The etag of policy file \[.*\] is not '
                                'properly formatted.'):
      iam_util.ParsePolicyFile(bad_file, self.messages.Policy)

  def testParseIamPolicyWithMask(self):
    policy_file = self._CreateIAMPolicyFile(etag=b'abcd')
    expected_policy = self._GetTestIAMPolicy(etag=b'abcd')
    policy, update_mask = iam_util.ParsePolicyFileWithUpdateMask(
        policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)
    self.assertEqual(update_mask, 'bindings,etag,version')


class LogSetIamPolicyTest(sdk_test_base.WithLogCapture):

  def testLogSetIamPolicy(self):
    iam_util.LogSetIamPolicy('my-project', 'project')
    self.AssertErrEquals('Updated IAM policy for project [my-project].\n')


class IAMUtilPolicyNoConditionTest(cli_test_base.CliTestBase,
                                   parameterized.TestCase):

  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1beta1')
  TEST_IAM_POLICY_NONE_CONDITION = messages.Policy(
      bindings=[
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/owner',
              condition=None)
      ],
      version=0)

  TEST_CONDITION = {
      'expression': 'ip=whitelist-ip',
      'title': 'whitelist ip',
      'description': 'whitelist ip description'
  }

  def testAddBindingToIamPolicyWithCondition(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    # when user does not specify --condition
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:viewer@gmail.com',
        role='roles/viewer',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    expected_policy.bindings.append(
        self.messages.Binding(
            members=['user:viewer@gmail.com'],
            role='roles/viewer',
            condition=None))
    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains('Adding binding with condition to a policy')

  def testAddBindingToIamPolicyWithCondition_Existing(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    # when user does not specify --condition
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/owner',
        condition=None)

    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    expected_policy.bindings[0].members.append('user:owner@gmail.com')

    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains('Adding binding with condition to a policy')

  def testAddBindingToIamPolicyWithCondition_WARNING(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/owner',
        condition=self.TEST_CONDITION)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    expected_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@gmail.com'],
            role='roles/owner',
            condition=self.messages.Expr(
                expression='ip=whitelist-ip',
                title='whitelist ip',
                description='whitelist ip description')))
    self.AssertErrMatches(
        'WARNING: Adding binding with condition to a policy without condition '
        'will change the behavior of add-iam-policy-binding and '
        'remove-iam-policy-binding commands.')
    self.assertEqual(actual_policy, expected_policy)

  def testRemoveBindingFromIamPolicyWithCondition(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:slick@gmail.com',
        role='roles/owner',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    expected_policy.bindings[0].members.remove('user:slick@gmail.com')
    self.assertEqual(actual_policy, expected_policy)

  def testRemoveBindingFromIamPolicyWithCondition_NotFound(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_NONE_CONDITION)
    with self.AssertRaisesExceptionMatches(
        iam_util.IamPolicyBindingNotFound,
        r'Policy binding with the specified member'
        ', role, and condition not found!'):
      iam_util.RemoveBindingFromIamPolicyWithCondition(
          policy=actual_policy,
          member='user:slick@gmail.com',
          role='roles/owner',
          condition=self.TEST_CONDITION)


class IAMUtilPolicyWithConditionTest(cli_test_base.CliTestBase,
                                     parameterized.TestCase):
  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1beta1')
  TEST_IAM_POLICY_MIX_CONDITION = messages.Policy(
      bindings=[
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/non-primitive',
              condition=messages.Expr(
                  expression='ip=whitelist_ip',
                  title='whitelist ip',
                  description='whitelist ip description',
              )),
          messages.Binding(
              members=['user:guest@gmail.com', 'user:peeker@gmail.com'],
              role='roles/viewer',
              condition=None)
      ],
      version=0)

  TEST_IAM_POLICY_MIX_CONDITION_MULTIPLE = messages.Policy(
      bindings=[
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/non-primitive',
              condition=messages.Expr(
                  expression='ip=whitelist_ip',
                  title='whitelist ip',
                  description='whitelist ip description',
              )),
          messages.Binding(
              members=['user:guest@gmail.com', 'user:peeker@gmail.com'],
              role='roles/viewer',
              condition=None),
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/non-primitive',
              condition=None),
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/non-primitive',
              condition=messages.Expr(
                  expression='expr', title='title', description='desc'))
      ],
      version=0)

  TEST_CONDITION = {
      'expression': 'ip=whitelist_ip',
      'title': 'whitelist ip',
      'description': 'whitelist ip description'
  }

  TEST_CONDITION_NEW = {
      'expression': 'ip=blacklist_ip',
      'title': 'blacklist ip',
      'description': 'blacklist ip description'
  }

  TEST_CONDITION_NONE = {
      'None': None
  }

  def testAddBindingToIamPolicyWithCondition_ErrorWhenCannotPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)

    with self.AssertRaisesExceptionMatches(
        iam_util.IamPolicyBindingIncompleteError,
        'Adding a binding without specifying a condition to a '
        'policy containing conditions is prohibited in non-interactive '
        'mode. Run the command again with `--condition=None`'):
      actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
      iam_util.AddBindingToIamPolicyWithCondition(
          self.messages.Binding,
          self.messages.Expr,
          policy=actual_policy,
          member='user:owner@gmail.com',
          role='roles/owner',
          condition=None)

  def testAddBindingToIamPolicyWithCondition_NoPrompt(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/non-primitive',
        condition=self.TEST_CONDITION)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings[0].members.append('user:owner@gmail.com')
    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains(
        'Adding binding with condition to a policy without condition')

  def testAddBindingToIamPolicyWithCondition_PromptNoneCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    self.WriteInput('2')
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/non-primitive',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@gmail.com'],
            role='roles/non-primitive',
            condition=None))
    self.assertEqual(actual_policy, expected_policy)
    err_message = json.loads(self.GetErr())
    self.assertEqual(
        err_message['prompt_string'],
        ('The policy contains bindings with conditions, so specifying a '
         'condition is required when adding a binding. '
         'Please specify a condition.'))
    choices = err_message['choices']
    self.assertEqual(len(choices), 3)
    self.assertEqual(choices[0],
                     ('expression=ip=whitelist_ip,title=whitelist ip,'
                      'description=whitelist ip description'))
    self.assertEqual(choices[1], 'None')
    self.assertEqual(choices[2], 'Specify a new condition')

  def testAddBindingToIamPolicyWithCondition_SpecifyNoneCondition(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/non-primitive',
        condition=self.TEST_CONDITION_NONE)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@gmail.com'],
            role='roles/non-primitive',
            condition=None))
    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains('The policy contains bindings with conditions')

  def testAddBindingToIamPolicyWithCondition_PromptNewCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    self.WriteInput('3')
    self.WriteInput(
        ('expression=ip=whitelist_ip,title=whitelist ip,description='
         'whitelist ip description'))
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:owner@gmail.com',
        role='roles/non-primitive',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings[0].members.append('user:owner@gmail.com')
    self.assertEqual(actual_policy, expected_policy)
    err_message = self.GetErr().split('\n', 1)
    first_prompt_json = json.loads(err_message[0])

    self.assertEqual(
        first_prompt_json['prompt_string'],
        ('The policy contains bindings with conditions, so specifying a '
         'condition is required when adding a binding. '
         'Please specify a condition.'))
    first_prompt_choices = first_prompt_json['choices']
    self.assertEqual(len(first_prompt_choices), 3)
    self.assertEqual(first_prompt_choices[0],
                     ('expression=ip=whitelist_ip,title=whitelist ip,'
                      'description=whitelist ip description'))
    self.assertEqual(first_prompt_choices[1], 'None')
    self.assertEqual(first_prompt_choices[2], 'Specify a new condition')
    self.assertEqual(
        err_message[1],
        '{"ux": "PROMPT_RESPONSE", "message": "Condition is either `None` or a '
        'list of key=value pairs. If not `None`, `expression` and `title` are '
        'required keys.\\nExample: --condition=expression=[expression],'
        'title=[title],description=[description].\\nSpecify the condition:  "}')

  def testAddBindingToIamPolicyWithCondition_NewCondition(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding,
        self.messages.Expr,
        policy=actual_policy,
        member='user:tester@gmail.com',
        role='roles/tester',
        condition=self.TEST_CONDITION_NEW)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings.append(
        self.messages.Binding(
            members=['user:tester@gmail.com'],
            role='roles/tester',
            condition=self.messages.Expr(
                expression='ip=blacklist_ip',
                title='blacklist ip',
                description='blacklist ip description',
            )))
    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains(
        'Adding binding with condition to a policy without condition')

  def testRemoveBindingFromIamPolicyWithCondition_NoPrompt(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:tester@gmail.com',
        role='roles/non-primitive',
        condition=self.TEST_CONDITION)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings[0].members.remove('user:tester@gmail.com')
    self.assertEqual(actual_policy, expected_policy)

  def testRemoveBindingFromIamPolicyWithCondition_PromptOldCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    self.WriteInput('1')
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:slick@gmail.com',
        role='roles/non-primitive',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings[0].members.remove('user:slick@gmail.com')
    self.assertEqual(actual_policy, expected_policy)
    err_message = json.loads(self.GetErr())
    self.assertEqual(err_message['prompt_string'],
                     ('The policy contains bindings with conditions, '
                      'so specifying a condition is required when removing a '
                      'binding. Please specify a condition.'))
    choices = err_message['choices']
    self.assertEqual(len(choices), 2)
    self.assertEqual(choices[0],
                     ('expression=ip=whitelist_ip,title=whitelist ip,'
                      'description=whitelist ip description'))
    self.assertEqual(choices[1], 'all conditions')

  def testRemoveBindingFromIamPolicyWithCondition_SpecifyNoneCondition(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:peeker@gmail.com',
        role='roles/viewer',
        condition=self.TEST_CONDITION_NONE)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    expected_policy.bindings[1].members.remove('user:peeker@gmail.com')
    self.assertEqual(actual_policy, expected_policy)
    self.AssertErrNotContains('The policy contains bindings with conditions')

  def testRemoveBindingFromIamPolicyWithCondition_NotFound_Prompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION)
    with self.AssertRaisesExceptionMatches(
        iam_util.IamPolicyBindingNotFound,
        r'Policy binding with the specified member and '
        'role not found!'):
      iam_util.RemoveBindingFromIamPolicyWithCondition(
          policy=actual_policy,
          member='newuser:peeker@gmail.com',
          role='roles/viewer',
          condition=None)

  def testRemoveBindingFromIamPolicyWithCondition_DeleteAll(self):
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION_MULTIPLE)
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:tester@gmail.com',
        role='roles/non-primitive',
        condition=None,
        all_conditions=True)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION_MULTIPLE)
    expected_policy.bindings[0].members.remove('user:tester@gmail.com')
    expected_policy.bindings[2].members.remove('user:tester@gmail.com')
    expected_policy.bindings[3].members.remove('user:tester@gmail.com')
    self.assertEqual(actual_policy, expected_policy)

  def testRemoveBindingFromIamPolicyWithCondition_Prompt_DeleteAll(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    actual_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION_MULTIPLE)
    self.WriteInput('4')
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy=actual_policy,
        member='user:tester@gmail.com',
        role='roles/non-primitive',
        condition=None)
    expected_policy = copy.deepcopy(self.TEST_IAM_POLICY_MIX_CONDITION_MULTIPLE)
    expected_policy.bindings[0].members.remove('user:tester@gmail.com')
    expected_policy.bindings[2].members.remove('user:tester@gmail.com')
    expected_policy.bindings[3].members.remove('user:tester@gmail.com')
    self.assertEqual(actual_policy, expected_policy)
    err_message = json.loads(self.GetErr())
    self.assertEqual(err_message['prompt_string'],
                     ('The policy contains bindings with conditions, '
                      'so specifying a condition is required when removing a '
                      'binding. Please specify a condition.'))
    choices = err_message['choices']
    expected_prompt_choices = set([
        'expression=ip=whitelist_ip,title=whitelist ip,'
        'description=whitelist ip description',
        'expression=expr,title=title,description=desc', 'None', 'all conditions'
    ])
    self.assertEqual(set(choices), expected_prompt_choices)

  @parameterized.named_parameters(
      ('YAML', 'expression: expr\ntitle: title\ndescription: desc',
       {
           'description': 'desc',
           'expression': 'expr',
           'title': 'title'
       }),
      ('JSON', '{"expression": "expr",\n"title": "title",\n"description":'
               ' "desc"}',
       {
           'description': 'desc',
           'expression': 'expr',
           'title': 'title'
       }),
      ('None', '{"None": null}',
       {
           'None': None
       }))
  def testParseYamlOrJsonCondition(self, file_content, expected_condition):
    condition = iam_util.ParseYamlOrJsonCondition(file_content)
    self.assertEqual(condition, expected_condition)

  def testParseYamlOrJsonCondition_Exception(self):
    file_content = 'expression: expr'
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*condition-from-file must be a path to a YAML or JSON file containing'
        ' the condition.*'):
      iam_util.ParseYamlOrJsonCondition(file_content)

  @parameterized.named_parameters(
      ('NoneCondition', {'None': None}, 'roles/editor'),
      ('ConditionIsNotSpecified', None, 'roles/owner'),
      ('NormalCondition', {'expression': 'expr', 'title': 'title'},
       'roles/non-primitive'),
  )
  def testValidateMutexConditionAndPrimitiveRoles(self, condition, role):
    iam_util.ValidateMutexConditionAndPrimitiveRoles(condition, role)

  def testValidateMutexConditionAndPrimitiveRoles_Error(self):
    condition = {'expression': 'expr', 'title': 'title'}
    role = 'roles/editor'
    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingInvalidError,
        'Binding with a condition and a primitive role is not allowed. '
        'Primitive roles are `roles/editor`, `roles/owner`, '
        'and `roles/viewer`.'):
      iam_util.ValidateMutexConditionAndPrimitiveRoles(condition, role)

  def testValidateAndExtractCondition_FromCondition(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args([
        '--role=roles/non-primitive', '--member=user:tester@gmail.com',
        '--condition=expression=expr,title=title,description=descr'
    ])
    condition = iam_util.ValidateAndExtractCondition(res)
    expected_condition = {
        'expression': 'expr',
        'title': 'title',
        'description': 'descr'
    }
    self.assertEqual(condition, expected_condition)

  def testValidateAndExtractCondition_FromFile(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    condition_file = self.Touch(
        self.temp_path,
        'condition',
        contents='expression: expr\ntitle: title\n'
        'description: descr')
    res = parser.parse_args([
        '--role=roles/non-primitive', '--member=user:tester@gmail.com',
        '--condition-from-file={}'.format(condition_file)
    ])
    condition = iam_util.ValidateAndExtractCondition(res)
    expected_condition = {
        'expression': 'expr',
        'title': 'title',
        'description': 'descr'
    }
    self.assertEqual(condition, expected_condition)

  def testValidateAndExtractConditionMutex_PrimitiveRole(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args([
        '--role=roles/editor', '--member=user:tester@gmail.com',
        '--condition=expression=expr,title=title,description=descr'
    ])
    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingInvalidError,
        r'.*Binding with a condition and a primitive role is not allowed.*'):
      iam_util.ValidateAndExtractConditionMutexRole(res)

  def testValidateAndExtractConditionMutex_NonPrimitiveRole(self):
    parser = util.ArgumentParser()
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)
    res = parser.parse_args([
        '--role=roles/non-primitive', '--member=user:tester@gmail.com',
        '--condition=expression=expr,title=title,description=descr'
    ])
    condition = iam_util.ValidateAndExtractConditionMutexRole(res)
    expected_condition = {
        'expression': 'expr',
        'title': 'title',
        'description': 'descr'
    }
    self.assertEqual(condition, expected_condition)


if __name__ == '__main__':
  test_case.main()
