# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""E2E tests for `gcloud monitoring` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import uuid

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.surface.monitoring import test_data
import six


class MonitoringE2eTestsBase(e2e_base.WithServiceAuth,
                             cli_test_base.CliTestBase):

  @retry.RetryOnException(max_retrials=4, jitter_ms=2000,
                          sleep_ms=1000, exponential_sleep_multiplier=2)
  def _RunCommandWithRetries(self, command_str):
    return self.Run(command_str)

  @contextlib.contextmanager
  def _CreateAlertPolicy(self, policy_contents):
    policy_file = self.Touch(self.temp_path,
                             'my_policy.json',
                             contents=policy_contents)
    policy_name = None
    try:
      policy = self._RunCommandWithRetries(
          'monitoring policies create'
          ' --policy-from-file {} --no-enabled'.format(policy_file)
      )
      policy_name = policy.name
      yield policy
    finally:
      if policy_name:
        self._RunCommandWithRetries('monitoring policies delete {} '
                                    '--quiet '.format(policy_name))

  @contextlib.contextmanager
  def _CreateNotificationChannel(self, param_string):
    channel_name = None
    try:
      channel = self._RunCommandWithRetries(
          ' '.join(['monitoring channels create', param_string])
      )
      channel_name = channel.name

      yield channel
    finally:
      if channel_name:
        self._RunCommandWithRetries('monitoring channels delete {} '
                                    '--force --quiet'.format(channel_name))


