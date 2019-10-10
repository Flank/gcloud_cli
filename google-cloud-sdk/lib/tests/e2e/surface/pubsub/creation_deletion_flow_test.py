# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Integration tests for topic, subscription, and snapshot creation/deletion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.pubsub import e2e_base


class PubsubIntegrationTest(e2e_base.CloudPubsubTestBase):
  """Integration tests for Cloud Pub/Sub."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreationUpdateDeletionFlow(self):
    id_gen = e2e_utils.GetResourceNameGenerator(prefix='cpstest')
    topic_name = next(id_gen)
    subscription_name = next(id_gen)
    snapshot_name = next(id_gen)

    with self._CreateTopic(topic_name), \
         self._CreateSubscription(topic_name, subscription_name, 20) as sub, \
         self._CreateSnapshot(topic_name, subscription_name, snapshot_name):
      self.assertEqual(20, sub.ackDeadlineSeconds)
      result = self.ClearAndRun('subscriptions update {0} --ack-deadline=40'
                                ' --format=disable'.format(subscription_name))
      sub_ref = util.ParseSubscription(subscription_name, self.Project())
      self.AssertErrEquals(
          'Updated subscription [{}].\n'.format(sub_ref.RelativeName()))
      self.assertEqual(40, result.ackDeadlineSeconds)

      result = self.ClearAndRun('snapshots describe {}'.format(snapshot_name))
      snapshot_ref = util.ParseSnapshot(snapshot_name, self.Project())
      self.assertEqual(result.name, snapshot_ref.RelativeName())


if __name__ == '__main__':
  test_case.main()
