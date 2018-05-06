# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud monitoring policies conditions update`."""
from apitools.base.py import encoding
from googlecloudsdk.command_lib.monitoring import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringDescribeTest(base.MonitoringTestBase, parameterized.TestCase):

  def SetUp(self):
    self.aggregations = [self.CreateAggregation(
        alignment_period='60s',
        cross_series_reducer='REDUCE_MEAN',
        per_series_aligner='ALIGN_SUM')]
    self.filter_str = ('metric.type = metric{0} AND '
                       'metric.label.instance_name = my-instance{0}')
    policy_name = 'projects/{}/alertPolicies/policy-id'.format(self.Project())
    self.conditions = [
        self.CreateCondition(
            name='{}/conditions/condition-id0'.format(policy_name),
            display_name='my-condition0',
            condition_filter=self.filter_str.format('1'),
            duration='180s',
            trigger_count=5,
            aggregations=self.aggregations),
        self.CreateCondition(
            name='{}/conditions/condition-id1'.format(policy_name),
            display_name='my-condition1',
            condition_filter=self.filter_str.format('2'),
            duration='120s',
            trigger_percent=0.42,
            comparison='COMPARISON_GT',
            threshold_value=0.8,
            aggregations=self.aggregations)]
    self.notification_channels = [
        'projects/{0}/notificationChannels/my-channel{1}'
        .format(self.Project(), i) for i in range(3)]
    self.policy = self.messages.AlertPolicy(
        name=policy_name,
        conditions=self.conditions)

  def _ExpectGet(self, policy):
    self.client.projects_alertPolicies.Get.Expect(
        self.messages.MonitoringProjectsAlertPoliciesGetRequest(
            name=policy.name),
        policy)

  def _ExpectUpdate(self, policy):
    self.client.projects_alertPolicies.Patch.Expect(
        self.messages.MonitoringProjectsAlertPoliciesPatchRequest(
            name=policy.name,
            alertPolicy=policy,
            updateMask='conditions'),
        policy)

  def testCreate_AbsentToAbsent(self):
    new_condition = encoding.CopyProtoMessage(self.conditions[0])
    new_condition.displayName = 'my-condition2'
    new_condition.conditionAbsent.trigger.count = 2

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[0] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id0 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-count 2')

  def testCreate_ThresholdToThreshold(self):
    new_condition = encoding.CopyProtoMessage(self.conditions[1])
    new_condition.displayName = 'my-condition2'
    new_condition.conditionThreshold.trigger.percent = 0.58

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[1] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id1 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-percent 0.58')

  def testCreate_TriggerCountToPercent(self):
    new_condition = encoding.CopyProtoMessage(self.conditions[0])
    new_condition.conditionAbsent.trigger.count = None
    new_condition.conditionAbsent.trigger.percent = 0.58

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[0] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id0 '
             '--policy policy-id '
             '--trigger-percent 0.58')

  def testCreate_TriggerPercentToCount(self):
    new_condition = encoding.CopyProtoMessage(self.conditions[1])
    new_condition.conditionThreshold.trigger.count = 2
    new_condition.conditionThreshold.trigger.percent = None

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[1] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id1 '
             '--policy policy-id '
             '--trigger-count 2')

  def testCreate_AbsentToThreshold(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id0'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('1'),
        duration='180s',
        trigger_count=5,
        aggregations=self.aggregations,
        comparison='COMPARISON_LT',
        threshold_value=0.5)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[0] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id0 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--if "< 0.5"')

  def testCreate_AbsentToThresholdAndChangeCount(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id0'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('1'),
        duration='180s',
        trigger_count=2,
        aggregations=self.aggregations,
        comparison='COMPARISON_LT',
        threshold_value=0.5)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[0] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id0 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-count 2 '
             '--if "< 0.5"')

  def testCreate_AbsentToThresholdAndTriggerCountToPercent(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id0'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('1'),
        duration='180s',
        trigger_percent=0.81,
        aggregations=self.aggregations,
        comparison='COMPARISON_LT',
        threshold_value=0.5)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[0] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id0 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-percent 0.81 '
             '--if "< 0.5"')

  def testCreate_ThresholdToAbsent(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id1'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='120s',
        trigger_percent=0.42,
        aggregations=self.aggregations)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[1] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id1 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--if absent')

  def testCreate_ThresholdToAbsentAndChangePercent(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id1'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='120s',
        trigger_percent=0.81,
        aggregations=self.aggregations)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[1] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id1 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-percent 0.81 '
             '--if absent')

  def testCreate_ThresholdToAbsentAndTriggerPercentToCount(self):
    new_condition = self.CreateCondition(
        name='{}/conditions/condition-id1'.format(self.policy.name),
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='120s',
        trigger_count=3,
        aggregations=self.aggregations)

    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions[1] = new_condition

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions update condition-id1 '
             '--policy policy-id '
             '--display-name my-condition2 '
             '--trigger-count 3 '
             '--if absent')

  def testUpdate_UpdateArgSpecified(self,):
    with self.AssertRaisesExceptionMatches(
        util.NoUpdateSpecifiedError,
        'Did not specify any flags for updating the condition.'):
      self.Run('monitoring policies conditions update condition-id0 '
               '--policy policy-id')


if __name__ == '__main__':
  test_case.main()
