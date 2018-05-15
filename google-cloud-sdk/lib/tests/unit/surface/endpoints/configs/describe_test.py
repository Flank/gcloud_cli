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

"""Unit tests for endpoints configs describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base

CONFIG_ID = '2016-01-01R2'


class EndpointsConfigsDescribeTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints configs describe command."""

  def SetUp(self):
    self.config_id_input = self._constructServiceConfigUri(
        self.DEFAULT_SERVICE_NAME, CONFIG_ID)

  def _constructServiceConfigUri(self, service, config_id):
    return 'services/{0}/configs/{1}'.format(service, config_id)

  def _expectDescribeRequest(self, service_name, config_id):
    self.mocked_client.services_configs.Get.Expect(
        request=(self.services_messages.
                 ServicemanagementServicesConfigsGetRequest(
                     serviceName=service_name,
                     configId=config_id
                 )),
        response=self.services_messages.Service(
            name=self.DEFAULT_SERVICE_NAME,
            id=CONFIG_ID)
    )

  def _doDescribe(self, service_input, config_id_input):
    service_config = self.services_messages.Service(
        name=self.DEFAULT_SERVICE_NAME,
        id=CONFIG_ID)

    cmd = 'endpoints configs describe {0} {1}'.format(
        '--service {0}'.format(service_input) if service_input else '',
        config_id_input)

    self._expectDescribeRequest(self.DEFAULT_SERVICE_NAME, CONFIG_ID)
    response = self.Run(cmd)
    self.assertEqual(response, service_config)

  def testServicesConfigsDescribe(self):
    self._doDescribe(self.DEFAULT_SERVICE_NAME, CONFIG_ID)

  def testServicesConfigsDescribeResourceUri(self):
    self._doDescribe(self.DEFAULT_SERVICE_NAME, self.config_id_input)

  def testServicesConfigsDescribeResourceUriMismatchedServices(self):
    service_input = 'foobar'

    # The serviceName in the resource URI overrides the --service flag
    self._doDescribe(service_input, self.config_id_input)

  def testServicesConfigsDescribeResourceUriNoService(self):
    self._doDescribe(None, self.config_id_input)

  def testServicesConfigsDescribeResourceUriIncomplete(self):
    with self.assertRaisesRegex(
        parser_errors.RequiredError,
        'argument --service: Must be specified.'):
      self.Run('endpoints configs describe {0}'.format(CONFIG_ID))


if __name__ == '__main__':
  test_case.main()
