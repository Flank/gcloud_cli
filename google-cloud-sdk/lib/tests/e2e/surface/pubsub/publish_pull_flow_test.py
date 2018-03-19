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
"""Integration tests for CPS topic and subscription publish/pull flows."""
import random
import time

from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.pubsub import e2e_base


class PubsubIntegrationTest(e2e_base.CloudPubsubTestBase):
  """Integration tests for Cloud Pub/Sub."""

  def _PublishMessages(self, topic_name):
    """Publishes messages with random numbers from 0 to 20.

    Args:
      topic_name: (string) Name of the topic to publish messages to.

    Returns:
      Returns a list of random ints that correspond to the payload of the
      published messages.
    """
    messages = []
    random.seed(time.time())

    for _ in xrange(3):
      rmsg = random.randint(0, 20)
      self.Run(
          'pubsub topics publish {0} --message msg_{1} --attribute k1=v1,k2=v2'
          .format(topic_name, rmsg))
      messages.append(rmsg)
    self.AssertOutputMatches(r'(messageIds:\n- \'.*\'\n){3}')
    self.ClearOutput()
    return messages

  def _PullMessages(self, subscription_name, messages_to_check):
    self.ClearAndRun(
        'subscriptions pull {0} --auto-ack'.format(subscription_name))
    for msg in messages_to_check:
      self.AssertOutputMatches(
          r'msg_{0} | \d+ | k2=v2 k1=v1'.format(msg), normalize_space=True)
    self.ClearOutput()

  def testPublishAndPullFlow(self):
    """Tests the topics publish and subscriptions pull Cloud Pub/Sub flow.

    The test creates temporary topic and subscription. It then publishes 3
    messages with a random int as a payload. It then pulls messages from the
    subscription and matches them against the random ints sent. The test passes
    if the payload of the published messages are present in the messages pulled
    from the subscription.
    """
    id_gen = e2e_utils.GetResourceNameGenerator(prefix='cpstest')
    topic_name = id_gen.next()
    subscription_name = id_gen.next()

    with self._CreateTopic(topic_name):
      with self._CreateSubscription(topic_name, subscription_name):
        messages = self._PublishMessages(topic_name)
        self._PullMessages(subscription_name, messages)


if __name__ == '__main__':
  test_case.main()
