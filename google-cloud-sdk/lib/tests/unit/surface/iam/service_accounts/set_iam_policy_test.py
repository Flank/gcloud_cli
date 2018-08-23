# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests that ensure setting an IAM policy works properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base

_ETAG_CONFIRM_PROMPT = (r'The specified policy does not contain an \"etag\" '
                        r'field identifying a specific version to replace. '
                        r'Changing a policy without an \"etag\" can overwrite '
                        r'concurrent policy changes.')


class SetIamPolicy(unit_test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _CreatePolicyAndFile(self, include_etag=False):
    etag_bin = b'abcde'
    if include_etag:
      etag_field = ''',
              "etag": "{}"'''.format(
                  base64.urlsafe_b64encode(etag_bin).decode('ascii'))
    else:
      etag_field = ''
    policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner',
                members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer',
                members=['allUsers'])],
        etag=(etag_bin if include_etag else None))
    f = self.Touch(
        self.temp_path,
        contents=
        '''{{
          "version": 1,
          "bindings": [
            {{
              "role": "roles/owner",
              "members": ["user:test-user@gmail.com"]
            }},
            {{
              "role": "roles/viewer",
              "members": ["allUsers"]
            }}
          ]{}
        }}'''.format(etag_field))
    return policy, f

  def testSetIamPolicy(self):
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy)),
        response=policy)

    result = self.Run('iam service-accounts set-iam-policy '
                      'test@test-project.iam.gserviceaccount.com '
                      '{0}'.format(in_file))
    self.assertEqual(result, policy)

  def testSetIamPolicyCheckOutput(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy)),
        response=policy)

    result = self.Run('iam service-accounts set-iam-policy '
                      'test@test-project.iam.gserviceaccount.com '
                      '{0}'.format(in_file))

    self.assertEqual(result, policy)

    self.AssertErrContains('Updated IAM policy for service account '
                           '[test@test-project.iam.gserviceaccount.com].')

  def testSetIamPolicyWithServiceAccount(self):
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy)),
        response=policy)

    result = self.Run('iam service-accounts set-iam-policy '
                      'test@test-project.iam.gserviceaccount.com '
                      '{0} --account test@test-project.iam.gserviceaccount.'
                      '.com'.format(in_file))

    self.assertEqual(result, policy)

  def testSetIamPolicyYaml(self):
    policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer', members=['allUsers'])
        ],
        etag=None)
    in_file = self.Touch(
        self.temp_path,
        contents='version: 1\n'
                 'bindings:\n'
                 '- members:\n'
                 '  - user:test-user@gmail.com\n'
                 '  role: roles/owner\n'
                 '- members:\n'
                 '  - allUsers\n'
                 '  role: roles/viewer')

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    result = self.Run('iam service-accounts set-iam-policy '
                      'test@test-project.iam.gserviceaccount.com '
                      '{0}'.format(in_file))

    self.assertEqual(result, policy)

  def testMissingInputFile(self):
    with self.assertRaises(exceptions.Error):
      self.Run('iam service-accounts set-iam-policy '
               'test@test-project.iam.gserviceaccount.com '
               '/file-does-not-exist')

  def testPromptNoEtagYesSucceeds(self):
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.WriteInput('y\n')
    self.Run('iam service-accounts set-iam-policy '
             'test@test-project.iam.gserviceaccount.com '
             '{0}'.format(in_file))
    self.AssertErrContains(_ETAG_CONFIRM_PROMPT)

  def testPromptNoEtagNoFails(self):
    _, in_file = self._CreatePolicyAndFile()
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iam service-accounts set-iam-policy '
               'test@test-project.iam.gserviceaccount.com '
               '{0}'.format(in_file))
    self.AssertErrContains(_ETAG_CONFIRM_PROMPT)

  def testNoPromptWithEtag(self):
    policy, in_file = self._CreatePolicyAndFile(include_etag=True)

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'),
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(
                policy=policy)),
        response=policy)
    self.Run('iam service-accounts set-iam-policy '
             'test@test-project.iam.gserviceaccount.com '
             '{0}'.format(in_file))
    self.AssertErrNotContains(_ETAG_CONFIRM_PROMPT)

  def testSetIamPolicyInvalidName(self):
    _, in_file = self._CreatePolicyAndFile(include_etag=True)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts set-iam-policy '
               'test {0}'.format(in_file))

  def testSetIamPolicyValidUniqueId(self):
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource='projects/-/serviceAccounts/' + self.sample_unique_id,
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy)),
        response=policy)

    try:
      self.Run('iam service-accounts set-iam-policy '
               '{0} {1}'.format(self.sample_unique_id, in_file))
    except cli_test_base.MockArgumentError:
      self.fail('set-iam-policy should accept unique ids for service '
                'accounts.')

if __name__ == '__main__':
  test_case.main()
