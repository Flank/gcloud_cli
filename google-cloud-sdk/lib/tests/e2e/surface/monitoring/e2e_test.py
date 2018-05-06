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
"""E2E tests for `gcloud monitoring` commands."""
import contextlib

from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.surface.monitoring import test_data


class MonitoringE2eTests(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def _CreateAlertPolicy(self):
    policy_file = self.Touch(self.temp_path,
                             'my_policy.json',
                             contents=test_data.ALERT_POLICY)
    policy_name = None
    try:
      policy = self.Run('monitoring policies create --policy-from-file {} '
                        '--no-enabled'.format(policy_file))
      policy_name = policy.name
      yield policy
    finally:
      if policy_name:
        self.Run('monitoring policies delete {} --quiet '.format(policy_name))

  @contextlib.contextmanager
  def _CreateNotificationChannel(self):
    channel_name = None
    try:
      channel = self.Run('monitoring channels create --no-enabled '
                         '--display-name "My Channel" --type email '
                         '--channel-labels email_address=nobody@google.com')
      channel_name = channel.name
      yield channel
    finally:
      if channel_name:
        self.Run('monitoring channels delete {} --force --quiet'
                 .format(channel_name))

  def testMonitoringCommands(self):
    condition_file = self.Touch(self.temp_path,
                                'my_condition.json',
                                contents=test_data.CONDITION)
    with self._CreateAlertPolicy() as policy, \
         self._CreateNotificationChannel() as channel:
      self.assertFalse(policy.enabled)
      self.assertEqual([], policy.notificationChannels)

      # Test enabling and adding a notification channel
      policy = self.Run('monitoring policies update {0} --enabled '
                        '--add-notification-channels {1}'.format(
                            policy.name, channel.name))
      self.assertTrue(policy.enabled)
      self.assertEqual([channel.name], policy.notificationChannels)

      # Test creating and deleting conditions
      self.assertEqual(1, len(policy.conditions))
      policy = self.Run('monitoring policies conditions create {0} '
                        '--condition-from-file {1}'.format(
                            policy.name, condition_file))
      self.assertEqual(2, len(policy.conditions))
      self.assertTrue(
          any([c.displayName == 'cores' for c in policy.conditions]))
      policy = self.Run('monitoring policies conditions delete {0} --quiet'
                        .format(policy.conditions[0].name))
      self.assertEqual(1, len(policy.conditions))


if __name__ == '__main__':
  test_case.main()