class AlphaMonitoringE2eTests(MonitoringE2eTestsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testMonitoringCommands(self):
    condition_file = self.Touch(self.temp_path,
                                'my_condition.json',
                                contents=test_data.CONDITION)
    create_channel_params = ('--type email '
                             '--channel-labels email_address=nobody@google.com '
                             '--no-enabled --display-name "My Channel" ')

    with self._CreateAlertPolicy(test_data.ALERT_POLICY) as policy, \
        self._CreateNotificationChannel(create_channel_params) as channel, \
        self._CreateNotificationChannel(create_channel_params) as channel2:
      self.assertFalse(policy.enabled)
      self.assertEqual([], policy.notificationChannels)

      # Test enabling and adding a notification channel
      policy = self._RunCommandWithRetries(
          'monitoring policies update {0} --enabled '
          '--add-notification-channels {1}'.format(policy.name, channel.name)
      )
      self.assertTrue(policy.enabled)
      self.assertEqual([channel.name], policy.notificationChannels)

      # Test updating a notification channel
      policy = self._RunCommandWithRetries(
          'monitoring policies update {0} --enabled '
          '--set-notification-channels {1}'.format(policy.name, channel2.name)
      )
      self.assertTrue(policy.enabled)
      self.assertEqual([channel2.name], policy.notificationChannels)

      # Test creating and deleting conditions
      self.assertEqual(1, len(policy.conditions))
      policy = self._RunCommandWithRetries(
          'monitoring policies conditions create {0} '
          '--condition-from-file {1}'.format(policy.name, condition_file)
      )
      self.assertEqual(2, len(policy.conditions))
      self.assertTrue(
          any([c.displayName == 'cores' for c in policy.conditions]))
      policy = self._RunCommandWithRetries(
          'monitoring policies conditions delete {0} '
          '--quiet'.format(policy.conditions[0].name)
      )
      self.assertEqual(1, len(policy.conditions))

  def testCreatePolicyWithoutAggregations(self):
    with self._CreateAlertPolicy(test_data.ALERT_POLICY_NO_AGGREGATIONS) \
        as policy:
      self.assertFalse(policy.enabled)


class BetaMonitoringE2eTests(MonitoringE2eTestsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testNotificationChannelDescriptorsDescribe(self):
    email_descriptor_by_type = self.Run(
        'monitoring channel-descriptors describe email')
    email_descriptor_by_name = self.Run(
        'monitoring channel-descriptors describe '
        'projects/{}/notificationChannelDescriptors/email'.format(
            self.Project()))
    self.assertEqual(email_descriptor_by_name, email_descriptor_by_type)
    email_descriptor = email_descriptor_by_type
    self.assertEqual(email_descriptor.type, 'email')
    self.assertTrue(
        any([label.key == 'email_address' for label in email_descriptor.labels
            ]))

  def testNotificationChannelDescriptorsList(self):
    descriptors = list(
        self.Run('monitoring channel-descriptors list --format=disable'))
    self.assertTrue(descriptors)
    self.assertTrue(
        any([descriptor.type == 'email' for descriptor in descriptors]),
        msg='descriptors:\n{}'.format(descriptors))

  def testNotificationChannelCommands(self):
    run_id = six.text_type(uuid.uuid4())
    with self._CreateNotificationChannel(
        '--type=email --channel-labels=email_address=noreply@google.com '
        '--display-name="Test Channel A" '
        '--user-labels=role=primary-oncall,team=backend,run={}'.format(run_id)
    ) as channel_a, \
        self._CreateNotificationChannel(
            '--type=email --channel-labels=email_address=noreply@google.com '
            '--display-name="Test Channel B" '
            '--user-labels=role=secondary-oncall,team=backend,run={}'.format(
                run_id),) as channel_b, \
        self._CreateNotificationChannel(
            '--type=webhook_tokenauth '
            '--channel-labels=url=https://devnull.google.com/invalid '
            '--display-name="Test Channel C" --no-enabled '
            '--user-labels=role=secondary-oncall,team=frontend,run={}'.format(
                run_id)) as channel_c:
      all_channels = [channel_a, channel_b, channel_c]
      self.assertTrue(channel_a.enabled)
      self.assertTrue(channel_b.enabled)
      self.assertFalse(channel_c.enabled)

      channel_a_copy = self.Run(
          'monitoring channels describe {}'.format(channel_a.name)
      )
      self.assertChannelsEqual(channel_a, channel_a_copy)
      secondary_oncallers = list(
          self.Run('monitoring channels list --format=disable '
                   '--filter="user_labels.role=\'secondary-oncall\' '
                   'AND user_labels.run=\'{}\'" '
                   '--sort-by=display_name'.format(run_id))
      )
      self.assertLen(secondary_oncallers, 2,
                     msg='All channels: {}'.format(all_channels))
      self.assertChannelsEqual(secondary_oncallers[0], channel_b)
      self.assertChannelsEqual(secondary_oncallers[1], channel_c)

      last_backend_team_member_by_name = list(
          self.Run('monitoring channels list --format=disable '
                   '--filter="user_labels.team=\'backend\' '
                   'AND user_labels.run=\'{}\'" --sort-by=~display_name '
                   '--limit=1'.format(run_id)))
      self.assertLen(last_backend_team_member_by_name, 1,
                     msg='All channels: {}'.format(all_channels))
      self.assertChannelsEqual(last_backend_team_member_by_name[0],
                               channel_b)

      channel_a = self._RunCommandWithRetries(
          'monitoring channels update {} --display-name="Zainy Zebra"'
          .format(channel_a.name)
      )
      all_channels = [channel_a, channel_b, channel_c]
      last_backend_team_member_by_name = list(
          self.Run('monitoring channels list --format=disable '
                   '--filter="user_labels.team=\'backend\' '
                   'AND user_labels.run=\'{}\'" --sort-by=~display_name '
                   '--limit=1'.format(run_id)))
      self.assertLen(last_backend_team_member_by_name, 1,
                     msg='All channels: {}'.format(all_channels))
      self.assertChannelsEqual(last_backend_team_member_by_name[0],
                               channel_a)

  def assertLen(self, obj, count, msg=None):
    exposition = 'size of {} is {}, not {}'.format(obj, len(obj), count)
    if msg:
      exposition = '{}; {}'.format(exposition, msg)
    self.assertEqual(len(obj), count, msg=exposition)

  def assertChannelsEqual(self, a, b, msg=None):
    self._sortLabels(a)
    self._sortLabels(b)
    exposition = 'expected:\n{}\n...to equal:\n{}'.format(a, b)
    if msg:
      exposition = '{}\n\n{}'.format(exposition, msg)
    self.assertEqual(a, b, msg=exposition)

  def _sortLabels(self, channel):
    channel.labels.additionalProperties = sorted(
        channel.labels.additionalProperties, key=lambda x: x.key)
    channel.userLabels.additionalProperties = sorted(
        channel.userLabels.additionalProperties, key=lambda x: x.key)


if __name__ == '__main__':
  test_case.main()
