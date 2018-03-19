# Copyright 2015 Google Inc. All Rights Reserved.
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

import os
import time

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import update_check
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.updater import util


class LastUpdateCheckTests(util.Base, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.config.Paths.update_check_cache_path',
                    new=os.path.join(self.sdk_root_path, 'check_file'))

  def testBasicUpdateData(self):
    time_mock = self.StartObjectPatch(time, 'time', return_value=1)

    with update_check.UpdateCheckData() as checker:
      # Everything starts as empty because the cache doesn't exist.
      self.assertEquals(0, checker.LastUpdateCheckTime())
      self.assertEquals(0, checker.LastUpdateCheckRevision())
      self.assertFalse(checker.UpdatesAvailable())
      self.assertEquals(checker.SecondsSinceLastUpdateCheck(), 1)
      self.assertFalse(checker.ShouldDoUpdateCheck())

      # Time elapses, should report that we should do an update check.
      check_plus_one = (
          update_check.UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS + 1)
      time_mock.return_value = check_plus_one
      self.assertEquals(checker.SecondsSinceLastUpdateCheck(), check_plus_one)
      self.assertTrue(checker.ShouldDoUpdateCheck())

      # Set the current state from this snapshot.
      snapshot = self.CreateSnapshotFromComponents(
          20000101000000, [], None,
          notifications=[
              {
                  'id': 'basic',
                  'trigger': {'frequency': 2},
                  'notification': {'custom_message': 'custom'}
              }
          ])
      checker.SetFromSnapshot(snapshot, True)

      # Check that the update was done, and all attributes cached correctly.
      self.assertEquals(check_plus_one, checker.LastUpdateCheckTime())
      self.assertEquals(20000101000000, checker.LastUpdateCheckRevision())
      self.assertTrue(checker.UpdatesAvailable())
      self.assertEquals(checker.SecondsSinceLastUpdateCheck(), 0)
      self.assertFalse(checker.ShouldDoUpdateCheck())

      # Notify that an update is available because we haven't before.
      self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
      checker.Notify(command_path=None)
      self.AssertErrContains('custom')
      self.assertEqual(check_plus_one,
                       checker._data.last_nag_times.get('basic'))
      self.ClearErr()

      # Time advances, but not enough to nag again.
      time_mock.return_value = check_plus_one + 1
      checker.Notify(command_path=None)
      self.AssertErrNotContains('custom')
      self.assertEqual(check_plus_one,
                       checker._data.last_nag_times.get('basic'))

      # Time advances enough to nag again.  Check that nag time is updated.
      time_mock.return_value = check_plus_one + 2
      checker.Notify(command_path=None)
      self.AssertErrContains('custom')
      self.assertEqual(check_plus_one + 2,
                       checker._data.last_nag_times.get('basic'))

    # Reload the cache and make sure everything was saved correctly.
    with update_check.UpdateCheckData() as checker:
      self.assertEquals(check_plus_one, checker.LastUpdateCheckTime())
      self.assertEquals(20000101000000, checker.LastUpdateCheckRevision())
      self.assertTrue(checker.UpdatesAvailable())
      self.assertEquals(checker.SecondsSinceLastUpdateCheck(), 2)
      self.assertFalse(checker.ShouldDoUpdateCheck())
      self.assertEqual(check_plus_one + 2,
                       checker._data.last_nag_times.get('basic'))

  def testBadFile(self):
    with update_check.UpdateCheckData() as checker:
      self.assertEquals(0, checker.LastUpdateCheckTime())
      checker._data.last_update_check_time = 5
      self.assertEquals(5, checker.LastUpdateCheckTime())

    with open(config.Paths().update_check_cache_path, 'w') as f:
      f.write('junk')

    with update_check.UpdateCheckData() as checker:
      # Make sure there was no error and the file just gets reset.
      self.assertEquals(0, checker.LastUpdateCheckTime())

  def testConditionMatching(self):
    freq = update_check.UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS
    time_mock = self.StartObjectPatch(time, 'time')
    time_mock.return_value = freq
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.version',
                    new='1.2.3')
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.revision',
                    new=20000101000000)

    with update_check.UpdateCheckData() as checker:
      self.assertEquals(checker.SecondsSinceLastUpdateCheck(), freq)
      self.assertTrue(checker.ShouldDoUpdateCheck())

      # Set the current state from this snapshot.
      snapshot = self.CreateSnapshotFromComponents(
          20000101000005, [], None,
          notifications=[
              {
                  'id': 'basic',
                  'trigger': {'frequency': 2},
                  'notification': {'custom_message': 'custom'}
              },
          ])

      # Doesn't match start version
      snapshot.sdk_definition.notifications[0].condition = schemas.Condition(
          start_version='2.0.0', end_version=None, version_regex=None, age=None,
          check_components=True)
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertFalse(checker.UpdatesAvailable())

      # Doesn't match end version
      snapshot.sdk_definition.notifications[0].condition = schemas.Condition(
          start_version=None, end_version='0.0.0', version_regex=None, age=None,
          check_components=True)
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertFalse(checker.UpdatesAvailable())

      # Doesn't match age
      snapshot.sdk_definition.notifications[0].condition = schemas.Condition(
          start_version=None, end_version=None, version_regex=None, age=100,
          check_components=True)
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertFalse(checker.UpdatesAvailable())

      # Doesn't match check_components.
      snapshot.sdk_definition.notifications[0].condition = schemas.Condition(
          start_version=None, end_version=None, version_regex=None, age=None,
          check_components=True)
      checker.SetFromSnapshot(snapshot, False, force=True)
      self.assertFalse(checker.UpdatesAvailable())

      # Matches.
      snapshot.sdk_definition.notifications[0].condition = schemas.Condition(
          None, None, None, None, True)
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertTrue(checker.UpdatesAvailable())

      # Add in another notification, check that they both get stored.
      snapshot.sdk_definition.notifications.append(
          schemas.NotificationSpec.FromDictionary({'id': 'default'}))
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertEqual(['basic', 'default'],
                       [n.id for n in checker._data.notifications])

      # Remove that notification, ensure it gets removed.
      del snapshot.sdk_definition.notifications[1]
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertEqual(['basic'], [n.id for n in checker._data.notifications])

  def testNags(self):

    def CheckOutput(basic, another):
      self.AssertErrContains('basic', success=basic)
      self.AssertErrContains('another', success=another)
      self.AssertErrNotContains('not_activated')
      self.ClearErr()

    time_mock = self.StartObjectPatch(time, 'time', return_value=0)
    out_mock = self.StartObjectPatch(log._ConsoleWriter, 'isatty')
    out_mock.return_value = True

    snapshot = self.CreateSnapshotFromComponents(
        20000101000000, [], None,
        notifications=[
            {
                'id': 'basic',
                'trigger': {'frequency': 2, 'command_regex': r'gcloud\..+'},
                'notification': {'custom_message': 'basic'}
            },
            {
                'id': 'another',
                'trigger': {'frequency': 3},
                'notification': {'custom_message': 'another'}
            },
            {
                'id': 'not_activated',
                'condition': {'version_regex': 'xxxxxxx'},
                'trigger': {'frequency': 1},
                'notification': {'custom_message': 'not_activated'}
            }
        ])

    with update_check.UpdateCheckData() as checker:
      checker.SetFromSnapshot(snapshot, True)

      # Ensure 'not_activated' did not get picked up.
      self.assertEqual(['basic', 'another'],
                       [n.id for n in checker._data.notifications])

      # Time 0, nothing to notify
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)

      # Time 1, nothing to notify
      time_mock.return_value = 1
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)

      # Time 2, turn not in a terminal, don't notify
      time_mock.return_value = 2
      out_mock.return_value = False
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)
      # Time 2, notify 'basic'
      out_mock.return_value = True
      # Command is not correct for notification.
      checker.Notify(command_path='asdf')
      CheckOutput(False, False)
      # Matching command should notify.
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(True, False)
      # Second time won't notify because time has not expired
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)

      # Time 4, both are eligible, 'basic' goes first because it comes first
      # in the list.
      time_mock.return_value = 4
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(True, False)
      # On second command, 'basic' has already been notified so now 'another'
      # goes.
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, True)

      # Time 5, nothing to notify
      time_mock.return_value = 5
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)

      # Time 6, notify 'basic'
      time_mock.return_value = 6
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(True, False)
      checker.Notify(command_path='gcloud.foo')
      CheckOutput(False, False)

      # Make sure the last nag times are correctly recorded.
      self.assertEqual(6, checker._data.last_nag_times.get('basic'))
      self.assertEqual(4, checker._data.last_nag_times.get('another'))

      # Remove a notification and make sure the last nag time gets cleaned up
      # and the other is not cleared.
      del snapshot.sdk_definition.notifications[0]
      checker.SetFromSnapshot(snapshot, True, force=True)
      self.assertNotIn('basic', checker._data.last_nag_times)
      self.assertEqual(4, checker._data.last_nag_times.get('another'))

      # Set from incompat schema.  Make sure we get a single notification for
      # that and remove others.
      checker.SetFromIncompatibleSchema()
      self.assertEqual(['incompatible'],
                       [n.id for n in checker._data.notifications])
      self.assertEqual({}, checker._data.last_nag_times)

      # Hasn't been enough time to notify
      checker.Notify(command_path='gcloud.foo')
      self.AssertErrNotContains('gcloud components update')
      self.ClearErr()
      # Now there is enough time to notify.
      time_mock.return_value = 604801
      checker.Notify(command_path='gcloud.foo')
      self.AssertErrContains('gcloud components update')
      self.ClearErr()

      # Make sure last nag is recorded per usual.
      self.assertEqual(604801, checker._data.last_nag_times.get('incompatible'))
      checker.SetFromIncompatibleSchema()
      # Make sure last nag was not cleared.
      self.assertEqual(604801, checker._data.last_nag_times.get('incompatible'))

  def testUpdatesAvailableNoCheckComponents(self):
    with update_check.UpdateCheckData() as checker:
      # Everything starts as empty because the cache doesn't exist.
      self.assertFalse(checker.UpdatesAvailable())

      snapshot = self.CreateSnapshotFromComponents(
          20000101000000, [],
          None,
          notifications=[{
              'id': 'test',
              'condition': {
                  'check_components': False
              }
          }])
      checker.SetFromSnapshot(snapshot, True)
      self.assertEquals(1, len(checker._data.notifications))
      self.assertFalse(checker.UpdatesAvailable())

      snapshot = self.CreateSnapshotFromComponents(
          20000101000001, [],
          None,
          notifications=[{
              'id': 'test',
              'condition': {
                  'check_components': True
              }
          }])
      checker.SetFromSnapshot(snapshot, True)
      self.assertEquals(1, len(checker._data.notifications))
      self.assertTrue(checker.UpdatesAvailable())


if __name__ == '__main__':
  test_case.main()
