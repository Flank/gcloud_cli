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

"""Unit tests for endpoints add-iam-policy-binding command."""

from googlecloudsdk.api_lib.endpoints import services_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.endpoints import unit_test_base

# Shorten the Access Policy Get request name for better readability
GET_REQUEST = (services_util.GetMessagesModule()
               .ServicemanagementServicesGetIamPolicyRequest)


class EndpointsAddIamPolicyBindingTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services add-iam-policy-binding command."""

  def PreSetUp(self):
    self.access_policy_msg = self.services_messages.Policy
    self.etag = 'test_etag'
    self.encoded_etag = self.etag.encode('base64').strip()
    self.consumer_role = 'roles/servicemanagement.serviceConsumer'

  def testAddUserToService(self):
    member_to_add = 'my_new_test_user12345@google.com'
    member_string = 'user:{0}'.format(member_to_add)

    old_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(
            role='roles/servicemanagement.serviceConsumer', members=[])],
        etag=self.etag
    )

    new_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(
            role=self.consumer_role,
            members=[member_string])],
        etag=self.etag
    )

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(servicesId=self.DEFAULT_SERVICE_NAME),
        response=old_policy
    )

    set_policy_request = self.services_messages.SetIamPolicyRequest(
        policy=new_policy)
    expected_request = (self.services_messages.
                        ServicemanagementServicesSetIamPolicyRequest(
                            servicesId=self.DEFAULT_SERVICE_NAME,
                            setIamPolicyRequest=set_policy_request))

    self.mocked_client.services.SetIamPolicy.Expect(
        request=expected_request,
        response=new_policy)

    response = self.Run(
        'endpoints services add-iam-policy-binding {0} --member {1} '
        '--role {2}'.format(self.DEFAULT_SERVICE_NAME,
                            member_string,
                            self.consumer_role))
    self.assertEqual(response, new_policy)

  def testAddUserToServiceGetIamPolicy404(self):
    member_to_add = 'my_new_test_user12345@google.com'
    member_string = 'user:{0}'.format(member_to_add)

    new_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(
            role=self.consumer_role,
            members=[member_string])],
        etag=None
    )

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(servicesId=self.DEFAULT_SERVICE_NAME),
        exception=http_error.MakeHttpError(404)
    )

    set_policy_request = self.services_messages.SetIamPolicyRequest(
        policy=new_policy)
    expected_request = (self.services_messages.
                        ServicemanagementServicesSetIamPolicyRequest(
                            servicesId=self.DEFAULT_SERVICE_NAME,
                            setIamPolicyRequest=set_policy_request))

    self.mocked_client.services.SetIamPolicy.Expect(
        request=expected_request,
        response=new_policy)

    response = self.Run(
        'endpoints services add-iam-policy-binding {0} --member {1} '
        '--role {2}'.format(self.DEFAULT_SERVICE_NAME,
                            member_string,
                            self.consumer_role))
    self.assertEqual(response, new_policy)

  def testAddUserToServiceGetIamPolicy403(self):
    member_to_add = 'my_new_test_user12345@google.com'
    member_string = 'user:{0}'.format(member_to_add)

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(servicesId=self.DEFAULT_SERVICE_NAME),
        exception=http_error.MakeHttpError(403)
    )

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.Run('endpoints services add-iam-policy-binding {0} '
               '--member {1} --role {2}'
               .format(self.DEFAULT_SERVICE_NAME, member_string,
                       self.consumer_role))

  def testAddGroupToService(self):
    member_to_add = 'my_new_test_group12345@google.com'
    member_string = 'group:{0}'.format(member_to_add)

    old_policy = self.access_policy_msg(
        bindings=[
            self.services_messages.Binding(role=self.consumer_role,
                                           members=[])
        ],
        etag=self.etag
    )

    new_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(
            role=self.consumer_role, members=[member_string])],
        etag=self.etag
    )

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(servicesId=self.DEFAULT_SERVICE_NAME),
        response=old_policy
    )

    set_policy_request = self.services_messages.SetIamPolicyRequest(
        policy=new_policy)
    expected_request = (self.services_messages.
                        ServicemanagementServicesSetIamPolicyRequest(
                            servicesId=self.DEFAULT_SERVICE_NAME,
                            setIamPolicyRequest=set_policy_request))

    self.mocked_client.services.SetIamPolicy.Expect(
        request=expected_request,
        response=new_policy)

    response = self.Run(
        'endpoints services add-iam-policy-binding {0} --member {1} '
        '--role {2}'.format(self.DEFAULT_SERVICE_NAME,
                            member_string,
                            self.consumer_role))
    self.assertEqual(response, new_policy)

  def testAddAllUsersToService(self):
    member = 'allUsers'

    old_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(role=self.consumer_role,
                                                 members=[])],
        etag=self.etag
    )

    new_policy = self.access_policy_msg(
        bindings=[self.services_messages.Binding(
            role=self.consumer_role, members=[member])],
        etag=self.etag
    )

    self.mocked_client.services.GetIamPolicy.Expect(
        request=GET_REQUEST(servicesId=self.DEFAULT_SERVICE_NAME),
        response=old_policy
    )

    set_policy_request = self.services_messages.SetIamPolicyRequest(
        policy=new_policy)
    expected_request = (self.services_messages.
                        ServicemanagementServicesSetIamPolicyRequest(
                            servicesId=self.DEFAULT_SERVICE_NAME,
                            setIamPolicyRequest=set_policy_request))

    self.mocked_client.services.SetIamPolicy.Expect(
        request=expected_request,
        response=new_policy)

    response = self.Run(
        'endpoints services add-iam-policy-binding {0} --member {1} '
        '--role {2}'.format(self.DEFAULT_SERVICE_NAME,
                            member,
                            self.consumer_role))
    self.assertEqual(response, new_policy)


if __name__ == '__main__':
  test_case.main()
