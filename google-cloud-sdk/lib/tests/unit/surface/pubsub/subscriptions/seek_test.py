# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Test of the 'pubsub subscriptions seek' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsSeekTest(base.CloudPubsubTestBase, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_subscriptions.Seek
    properties.VALUES.core.user_output_enabled.Set(True)

  def testSeekToSnapshot(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    snap_ref = util.ParseSnapshot('snap', self.Project())

    seek_req = self.msgs.PubsubProjectsSubscriptionsSeekRequest(
        seekRequest=self.msgs.SeekRequest(snapshot=snap_ref.RelativeName()),
        subscription=sub_ref.RelativeName())
    self.svc.Expect(request=seek_req, response=self.msgs.SeekResponse())

    result = self.Run('pubsub subscriptions seek sub --snapshot snap')
    self.assertEqual(result['subscriptionId'], sub_ref.RelativeName())
    self.assertEqual(result['snapshotId'], snap_ref.RelativeName())
    self.assertNotIn('time', result)

  def testSeekToSnapshotFullUri(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    snap_ref = util.ParseSnapshot('snap', self.Project())

    seek_req = self.msgs.PubsubProjectsSubscriptionsSeekRequest(
        seekRequest=self.msgs.SeekRequest(snapshot=snap_ref.RelativeName()),
        subscription=sub_ref.RelativeName())
    self.svc.Expect(request=seek_req, response=self.msgs.SeekResponse())

    result = self.Run('pubsub subscriptions seek {} --snapshot {}'
                      .format(sub_ref.SelfLink(), snap_ref.SelfLink()))
    self.assertEqual(result['subscriptionId'], sub_ref.RelativeName())
    self.assertEqual(result['snapshotId'], snap_ref.RelativeName())
    self.assertNotIn('time', result)

  def testSeekToCrossProjectSnapshot(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    snap_ref = util.ParseSnapshot('snap', 'other-proj')

    seek_req = self.msgs.PubsubProjectsSubscriptionsSeekRequest(
        seekRequest=self.msgs.SeekRequest(snapshot=snap_ref.RelativeName()),
        subscription=sub_ref.RelativeName())
    self.svc.Expect(request=seek_req, response=self.msgs.SeekResponse())

    result = self.Run('pubsub subscriptions seek sub'
                      '    --snapshot snap'
                      '    --snapshot-project other-proj')
    self.assertEqual(result['subscriptionId'], sub_ref.RelativeName())
    self.assertEqual(result['snapshotId'], snap_ref.RelativeName())
    self.assertNotIn('time', result)

  @parameterized.parameters(
      ('2016-10-31T12:34:56Z', '2016-10-31T12:34:56.000000Z'),
      ('2019-01-24T15:15:25-05:00', '2019-01-24T20:15:25.000000Z'))
  def testSeekToTime(self, time_flag_value, time_parsed_value):
    sub_ref = util.ParseSubscription('sub', self.Project())

    seek_req = self.msgs.PubsubProjectsSubscriptionsSeekRequest(
        seekRequest=self.msgs.SeekRequest(time=time_parsed_value),
        subscription=sub_ref.RelativeName())
    self.svc.Expect(request=seek_req, response=self.msgs.SeekResponse())

    result = self.Run('pubsub subscriptions seek sub'
                      '    --time ' + time_flag_value)
    self.assertEqual(result['subscriptionId'], sub_ref.RelativeName())
    self.assertEqual(result['time'], time_parsed_value)
    self.assertNotIn('snapshotId', result)


if __name__ == '__main__':
  test_case.main()
