# -*- coding: utf-8 -*- #
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
"""Tests for `gcloud monitoring policies create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.monitoring import base
from six.moves import range


class MonitoringCreateTest(base.MonitoringTestBase, parameterized.TestCase):

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
            alertPolicy=policy),
        policy)

  def testCreate_AllOptions(self):
    new_condition = self.CreateCondition(
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='360s',
        trigger_count=2,
        aggregations=self.aggregations)
    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions.append(new_condition)
    aggregation_str = encoding.MessageToJson(self.aggregations[0])

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions create policy-id '
             '--condition-display-name my-condition2 --condition-filter "{0}" '
             '--aggregation "{1}" --duration 360s --trigger-count 2 '
             '--if absent'
             .format(self.filter_str.format('2'), aggregation_str))

  @parameterized.parameters(
      (True, True),
      (True, False),
      (False, True),
      (False, False)
  )
  def testCreate_FromString(self, use_yaml, from_file):
    new_condition = self.CreateCondition(
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='360s',
        trigger_count=2,
        aggregations=self.aggregations)
    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions.append(new_condition)

    condition_str = encoding.MessageToJson(new_condition)
    if use_yaml:
      condition_json = json.loads(condition_str)
      condition_str = yaml.dump(condition_json)

    if from_file:
      condition_file = self.Touch(self.temp_path, 'condition',
                                  contents=condition_str)
      flag = '--condition-from-file ' + condition_file
    else:
      flag = '--condition \'{}\''.format(condition_str)

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions create policy-id ' + flag)

  def testCreate_FromStringGetsModified(self):
    base_condition = self.CreateCondition(
        display_name='my-condition2',
        condition_filter=self.filter_str.format('2'),
        duration='360s',
        trigger_count=2)
    condition_str = encoding.MessageToJson(base_condition)
    new_condition = self.CreateCondition(
        display_name='my-condition3',
        condition_filter=self.filter_str.format('3'),
        duration='420s',
        trigger_count=3,
        aggregations=self.aggregations)
    new_policy = encoding.CopyProtoMessage(self.policy)
    new_policy.conditions.append(new_condition)
    aggregation_str = encoding.MessageToJson(self.aggregations[0])

    self._ExpectGet(self.policy)
    self._ExpectUpdate(new_policy)
    self.Run('monitoring policies conditions create policy-id '
             '--condition \'{0}\' '
             '--condition-display-name my-condition3 --condition-filter "{1}" '
             '--aggregation "{2}" --duration 420s --trigger-count 3 '
             '--if absent'.format(condition_str,
                                  self.filter_str.format('3'),
                                  aggregation_str))

  def testCreate_NoPolicyIdentifier(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.MinimumArgumentException,
        'One of [--condition-filter, --condition, --condition-from-file] must '
        'be supplied.'):
      self.Run('monitoring policies conditions create policy-id '
               '--condition-display-name my-condition2')

  def testCreate_FromStringMutex(self):
    temp_file = self.Touch(self.temp_path, 'temp.json')
    with self.AssertRaisesArgumentErrorMatches(
        'At most one of --condition | --condition-from-file may be specified.'):
      self.Run('monitoring policies conditions create policy-id '
               '--condition "a-cond" --condition-from-file {}'
               .format(temp_file))

if __name__ == '__main__':
  test_case.main()
