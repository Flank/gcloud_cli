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
from googlecloudsdk.command_lib.monitoring import util
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
    self.aggregation_str = encoding.MessageToJson(self.aggregations[0])
    self.filter_str = ('metric.type = metric{0} AND '
                       'metric.label.instance_name = my-instance{0}')
    self.conditions = [
        self.CreateCondition(
            display_name='my-condition1',
            condition_filter=self.filter_str.format('1'),
            duration='180',
            trigger_count=5,
            aggregations=self.aggregations),
        self.CreateCondition(
            display_name='my-condition2',
            condition_filter=self.filter_str.format('2'),
            duration='120s',
            trigger_percent=0.42,
            comparison='COMPARISON_GT',
            threshold_value=0.8,
            aggregations=self.aggregations)]
    self.notification_channels = [
        'projects/{0}/notificationChannels/my-channel{1}'
        .format(self.Project(), i) for i in range(3)]
    self.service = self.client.projects_alertPolicies
    self.project_name = 'projects/' + self.Project()
    self.labels_cls = self.messages.AlertPolicy.UserLabelsValue

  def _ExpectCreate(self, policy, response):
    req = self.messages.MonitoringProjectsAlertPoliciesCreateRequest(
        name=self.project_name,
        alertPolicy=policy)
    self.service.Create.Expect(req, response)

  @parameterized.parameters(True, False)
  def testCreate_FromJson(self, from_file):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)
    policy_str = encoding.MessageToJson(policy)

    if from_file:
      policy_file = self.Touch(self.temp_path, 'policy.json',
                               contents=policy_str)
      flag = '--policy-from-file ' + policy_file
    else:
      flag = '--policy \'{}\''.format(policy_str)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create ' + flag)

  @parameterized.parameters(True, False)
  def testCreate_FromYaml(self, from_file):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)
    policy_json = json.loads(encoding.MessageToJson(policy))
    policy_str = yaml.dump(policy_json)
    if from_file:
      policy_file = self.Touch(self.temp_path, 'policy.yaml',
                               contents=policy_str)
      flag = '--policy-from-file ' + policy_file
    else:
      flag = '--policy "{}"'.format(policy_str)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create ' + flag)

  def testCreate_AbsenceCondition(self):
    filter_str = ('metric.type = compute.googleapis.com/instance/cpu/'
                  'usage_time AND metric.label.instance_name = '
                  'my-instance-name')
    conditions = [
        self.CreateCondition(
            'my-condition1',
            filter_str,
            '300s',
            trigger_count=10,
            aggregations=self.aggregations)]
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=conditions,
        enabled=None,
        documentation_content='documentation',
        notification_channels=self.notification_channels)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create --display-name my-policy '
             '--documentation documentation '
             '--notification-channels my-channel0,my-channel1,my-channel2 '
             '--condition-display-name my-condition1 --condition-filter "{0}" '
             '--aggregation "{1}" --duration 300s --trigger-count 10 '
             '--if absent'
             .format(filter_str, self.aggregation_str))

  def testCreate_ThresholdCondition(self):
    filter_str = ('metric.type = compute.googleapis.com/instance/cpu/'
                  'usage_time AND metric.label.instance_name = '
                  'my-instance-name')
    conditions = [
        self.CreateCondition(
            'my-condition1',
            filter_str,
            '300s',
            trigger_count=10,
            comparison='COMPARISON_LT',
            threshold_value=0.24,
            aggregations=self.aggregations)]
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create --display-name my-policy '
             '--documentation documentation --enabled '
             '--notification-channels my-channel0,my-channel1,my-channel2 '
             '--condition-display-name my-condition1 --condition-filter "{0}" '
             '--aggregation "{1}" --duration 300s --trigger-count 10 '
             '--if "< 0.24"'
             .format(filter_str, self.aggregation_str))

  def testCreate_NoDocumentation(self):
    filter_str = ('metric.type = compute.googleapis.com/instance/cpu/'
                  'usage_time AND metric.label.instance_name = '
                  'my-instance-name')
    conditions = [
        self.CreateCondition(
            'my-condition1',
            filter_str,
            '300s',
            trigger_count=10,
            aggregations=self.aggregations)]
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=conditions,
        enabled=True,
        notification_channels=self.notification_channels)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create --display-name my-policy --enabled '
             '--notification-channels my-channel0,my-channel1,my-channel2 '
             '--condition-display-name my-condition1 --condition-filter "{0}" '
             '--aggregation "{1}" --duration 300s --trigger-count 10 '
             '--if absent'
             .format(filter_str, self.aggregation_str))

  def testCreate_DocumentationFromFile(self):
    policy = self.CreatePolicy(
        display_name='my-policy',
        enabled=True,
        documentation_content='documentation in file',
        notification_channels=self.notification_channels)
    documentation_file = self.Touch(self.temp_path, 'doc.md',
                                    contents='documentation in file')

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create --display-name my-policy '
             '--documentation-from-file {} --enabled '
             '--notification-channels my-channel0,my-channel1,my-channel2 '
             .format(documentation_file))

  def testCreate_WithUserLabels(self):
    user_labels = encoding.DictToAdditionalPropertyMessage(
        {'a': 'aardvark', 'b': 'bapple'}, self.labels_cls, sort_items=True)
    policy = self.CreatePolicy(
        display_name='my-policy',
        enabled=True,
        notification_channels=self.notification_channels,
        user_labels=user_labels)

    self._ExpectCreate(policy, policy)
    self.Run('monitoring policies create --display-name my-policy '
             '--enabled --user-labels=a=aardvark,b=bapple '
             '--notification-channels my-channel0,my-channel1,my-channel2 ')

  def testCreate_Overrides(self):
    user_labels = encoding.DictToAdditionalPropertyMessage(
        {'a': 'aardvark', 'b': 'bapple'}, self.labels_cls, sort_items=True)
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels,
        user_labels=user_labels)
    policy_str = encoding.MessageToJson(policy)

    filter_str = ('metric.type = compute.googleapis.com/instance/cpu/'
                  'usage_time AND metric.label.instance_name = '
                  'my-instance-name')
    new_conditions = self.conditions + [self.CreateCondition(
        'my-condition3',
        filter_str,
        '300s',
        trigger_count=10,
        comparison='COMPARISON_LT',
        threshold_value=0.24,
        aggregations=self.aggregations)]
    new_channels = [
        'projects/{0}/notificationChannels/other{1}'
        .format(self.Project(), i) for i in range(3)]
    new_user_labels = encoding.DictToAdditionalPropertyMessage(
        {'c': 'cairplane', 'd': 'dalert'}, self.labels_cls, sort_items=True)
    new_policy = self.CreatePolicy(
        display_name='my-new-policy',
        conditions=new_conditions,
        enabled=False,
        documentation_content='noitatnemucod',
        notification_channels=new_channels,
        user_labels=new_user_labels)

    self._ExpectCreate(new_policy, new_policy)
    self.Run('monitoring policies create --policy \'{0}\' '
             '--display-name my-new-policy '
             '--documentation noitatnemucod --no-enabled '
             '--notification-channels other0,other1,other2 '
             '--condition-display-name my-condition3 --condition-filter "{1}" '
             '--aggregation "{2}" --duration 300s --trigger-count 10 '
             '--if "< 0.24" --user-labels=c=cairplane,d=dalert'
             .format(policy_str, filter_str, self.aggregation_str))

  def testCreate_PolicyParseLoadError(self):
    with self.AssertRaisesExceptionMatches(
        util.YamlOrJsonLoadError,
        'Could not parse YAML or JSON string for'):
      self.Run('monitoring policies create --policy \'{"not valid[}\'')

  def testCreate_AggregationParseLoadError(self):
    with self.AssertRaisesExceptionMatches(
        util.YamlOrJsonLoadError,
        'Could not parse YAML or JSON string for'):
      self.Run('monitoring policies create --display-name my-policy '
               '--condition-display-name my-condition1 '
               '--condition-filter "{0}" --aggregation \'{"not valid[}\' '
               '--duration 300s --trigger-count 10 --if "< 0.24"')

  def testCreate_NoPolicyIdentifier(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.MinimumArgumentException,
        'One of [--display-name, --policy, --policy-from-file] must be '
        'supplied.'):
      self.Run('monitoring policies create '
               '--documentation documentation --enabled '
               '--notification-channels my-channel0,my-channel1,my-channel2')

  def testCreate_ConditionRequiredFlag(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'If --condition-filter is set then --if must be set as well.'):
      self.Run('monitoring policies create --display-name my-policy '
               '--condition-display-name my-condition1 --condition-filter cf '
               '--aggregation \'{"not valid[}\' --duration 300s '
               '--trigger-count 10')

  @parameterized.parameters(
      ('--condition-display-name', 'my-condition1'),
      ('--aggregation', '"{}"'),
      ('--duration', '300s'),
      ('--trigger-count', '10'),
      ('--if', 'absent'),
  )
  def testCreate_ConditionFlagsWithoutFilter(self, flag, value):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [{}]: Should only be specified if '
        '--condition-filter is also specified.'.format(flag)):
      self.Run('monitoring policies create --display-name my-policy '
               '{0} {1}'.format(flag, value))


if __name__ == '__main__':
  test_case.main()
