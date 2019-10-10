# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for endpoints configs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsConfigsListTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints configs list command."""

  def SetUp(self):
    self.configs = [self.CreateServiceConfig(config_id='2016-01-01R1'),
                    self.CreateServiceConfig(config_id='2016-01-01R2')]

  def _ListConfigs(self):
    list_request = (self.services_messages.
                    ServicemanagementServicesConfigsListRequest)

    self.mocked_client.services_configs.List.Expect(
        request=list_request(serviceName=self.DEFAULT_SERVICE_NAME),
        response=(self.services_messages.
                  ListServiceConfigsResponse(serviceConfigs=self.configs))
    )

    return self.Run('endpoints configs list '
                    '--service {0}'.format(self.DEFAULT_SERVICE_NAME))

  def testServicesConfigsList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = self._ListConfigs()
    self.assertEqual(response, self.configs)

  def testServicesVersionsListCheckOutput(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self._ListConfigs()

    # Verify the output
    expected_output = ('CONFIG_ID     SERVICE_NAME\n'
                       '2016-01-01R1  service-name.googleapis.com\n'
                       '2016-01-01R2  service-name.googleapis.com\n')
    self.AssertOutputEquals(expected_output)


if __name__ == '__main__':
  test_case.main()
