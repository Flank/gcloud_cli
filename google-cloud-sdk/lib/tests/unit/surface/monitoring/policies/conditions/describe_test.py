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
"""Tests for `gcloud monitoring policies describe`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.command_lib.monitoring import util
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringDescribeTest(base.MonitoringTestBase):

  def SetUp(self):
    self.filter_str = ('metric.type = metric{0} AND '
                       'metric.label.instance_name = my-instance{0}')
    policy_name = 'projects/{}/alertPolicies/policy-id'.format(self.Project())
    self.conditions = [
        self.CreateCondition(
            name='{}/conditions/condition-id0'.format(policy_name),
            display_name='my-condition0',
            condition_filter=self.filter_str.format('1'),
            duration='180s',
            trigger_count=5),
        self.CreateCondition(
            name='{}/conditions/condition-id1'.format(policy_name),
            display_name='my-condition1',
            condition_filter=self.filter_str.format('2'),
            duration='120s',
            trigger_percent=0.42,
            comparison='COMPARISON_GT',
            threshold_value=0.8)]
    self.policy = self.messages.AlertPolicy(
        name=policy_name,
        conditions=self.conditions)

  def _ExpectGet(self, policy):
    self.client.projects_alertPolicies.Get.Expect(
        self.messages.MonitoringProjectsAlertPoliciesGetRequest(
            name=policy.name),
        policy)

  def testDescribe(self):
    self._ExpectGet(self.policy)

    result = self.Run('monitoring policies conditions describe condition-id0 '
                      '--policy policy-id')
    self.assertEqual(result, self.conditions[0])

  def testDescribe_RelativeName(self):
    self._ExpectGet(self.policy)

    result = self.Run('monitoring policies conditions describe '
                      'projects/{}/alertPolicies/policy-id/conditions/'
                      'condition-id0'.format(self.Project()))
    self.assertEqual(result, self.conditions[0])

  def testDescribe_ConditionNotFound(self):
    self._ExpectGet(self.policy)

    with self.AssertRaisesExceptionMatches(
        util.ConditionNotFoundError,
        'No condition with name [projects/fake-project/alertPolicies/'
        'policy-id/conditions/shampoo] found in policy.'):
      self.Run('monitoring policies conditions describe shampoo '
               '--policy policy-id')

if __name__ == '__main__':
  test_case.main()
