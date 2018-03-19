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

"""Tests of the config_reporter module."""

import json

from apitools.base.py import encoding

from googlecloudsdk.api_lib.endpoints import config_reporter

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base

SERVICE_NAME = 'service-name.googleapis.com'
SERVICE_VERSION = 'service-config-version-1'
TITLE = 'The title of my swagger spec or google service config!'
CONFIG_TEMPLATE = """
{
     "title": "%s",
     "name": "%s"
}
"""
TEST_CONFIG = CONFIG_TEMPLATE % (TITLE, SERVICE_NAME)
TEST_SWAGGER = """
{
   "swagger": "2.0",
   "host": "%s",
   "title": "%s"
}
""" % (SERVICE_NAME, TITLE)
TEST_SWAGGER_PATH = '/tmp/foo/bar/swagger.json'


class ConfigReporterValueTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for ConfigReporterValue class."""

  def SetUp(self):
    self.value_types = [
        self.services_messages.GenerateConfigReportRequest.OldConfigValue,
        self.services_messages.GenerateConfigReportRequest.NewConfigValue,
    ]
    self.crv = config_reporter.ConfigReporterValue(self.DEFAULT_SERVICE_NAME)

  def _normalizeConfigValue(self, config_value):
    """Normalize the AdditionalProperties so comparisons always pass.

    Args:
      config_value: The OldValueType or NewValueType to normalize.
    """
    # Sanity check the type of the input
    # pylint: disable=unidiomatic-typecheck
    if type(config_value) not in self.value_types:
      raise TypeError('Invalid config_value in normalizeConfigValue')

    config_value.additionalProperties = sorted(
        config_value.additionalProperties)

  def testUsingConfig(self):
    self.crv.SetConfig(json.loads(TEST_CONFIG))
    self.assertTrue(self.crv.IsReadyForReport())
    self.assertEqual('type.googleapis.com/google.api.Service',
                     self.crv.GetTypeUrl())

    for value_type in self.value_types:
      expected_result_dict = json.loads(TEST_CONFIG)
      expected_result_dict['@type'] = 'type.googleapis.com/google.api.Service'
      expected_result = encoding.DictToMessage(expected_result_dict, value_type)

      config_value = self.crv.ConstructConfigValue(value_type)

      self.assertEqual(self._normalizeConfigValue(expected_result),
                       self._normalizeConfigValue(config_value))

  def testUsingSwagger(self):
    type_url = ('type.googleapis.com/'
                'google.api.servicemanagement.v1.ConfigSource')
    self.crv.SetSwagger(TEST_SWAGGER_PATH, TEST_SWAGGER)
    self.assertTrue(self.crv.IsReadyForReport())
    self.assertEqual(type_url, self.crv.GetTypeUrl())

    for value_type in self.value_types:
      config_file = self.services_messages.ConfigFile(
          filePath=TEST_SWAGGER_PATH,
          fileContents=TEST_SWAGGER,
          fileType=(self.services_messages.ConfigFile.
                    FileTypeValueValuesEnum.OPEN_API_YAML))
      config_source_message = self.services_messages.ConfigSource(
          files=[config_file])
      expected_result_dict = encoding.MessageToDict(config_source_message)
      expected_result_dict['@type'] = type_url
      expected_result = encoding.DictToMessage(expected_result_dict, value_type)

      config_value = self.crv.ConstructConfigValue(value_type)

      self.assertEqual(self._normalizeConfigValue(expected_result),
                       self._normalizeConfigValue(config_value))

  def testUsingConfigId(self):
    type_url = 'type.googleapis.com/google.api.servicemanagement.v1.ConfigRef'
    config_id = '2017-04-18R0'
    self.crv.SetConfigId(config_id)
    self.assertTrue(self.crv.IsReadyForReport())
    self.assertEqual(type_url, self.crv.GetTypeUrl())

    for value_type in self.value_types:
      expected_result_dict = {
          'name': 'services/{0}/configs/{1}'.format(self.DEFAULT_SERVICE_NAME,
                                                    config_id),
          '@type': type_url,
      }
      expected_result = encoding.DictToMessage(expected_result_dict, value_type)

      config_value = self.crv.ConstructConfigValue(value_type)

      self.assertEqual(self._normalizeConfigValue(expected_result),
                       self._normalizeConfigValue(config_value))

  def testUsingActiveConfigId(self):
    type_url = 'type.googleapis.com/google.api.servicemanagement.v1.ConfigRef'
    config_id = '2017-04-18R0'

    # The ConfigReporterValue class is set to use the active config ID by
    # default, so no need to set any values here
    self.assertTrue(self.crv.IsReadyForReport())
    self.assertEqual(type_url, self.crv.GetTypeUrl())

    percentages_value = (self.services_messages.TrafficPercentStrategy
                         .PercentagesValue)
    prop = percentages_value.AdditionalProperty
    rollout = self.services_messages.Rollout(
        rolloutId='rollout1',
        status=self.services_messages.Rollout.StatusValueValuesEnum.SUCCESS,
        serviceName=self.DEFAULT_SERVICE_NAME,
        trafficPercentStrategy=self.services_messages.TrafficPercentStrategy(
            percentages=percentages_value(additionalProperties=[
                prop(key=config_id, value=100.0),
            ])
        ),
    )

    for value_type in self.value_types:
      expected_result_dict = {
          'name': 'services/{0}/configs/{1}'.format(self.DEFAULT_SERVICE_NAME,
                                                    config_id),
          '@type': type_url,
      }
      expected_result = encoding.DictToMessage(expected_result_dict, value_type)

      req = self.services_messages.ServicemanagementServicesRolloutsListRequest(
          serviceName=self.DEFAULT_SERVICE_NAME,
          pageSize=1)
      self.mocked_client.services_rollouts.List.Expect(
          request=req,
          response=self.services_messages.ListServiceRolloutsResponse(
              rollouts=[rollout])
      )

      config_value = self.crv.ConstructConfigValue(value_type)

      self.assertEqual(self._normalizeConfigValue(expected_result),
                       self._normalizeConfigValue(config_value))

  def testUsingActiveConfigIdNoneAvailable(self):
    type_url = 'type.googleapis.com/google.api.servicemanagement.v1.ConfigRef'

    # The ConfigReporterValue class is set to use the active config ID by
    # default, so no need to set any values here
    self.assertTrue(self.crv.IsReadyForReport())
    self.assertEqual(type_url, self.crv.GetTypeUrl())

    for value_type in self.value_types:
      expected_result_dict = {
          'name': 'services/{0}'.format(self.DEFAULT_SERVICE_NAME),
          '@type': type_url,
      }
      expected_result = encoding.DictToMessage(expected_result_dict, value_type)

      req = self.services_messages.ServicemanagementServicesRolloutsListRequest(
          serviceName=self.DEFAULT_SERVICE_NAME,
          pageSize=1)
      self.mocked_client.services_rollouts.List.Expect(
          request=req,
          response=self.services_messages.ListServiceRolloutsResponse(
              rollouts=[])
      )

      config_value = self.crv.ConstructConfigValue(value_type)

      self.assertEqual(self._normalizeConfigValue(expected_result),
                       self._normalizeConfigValue(config_value))

  def testIsNotReadyForReport(self):
    self.crv.config_use_active_id = False
    self.assertFalse(self.crv.IsReadyForReport())

  def testConstructConfigValueReturnsNoneWhenNotReady(self):
    self.crv.config_use_active_id = False
    self.assertIsNone(
        self.crv.ConstructConfigValue(
            self.services_messages.GenerateConfigReportRequest.OldConfigValue))
    self.assertIsNone(
        self.crv.ConstructConfigValue(
            self.services_messages.GenerateConfigReportRequest.NewConfigValue))


if __name__ == '__main__':
  test_case.main()
