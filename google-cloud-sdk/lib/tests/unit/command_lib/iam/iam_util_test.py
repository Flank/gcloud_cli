# Copyright 2016 Google Inc. All Rights Reserved.
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

import argparse
import json
import pickle

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
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case


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


class IAMUtilTest(test_case.WithInput):

  messages = apis.GetMessagesModule('cloudresourcemanager', 'v1beta1')

  TEST_IAM_POLICY = messages.Policy(
      bindings=[
          messages.Binding(
              members=[u'user:tester@gmail.com', u'user:slick@gmail.com'],
              role=u'roles/owner')],
      version=0)

  def _GetTestIAMPolicy(self, etag=None):
    policy_msg = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                members=[u'user:tester@gmail.com', u'user:slick@gmail.com'],
                role=u'roles/owner')
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

  def testAddBindingToIamPolicy(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForAddIamPolicyBinding(ai)
    args = parser.parse_args(['--role=roles/editor',
                              '--member=user:etest@gmail.com'])

    expected_policy = pickle.loads(pickle.dumps(self.TEST_IAM_POLICY))
    expected_policy.bindings.append(self.messages.Binding(
        members=['user:etest@gmail.com'],
        role=u'roles/editor'))

    actual_policy = pickle.loads(pickle.dumps(self.TEST_IAM_POLICY))
    iam_util.AddBindingToIamPolicy(self.messages.Binding, actual_policy,
                                   args.member, args.role)

    self.assertEqual(actual_policy, expected_policy)

  def testRemoveBindingFromIamPolicy(self):
    parser = argparse.ArgumentParser()
    ai = self.getDummyArgumentInterceptor(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(ai)
    args = parser.parse_args(['--role=roles/owner',
                              '--member=user:slick@gmail.com'])

    expected_policy = pickle.loads(pickle.dumps(self.TEST_IAM_POLICY))
    expected_policy.bindings[0].members.remove('user:slick@gmail.com')

    actual_policy = pickle.loads(pickle.dumps(self.TEST_IAM_POLICY))
    iam_util.RemoveBindingFromIamPolicy(actual_policy,
                                        args.member, args.role)

    self.assertEqual(actual_policy, expected_policy)

  def testRemoveNonExistingBindingFromIamPolicy(self):
    policy = pickle.loads(pickle.dumps(self.TEST_IAM_POLICY))
    message = 'Policy binding with the specified member and role not found!'
    with self.assertRaisesRegex(iam_util.IamPolicyBindingNotFound, message):
      iam_util.RemoveBindingFromIamPolicy(policy,
                                          'user:lick@gmail.com',
                                          'roles/owner')

  def testSetIamPolicyJson(self):
    policy_file = self._CreateIAMPolicyFile(etag='abcd', as_json=True)
    expected_policy = self._GetTestIAMPolicy(etag='abcd')
    policy = iam_util.ParsePolicyFile(policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)

  def testParseIamPolicyYaml(self):
    policy_file = self._CreateIAMPolicyFile(etag='abcd')
    expected_policy = self._GetTestIAMPolicy(etag='abcd')
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
                                'properly formatted. Base64 decoding error: '
                                'Incorrect padding'):
      iam_util.ParsePolicyFile(bad_file, self.messages.Policy)

  def testParseIamPolicyWithMask(self):
    policy_file = self._CreateIAMPolicyFile(etag='abcd')
    expected_policy = self._GetTestIAMPolicy(etag='abcd')
    policy, update_mask = iam_util.ParsePolicyFileWithUpdateMask(
        policy_file, self.messages.Policy)

    self.assertEqual(policy, expected_policy)
    self.assertEqual(update_mask, 'bindings,etag,version')


class LogSetIamPolicyTest(sdk_test_base.WithLogCapture):

  def testLogSetIamPolicy(self):
    iam_util.LogSetIamPolicy('my-project', 'project')
    self.AssertErrEquals('Updated IAM policy for project [my-project].\n')


if __name__ == '__main__':
  test_case.main()
