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
"""Tests of the services_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.api_lib.endpoints import services_util
from tests.lib.surface.endpoints import unit_test_base


class ServicesUtilTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for services_util module."""

  def testIsProtoDescriptor(self):
    pb_filename = 'service.pb'
    descriptor_filename = 'service.descriptor'
    json_filename = 'service.json'

    self.assertTrue(services_util.IsProtoDescriptor(pb_filename))
    self.assertTrue(services_util.IsProtoDescriptor(descriptor_filename))
    self.assertFalse(services_util.IsProtoDescriptor(json_filename))

  def testReadBinaryProtoFile(self):
    expected_contents = b'\n\x1d\n\nnano.proto\x12\x07foo.barb\x06proto3'
    proto_file_path = self.Resource(
        'tests', 'unit', 'surface', 'endpoints', 'testdata', 'nano.pb')
    contents = services_util.ReadServiceConfigFile(proto_file_path)
    self.assertEqual(expected_contents, contents)

  def testPushAdvisorChangeTypeToString(self):
    enums = self.services_messages.ConfigChange.ChangeTypeValueValuesEnum
    result = services_util.PushAdvisorChangeTypeToString(enums.ADDED)
    self.assertEqual('added', result)
    result = services_util.PushAdvisorChangeTypeToString(enums.REMOVED)
    self.assertEqual('removed', result)
    result = services_util.PushAdvisorChangeTypeToString(enums.MODIFIED)
    self.assertEqual('modified', result)
    result = services_util.PushAdvisorChangeTypeToString('foo')
    self.assertEqual('[unknown]', result)

  def testPushAdvisorConfigChangeToString(self):
    advice = self.services_messages.Advice(
        description='Change the config so that this message does not appear. '
                    '\u2019')
    change_type = (self.services_messages.ConfigChange.ChangeTypeValueValuesEnum
                   .ADDED)
    element = 'element with unicode char \u2019'
    new_value = 'bar with unicode char \u2019'
    old_value = 'foo with unicode char \u2019'
    config_change = self.services_messages.ConfigChange(
        advices=[advice],
        changeType=change_type,
        element=element,
        newValue=new_value,
        oldValue=old_value)

    expected_result = (
        'Element [{element}] (old value = {old_value}, '
        'new value = {new_value}) was {change_type}. Advice:\n'
        '\t* {advice}'
        .format(
            element=config_change.element,
            old_value=config_change.oldValue,
            new_value=config_change.newValue,
            change_type=services_util.PushAdvisorChangeTypeToString(
                config_change.changeType),
            advice=advice.description))
    result = services_util.PushAdvisorConfigChangeToString(config_change)

    self.assertEqual(expected_result, result)

  def testGetActiveRolloutForService(self):
    success = self.services_messages.Rollout.StatusValueValuesEnum.SUCCESS
    failed = self.services_messages.Rollout.StatusValueValuesEnum.FAILED
    req = self.services_messages.ServicemanagementServicesRolloutsListRequest(
        serviceName=self.DEFAULT_SERVICE_NAME,
        pageSize=1)

    percentages_value = (self.services_messages.TrafficPercentStrategy
                         .PercentagesValue)
    prop = percentages_value.AdditionalProperty
    failed_rollout = self.services_messages.Rollout(
        rolloutId='rollout2',
        status=failed,
        serviceName=self.DEFAULT_SERVICE_NAME,
        trafficPercentStrategy=self.services_messages.TrafficPercentStrategy(
            percentages=percentages_value(additionalProperties=[
                prop(key='service_config_1', value=50.0),
                prop(key='service_config_2', value=50.0)
            ])
        ),
    )
    success_rollout = self.services_messages.Rollout(
        rolloutId='rollout1',
        status=success,
        serviceName=self.DEFAULT_SERVICE_NAME,
        trafficPercentStrategy=self.services_messages.TrafficPercentStrategy(
            percentages=percentages_value(additionalProperties=[
                prop(key='service_config_1', value=50.0),
                prop(key='service_config_2', value=50.0)
            ])
        ),
    )

    self.mocked_client.services_rollouts.List.Expect(
        request=req,
        response=self.services_messages.ListServiceRolloutsResponse(
            rollouts=[failed_rollout, success_rollout])
    )

    result = services_util.GetActiveRolloutForService(self.DEFAULT_SERVICE_NAME)
    self.assertEqual(result, success_rollout)

  def testGetActiveServiceConfigIdsFromRollout(self):
    success = self.services_messages.Rollout.StatusValueValuesEnum.SUCCESS
    percentages_value = (self.services_messages.TrafficPercentStrategy
                         .PercentagesValue)
    prop = percentages_value.AdditionalProperty
    active_config_ids = ['service_config_1', 'service_config_2']

    percentages = [
        prop(key=i, value=100. / len(active_config_ids))
        for i in active_config_ids
    ]

    rollout = self.services_messages.Rollout(
        rolloutId='rollout1',
        status=success,
        serviceName=self.DEFAULT_SERVICE_NAME,
        trafficPercentStrategy=self.services_messages.TrafficPercentStrategy(
            percentages=percentages_value(additionalProperties=percentages)
        ),
    )

    results = services_util.GetActiveServiceConfigIdsFromRollout(rollout)
    self.assertEqual(active_config_ids, results)

  def testGetActiveServiceConfigIdsFromRolloutNoActiveRollout(self):
    results = services_util.GetActiveServiceConfigIdsFromRollout(None)
    self.assertEqual([], results)
