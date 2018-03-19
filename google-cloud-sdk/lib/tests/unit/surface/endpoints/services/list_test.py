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

"""Unit tests for endpoints services list command."""

from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsListTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services list command."""

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    self.num_services = 10
    self.services = [self.CreateService('service-name%d.googleapis.com' % i)
                     for i in range(self.num_services)]

  def testServicesListProduced(self):
    mocked_response = self.services_messages.ListServicesResponse(
        services=self.services)

    self.mocked_client.services.List.Expect(
        request=self.services_messages.ServicemanagementServicesListRequest(
            consumerId=None,
            producerProjectId='fake-project',
            pageSize=2000,
        ),
        response=mocked_response
    )

    response = self.Run('endpoints services list')
    self.assertEqual(response, self.services)


if __name__ == '__main__':
  test_case.main()
