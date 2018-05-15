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

"""Unit tests for endpoints check-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.api_lib.endpoints import services_util

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


TEST_REQUEST = (services_util.GetMessagesModule().
                ServicemanagementServicesTestIamPermissionsRequest)

_ALL_IAM_PERMISSIONS = [
    'servicemanagement.services.get',
    'servicemanagement.services.getProjectSettings',
    'servicemanagement.services.delete',
    'servicemanagement.services.update',
    'servicemanagement.services.bind',
    'servicemanagement.services.updateProjectSettings',
    'servicemanagement.services.check',
    'servicemanagement.services.report',
    'servicemanagement.services.setIamPolicy',
    'servicemanagement.services.getIamPolicy',
]


class EndpointsCheckIamPolicyTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services access check command."""

  def testServicesAccessCheck(self):
    test_permissions = self.mocked_client.services.TestIamPermissions

    expected_request = TEST_REQUEST(
        servicesId=self.DEFAULT_SERVICE_NAME,
        testIamPermissionsRequest=(self.services_messages.
                                   TestIamPermissionsRequest(
                                       permissions=_ALL_IAM_PERMISSIONS)))
    mocked_response = self.services_messages.TestIamPermissionsResponse(
        permissions=['servicemanagement.services.get'])

    test_permissions.Expect(request=expected_request, response=mocked_response)

    response = self.Run('endpoints services check-iam-policy {0}'.format(
        self.DEFAULT_SERVICE_NAME))
    self.assertEqual(response, mocked_response)


if __name__ == '__main__':
  test_case.main()
