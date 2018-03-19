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
"""Test of the 'pubsub topics list-subscriptions' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsListSubscriptionsTest(base.CloudPubsubTestBase,
                                  sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_topics_subscriptions.List
    self.topic_ref = util.ParseTopic('topic', self.Project())

  def _CreateSubscriptionNames(self, names):
    return [util.ParseSubscription(name, self.Project()).RelativeName()
            for name in names]

  def testListTopicSubscriptions(self):
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic')
    self.AssertOutputEquals("""\
---
  projects/{0}/subscriptions/subs1
---
  projects/{0}/subscriptions/subs2
---
  projects/{0}/subscriptions/subs3
""".format(self.Project()))

  def testListTopicSubscriptionsUri(self):
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic --uri')

    expected_output = '\n'.join([
        self.GetSubscriptionUri(sub) for sub in subscriptions_names])
    self.AssertOutputContains(expected_output, normalize_space=True)

  def testListTopicSubscriptionsFullUri(self):
    sub_names = ['subs1', 'subs2', 'subs3']
    subscriptions_names = self._CreateSubscriptionNames(sub_names)

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions {} --format=list'
             .format(self.topic_ref.SelfLink()))

    output = '\n'.join([' - {}'.format(name) for name in subscriptions_names])
    self.AssertOutputContains(output)

  def testListTopicSubscriptionsWithFilter(self):
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic'
             ' --filter="subs1 OR subs2"')

    self.AssertOutputEquals("""\
---
  projects/{0}/subscriptions/subs1
---
  projects/{0}/subscriptions/subs2
""".format(self.Project()))

  def testListTopicSubscriptionsNoMatch(self):
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic'
             ' --filter=no-match')
    self.AssertOutputEquals('')


class TopicsListSubscriptionsBetaTest(TopicsListSubscriptionsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testListTopicSubscriptionsWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic')

    self.AssertOutputEquals("""\
---
projectId: {0}
subscription: projects/{0}/subscriptions/subs1
subscriptionId: subs1
---
projectId: {0}
subscription: projects/{0}/subscriptions/subs2
subscriptionId: subs2
---
projectId: {0}
subscription: projects/{0}/subscriptions/subs3
subscriptionId: subs3
""".format(self.Project()))


class TopicsListSubscriptionsGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_topics_subscriptions.List

  def _CreateSubscriptionNames(self, names):
    return [util.ParseSubscription(name, self.Project()).RelativeName()
            for name in names]

  def testTopicsListSubscriptionsNoLegacyOutput(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    properties.VALUES.pubsub.legacy_output.Set(True)
    topic_ref = util.ParseTopic('topic', self.Project())
    subscriptions_names = self._CreateSubscriptionNames(
        ['subs1', 'subs2', 'subs3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
            topic=topic_ref.RelativeName()),
        response=self.msgs.ListTopicSubscriptionsResponse(
            subscriptions=subscriptions_names))

    self.Run('pubsub topics list-subscriptions topic')
    self.AssertOutputEquals("""\
---
  projects/{0}/subscriptions/subs1
---
  projects/{0}/subscriptions/subs2
---
  projects/{0}/subscriptions/subs3
""".format(self.Project()))


if __name__ == '__main__':
  test_case.main()
