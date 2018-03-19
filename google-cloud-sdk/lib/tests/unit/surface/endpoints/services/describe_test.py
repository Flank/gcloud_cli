# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for endpoints services describe command."""

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsDescribeTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services describe command."""

  def _doDescribe(self, service_input):
    mocked_response = self.CreateService()
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=self.DEFAULT_SERVICE_NAME,
        ),
        response=mocked_response
    )

    response = self.Run(
        'endpoints services describe ' + service_input)
    self.assertEqual(response, mocked_response)

  def testServicesDescribe(self):
    self._doDescribe(self.DEFAULT_SERVICE_NAME)

  def testServicesDescribeResourceUri(self):
    self._doDescribe('services/{0}'.format(self.DEFAULT_SERVICE_NAME))


if __name__ == '__main__':
  test_case.main()
