# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for organizations set-iam-policy."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding

from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsSetIamPolicyTest(testbase.OrganizationsUnitTestBase):

  def testSetIamPolicyOrganization(self):
    self.mock_client.organizations.SetIamPolicy.Expect(self.DefaultRequest(),
                                                       self._GetTestIamPolicy())

    # Setting the IAM policy yields no result, it's just a side-effect,
    # so we offload the test assertion to the mock.
    self.DoRequest(self._GetTestIamPolicy())
    organization_name = self.TEST_ORGANIZATION.name[len('organizations/'):]
    self.AssertErrContains(
        'Updated IAM policy for organization [{}]'.format(organization_name))

  def testClearBindingsAndEtagSetIamPolicyOrganization(self):
    policy = self._GetTestIamPolicy(clear_fields=['bindings', 'etag'])

    expected_request = (
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                updateMask='auditConfigs,version,bindings,etag')))

    self.mock_client.organizations.SetIamPolicy.Expect(
        expected_request, policy)

    # Setting the IAM policy yields no result, it's just a side-effect,
    # so we offload the test assertion to the mock.
    self.DoRequest(policy)

  def testAuditConfigsPreservedSetIamPolicyOrganization(self):
    policy = self._GetTestIamPolicy(clear_fields=['auditConfigs'])

    expected_request = (
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                updateMask='bindings,etag,version')))

    self.mock_client.organizations.SetIamPolicy.Expect(
        expected_request, self._GetTestIamPolicy())

    # Setting the IAM policy yields no result, it's just a side-effect,
    # so we offload the test assertion to the mock.
    self.DoRequest(policy)

  def testBadJsonOrYamlSetIamPolicyOrganization(self):
    policy_file_path = self.Touch(self.temp_path, 'bad', contents='bad')
    with self.assertRaises(exceptions.Error):
      self.RunSetIamPolicy(policy_file_path)

  def testNoFileSetIamPolicyOrganization(self):
    with self.assertRaises(exceptions.Error):
      self.RunSetIamPolicy('/some/bad/path/to/non/existent/file')

  def testSetIamPolicyOrganization_raisesOrganizationsNotFoundError(self):
    self.SetupSetIamPolicyFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest(self._GetTestIamPolicy())

  def testSetIamPolicyOrganization_raisesOrganizationsAccessError(self):
    self.SetupSetIamPolicyFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organization [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest(self._GetTestIamPolicy())

  def DefaultRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(
            policy=self._GetTestIamPolicy(),
            updateMask='auditConfigs,bindings,etag,version'))

  def SetupSetIamPolicyFailure(self, exception):
    self.mock_client.organizations.SetIamPolicy.Expect(self.DefaultRequest(),
                                                       exception=exception)

  def RunSetIamPolicy(self, policy_file_path):
    self.RunOrganizations('set-iam-policy',
                          self.TEST_ORGANIZATION.name[len('organizations/'):],
                          policy_file_path)

  def DoRequest(self, policy):
    json = encoding.MessageToJson(policy)
    policy_file_path = self.Touch(self.temp_path, 'good.json', contents=json)
    self.RunSetIamPolicy(policy_file_path)


if __name__ == '__main__':
  test_case.main()
