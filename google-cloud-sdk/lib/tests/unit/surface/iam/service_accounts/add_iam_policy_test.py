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

"""Tests that ensure adding IAM policy bindings works properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import time

from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base

from six.moves import range


class AddIamPolicyBinding(unit_test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _SetUpPolicyExpectations(self, resource, old_policy, new_policy):
    self.client.projects_serviceAccounts.GetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetIamPolicyRequest(
            resource=resource),
        response=old_policy)
    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=resource,
            setIamPolicyRequest=self.msgs.SetIamPolicyRequest(
                policy=new_policy)),
        response=new_policy)

  def testAddIamPolicyBinding(self):
    old_policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner',
                members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer',
                members=['allUsers'])])

    new_policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner',
                members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer',
                members=['allUsers']),
            self.msgs.Binding(
                role='roles/editor',
                members=['user:new-user@gmail.com'])])
    resource = ('projects/-/serviceAccounts/'
                'test@test-project.iam.gserviceaccount.com')
    self._SetUpPolicyExpectations(resource, old_policy, new_policy)

    result = self.Run('iam service-accounts add-iam-policy-binding '
                      'test@test-project.iam.gserviceaccount.com '
                      '--role=roles/editor --member=user:new-user@gmail.com')

    self.assertEqual(result, new_policy)

  def testRetry(self):
    self.StartObjectPatch(time, 'sleep')
    old_policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner',
                members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer',
                members=['allUsers'])])

    new_policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner',
                members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer',
                members=['allUsers']),
            self.msgs.Binding(
                role='roles/editor',
                members=['user:new-user@gmail.com'])])

    get_request = self.msgs.IamProjectsServiceAccountsGetIamPolicyRequest(
        resource=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'))
    set_request = self.msgs.IamProjectsServiceAccountsSetIamPolicyRequest(
        resource=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
        setIamPolicyRequest=self.msgs.SetIamPolicyRequest(
            policy=new_policy))

    # Retry will send 4 requests total, so the first 3 should fail
    for i in range(3):  # pylint: disable=unused-variable
      self.client.projects_serviceAccounts.GetIamPolicy.Expect(
          request=get_request,
          response=copy.deepcopy(old_policy))
      self.client.projects_serviceAccounts.SetIamPolicy.Expect(
          request=set_request,
          exception=self.MockHttpError(409, 'Conflict'))

    self.client.projects_serviceAccounts.GetIamPolicy.Expect(
        request=get_request,
        response=copy.deepcopy(old_policy))
    self.client.projects_serviceAccounts.SetIamPolicy.Expect(
        request=set_request,
        response=new_policy)

    result = self.Run('iam service-accounts add-iam-policy-binding '
                      'test@test-project.iam.gserviceaccount.com '
                      '--role=roles/editor --member=user:new-user@gmail.com')
    self.assertEqual(result, new_policy)

  def testAddIamPolicyBindingInvalidName(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts add-iam-policy-binding '
               'test --role=roles/editor --member=user:new-user@gmail.com')

  def testAddIamPolicyBindingValidUniqueId(self):
    old_policy = self.msgs.Policy()
    new_policy = self.msgs.Policy(bindings=[
        self.msgs.Binding(
            role='roles/editor',
            members=['user:new-user@gmail.com'])])
    resource = 'projects/-/serviceAccounts/' + self.sample_unique_id
    self._SetUpPolicyExpectations(resource, old_policy, new_policy)

    try:
      self.Run('iam service-accounts add-iam-policy-binding %s '
               '--role=roles/editor --member=user:new-user@gmail.com'
               % self.sample_unique_id)
    except cli_test_base.MockArgumentError:
      self.fail('add-iam-policy-binding should accept unique ids for service '
                'accounts.')

if __name__ == '__main__':
  test_case.main()
