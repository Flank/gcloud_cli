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
from apitools.base.py import encoding
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.monitoring import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringUpdateTest(base.MonitoringTestBase, parameterized.TestCase):

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
            duration='180s',
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
    self.labels_cls = self.messages.AlertPolicy.UserLabelsValue

  def _ExpectUpdate(self, policy_name, policy, old_policy=None,
                    new_policy=None, field_masks=None):
    relative_name = 'projects/{0}/alertPolicies/{1}'.format(
        self.Project(), policy_name)
    if old_policy:
      get_request = self.messages.MonitoringProjectsAlertPoliciesGetRequest(
          name=relative_name)
      self.client.projects_alertPolicies.Get.Expect(get_request, old_policy)
    request = self.messages.MonitoringProjectsAlertPoliciesPatchRequest(
        name=relative_name,
        alertPolicy=policy,
        updateMask=field_masks)
    self.client.projects_alertPolicies.Patch.Expect(request,
                                                    new_policy or policy)

  def _RunLabelsTest(self, old_labels, new_labels, update_flags):
    policy_name = 'policy-id'
    old_labels = encoding.DictToAdditionalPropertyMessage(
        old_labels, self.labels_cls, sort_items=True)
    new_labels = encoding.DictToAdditionalPropertyMessage(
        new_labels, self.labels_cls, sort_items=True)
    old_policy = self.CreatePolicy(
        name=policy_name,
        display_name='my-policy',
        user_labels=old_labels)
    new_policy = self.CreatePolicy(
        name=policy_name,
        display_name='my-policy',
        user_labels=new_labels)
    self._ExpectUpdate(policy_name, new_policy, old_policy=old_policy,
                       field_masks='user_labels')
    self.Run('monitoring policies update {0} {1}'.format(
        policy_name, update_flags))

  def testUpdate_UpdateLabels(self):
    self._RunLabelsTest(
        {'a': 'aardvark', 'b': 'bapple'},
        {'a': 'aardvark', 'b': 'bapple', 'c': 'cairplane', 'd': 'dalert'},
        '--update-user-labels c=cairplane,d=dalert')

  def testUpdate_RemoveLabels(self):
    self._RunLabelsTest(
        {'a': 'aardvark', 'b': 'bapple', 'c': 'cairplane', 'd': 'dalert'},
        {'a': 'aardvark', 'b': 'bapple'},
        '--remove-user-labels c,d')

  def testUpdate_ClearAndUpdateLabels(self):
    self._RunLabelsTest(
        {'a': 'aardvark', 'b': 'bapple'},
        {'c': 'cairplane', 'd': 'dalert'},
        '--clear-user-labels --update-user-labels c=cairplane,d=dalert')

  def testUpdate_RemoveAndUpdateLabels(self):
    self._RunLabelsTest(
        {'a': 'aardvark', 'b': 'bapple'},
        {'a': 'aardvark', 'c': 'cairplane'},
        '--remove-user-labels b --update-user-labels c=cairplane')

  @parameterized.parameters(True, False)
  def testUpdate_FromJsonFile(self, from_file):
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

    self._ExpectUpdate('policy-id', policy)
    self.Run('monitoring policies update policy-id ' + flag)

  @parameterized.parameters(True, False)
  def testUpdate_AllOptions(self, from_string):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)
    modified_policy = self.CreatePolicy(
        display_name='my-new-policy',
        conditions=self.conditions,
        enabled=False,
        documentation_content='Who needs this?',
        notification_channels=self.notification_channels)

    if from_string:
      field_masks = None
      policy_str = encoding.MessageToJson(policy)
      policy_arg = '--policy \'{}\''.format(policy_str)
      old_policy = None
    else:
      field_masks = ','.join(
          ['display_name', 'documentation.content', 'enabled'])
      policy_arg = ''
      old_policy = policy

    self._ExpectUpdate('policy-id',
                       modified_policy,
                       old_policy=old_policy,
                       field_masks=field_masks)
    self.Run('monitoring policies update policy-id {} '
             '--display-name my-new-policy --no-enabled '
             '--documentation "Who needs this?"'.format(policy_arg))

  @parameterized.parameters(
      ('--set-notification-channels', [4, 5, 6], [4, 5, 6]),
      ('--remove-notification-channels', [1, 6], [0, 2]),
      ('--add-notification-channels', [2, 3, 4], [0, 1, 2, 3, 4]),
      ('--clear-notification-channels', '', []),
  )
  def testUpdate_ModifyNotificationChannels(self, flag, value, expected):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)
    policy_str = encoding.MessageToJson(policy)
    new_channels = self.notification_channels = [
        'projects/{0}/notificationChannels/my-channel{1}'
        .format(self.Project(), i) for i in expected]
    modified_policy = encoding.CopyProtoMessage(policy)
    modified_policy.notificationChannels = new_channels

    if value:
      value = ','.join(['my-channel{}'.format(i) for i in value])

    self._ExpectUpdate('policy-id', modified_policy)
    self.Run('monitoring policies update policy-id --policy \'{0}\' '
             '{1} {2}'.format(policy_str, flag, value))

  def testUpdate_ModifyWithoutDocumentation(self):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        notification_channels=self.notification_channels)
    policy_str = encoding.MessageToJson(policy)
    modified_policy = encoding.CopyProtoMessage(policy)
    modified_policy.displayName = 'changed-name'

    self._ExpectUpdate('policy-id', modified_policy)
    self.Run('monitoring policies update policy-id --policy \'{0}\' '
             '--display-name changed-name'.format(policy_str))

  def testUpdate_FieldMasks(self):
    policy = self.CreatePolicy(
        display_name='my-policy',
        conditions=self.conditions,
        enabled=True,
        documentation_content='documentation',
        notification_channels=self.notification_channels)
    policy_str = encoding.MessageToJson(policy)
    field_masks = ','.join(['disabled', 'notificationChannels'])

    self._ExpectUpdate('policy-id', policy, field_masks=field_masks)
    self.Run('monitoring policies update policy-id --policy \'{0}\' '
             '--fields {1}'.format(policy_str, field_masks))

  def testUpdate_ProhibitedFieldMasks(self,):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --fields: At most one of --fields'):
      self.Run('monitoring policies update policy-id --policy "{}" '
               '--display-name my-policy --fields disabled')

  def testUpdate_FieldMaskWithoutPolicy(self,):
    with self.AssertRaisesExceptionMatches(
        exceptions.OneOfArgumentsRequiredException,
        'One of arguments [--policy, --policy-from-file] is required: '
        'If --fields is specified.'):
      self.Run('monitoring policies update policy-id --fields disabled')

  def testUpdate_UpdateArgSpecified(self,):
    with self.AssertRaisesExceptionMatches(
        util.NoUpdateSpecifiedError,
        'Did not specify any flags for updating the policy.'):
      self.Run('monitoring policies update policy-id')


if __name__ == '__main__':
  test_case.main()
