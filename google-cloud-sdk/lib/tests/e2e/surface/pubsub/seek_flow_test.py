# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Integration tests for CPS subscription and snapshot seek flows."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.pubsub import e2e_base


class PubsubIntegrationTest(e2e_base.CloudPubsubTestBase):
  """Integration tests for Cloud Pub/Sub seek."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testSeekFlow(self):
    id_gen = e2e_utils.GetResourceNameGenerator(prefix='cpstest')
    topic_name = id_gen.next()
    subscription_name = id_gen.next()

    with self._CreateTopic(topic_name):
      with self._CreateSubscription(topic_name, subscription_name):
        self.ClearAndRun('subscriptions seek {0} --time 2016-10-31T12:34:56Z'
                         ' --format=csv[no-heading](subscriptionId,time)'
                         .format(subscription_name))
        sub_ref = util.ParseSubscription(subscription_name, self.Project())
        self.AssertOutputContains(
            '{},2016-10-31T12:34:56.000000Z'.format(sub_ref.RelativeName()))

if __name__ == '__main__':
  test_case.main()
