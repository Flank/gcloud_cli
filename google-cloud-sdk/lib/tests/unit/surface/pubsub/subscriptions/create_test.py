# -*- coding: utf-8 -*- #
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

"""Test of the 'pubsub subscriptions create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SubscriptionsCreateTestBase(base.CloudPubsubTestBase):

  def SetUp(self):
    self.svc = self.client.projects_subscriptions.Create

  def ExpectCreatedSubscriptions(self, cmd, reqs):
    """Test that cmd results in the expected req sent and subscription created.

    Args:
      cmd: a `subscriptions create` command to pass to gcloud pubsub
      reqs: a list of expected request Subscription objects

    Returns:
      A list of serialized created Cloud Pub/Sub Subscription objects based on
      the request Subscription objects.
    """
    for req in reqs:
      # The request and response are of the same type.
      resp = copy.deepcopy(req)
      # Handle server-side defaults.
      if not resp.ackDeadlineSeconds:
        resp.ackDeadlineSeconds = 10
      if not resp.messageRetentionDuration:
        resp.messageRetentionDuration = '604800s'

      self.svc.Expect(request=req, response=resp)

    return list(self.Run(cmd))


class SubscriptionsCreateTest(SubscriptionsCreateTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testPullSubscriptionsCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 --ack-deadline=180',
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].ackDeadlineSeconds, 180)
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testSubscriptionFormatsProjectsPathsCorrectly(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', 'my_project')
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --ack-deadline 180 --topic topic1'
         ' --topic-project my_project'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testSubscriptionProjectFlags(self):
    sub_ref = util.ParseSubscription('subs1', 'proj1')
    topic_ref = util.ParseTopic('topic1', 'proj2')
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --ack-deadline 180 --topic topic1'
         ' --topic-project proj2 --project proj1'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testPullSubscriptionsCreateFullUri(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create {} --topic {} '
        '--ack-deadline=180'.format(sub_ref.SelfLink(), topic_ref.SelfLink()),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].ackDeadlineSeconds, 180)
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testPullSubscriptionsCreateFullUriDifferentTopicProject(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', 'my-project')
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create {} --topic {} '
        '--ack-deadline=180'.format(sub_ref.SelfLink(), topic_ref.SelfLink()),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].ackDeadlineSeconds, 180)
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testPullSubscriptionsCreateWithCrossProjectTopic(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', 'fake-topic-project')
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1 '
         '--topic-project fake-topic-project --ack-deadline=180'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].ackDeadlineSeconds, 180)

  def testPushSubscriptionsCreateNoOutput(self):
    sub_refs = [
        util.ParseSubscription('subs2', self.Project()),
        util.ParseSubscription('subs3', self.Project())]
    topic_ref = util.ParseTopic('topic2', self.Project())
    req_subscriptions = [
        self.msgs.Subscription(
            name=sub_ref.RelativeName(),
            topic=topic_ref.RelativeName(),
            pushConfig=self.msgs.PushConfig(
                pushEndpoint='https://my.appspot.com/push'))
        for sub_ref in sub_refs]

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs2 subs3 --topic topic2'
         ' --push-endpoint https://my.appspot.com/push'),
        req_subscriptions)

    self.assertEqual(2, len(result))
    for idx, sub_ref in enumerate(sub_refs):
      self.assertEqual(result[idx].ackDeadlineSeconds, 10)
      self.assertEqual(
          result[idx].name,
          sub_ref.RelativeName())
      self.assertEqual(
          result[idx].topic,
          topic_ref.RelativeName())
      self.assertEqual(
          result[idx].pushConfig.pushEndpoint,
          'https://my.appspot.com/push')

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testPushSubscriptionsCreateWithNonExistentTopic(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('non-existent', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName())

    self.svc.Expect(
        request=req_subscription,
        response=None,
        exception=http_error.MakeHttpError(404, 'Topic does not exist.'))

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to create the following: [subs1].'):
      self.Run('pubsub subscriptions create subs1 --topic non-existent')
    self.AssertErrContains(sub_ref.RelativeName())
    self.AssertErrContains('Topic does not exist.')

  def testPushSubscriptionsCreate(self):
    properties.VALUES.core.user_output_enabled.Set(True)

    sub_refs = [
        util.ParseSubscription('subs2', self.Project()),
        util.ParseSubscription('subs3', self.Project())]
    topic_ref = util.ParseTopic('topic2', self.Project())
    req_subscriptions = [
        self.msgs.Subscription(
            name=sub_ref.RelativeName(),
            topic=topic_ref.RelativeName(),
            pushConfig=self.msgs.PushConfig(
                pushEndpoint='https://my.appspot.com/push'))
        for sub_ref in sub_refs]

    self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs2 subs3 --topic topic2'
         ' --push-endpoint https://my.appspot.com/push'),
        req_subscriptions)

    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created subscription [{}].
Created subscription [{}].
""".format(sub_refs[0].RelativeName(), sub_refs[1].RelativeName()))

  def testPushSubscriptionsCreateWithOutputAndFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)

    sub_refs = [
        util.ParseSubscription('subs2', self.Project()),
        util.ParseSubscription('subs3', self.Project())]
    topic_ref = util.ParseTopic('topic2', self.Project())
    req_subscriptions = [
        self.msgs.Subscription(
            name=sub_ref.RelativeName(),
            topic=topic_ref.RelativeName(),
            pushConfig=self.msgs.PushConfig(
                pushEndpoint='https://my.appspot.com/push'))
        for sub_ref in sub_refs]

    self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs2 subs3 --topic topic2'
         ' --push-endpoint https://my.appspot.com/push'
         ' --format=csv[no-heading]'
         '(name,pushConfig.pushEndpoint,ackDeadlineSeconds)'),
        req_subscriptions)

    self.AssertOutputEquals("""\
{},https://my.appspot.com/push,10
{},https://my.appspot.com/push,10
""".format(sub_refs[0].RelativeName(), sub_refs[1].RelativeName()))
    self.AssertErrEquals("""\
Created subscription [{}].
Created subscription [{}].
""".format(sub_refs[0].RelativeName(), sub_refs[1].RelativeName()))


class SubscriptionsCreateGATest(SubscriptionsCreateTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSubscriptionsCreateNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 --ack-deadline=180',
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].ackDeadlineSeconds, 180)
    self.assertEqual(result[0].topic, topic_ref.RelativeName())


class SubscriptionsCreateBetaTest(SubscriptionsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testPullSubscriptionsCreateWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=180,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 --ack-deadline=180',
        [req_subscription])

    self.assertEqual(result[0]['subscriptionId'], sub_ref.RelativeName())
    self.assertEqual(result[0]['ackDeadlineSeconds'], 180)
    self.assertEqual(result[0]['topic'], topic_ref.RelativeName())

  def testSubscriptionsCreateLabels(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    labels = self.msgs.Subscription.LabelsValue(additionalProperties=[
        self.msgs.Subscription.LabelsValue.AdditionalProperty(
            key='key1', value='value1')])
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        labels=labels)

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 --labels key1=value1',
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())

  def testRetentionPullSubscriptionsCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        messageRetentionDuration='259200s',  # 3 days
        retainAckedMessages=True,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --retain-acked-messages --message-retention-duration=3d'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].retainAckedMessages, True)
    self.assertEqual(result[0].messageRetentionDuration, '259200s')

  def testRetentionPullSubscriptionsCreateWithOutputAndFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)

    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        messageRetentionDuration='259200s',  # 3 days
        retainAckedMessages=True,
        topic=topic_ref.RelativeName())

    self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --retain-acked-messages --message-retention-duration=3d'
         ' --format=csv[no-heading](name,retainAckedMessages,'
         'messageRetentionDuration)'),
        [req_subscription])

    self.AssertOutputEquals(
        'projects/{project}/subscriptions/subs1,True,259200s\n'
        .format(project=self.Project()))
    self.AssertErrEquals(
        'Created subscription [projects/fake-project/subscriptions/subs1].\n')

  def testNoRetentionPullSubscriptionsCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        retainAckedMessages=False,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --no-retain-acked-messages'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].retainAckedMessages, False)

  def testNoRetentionPullSubscriptionsCreateWithOutputAndFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)

    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        retainAckedMessages=False,
        topic=topic_ref.RelativeName())

    self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --no-retain-acked-messages --format=csv[no-heading](name,'
         'retainAckedMessages)'),
        [req_subscription])

    self.AssertOutputEquals('{},False\n'.format(sub_ref.RelativeName()))
    self.AssertErrEquals(
        'Created subscription [{}].\n'.format(sub_ref.RelativeName()))

  def testNoExpirationSubscriptionCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        expirationPolicy=self.msgs.ExpirationPolicy())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --expiration-period never'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].expirationPolicy.ttl, None)

  def testExpirationSubscriptionCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        expirationPolicy=self.msgs.ExpirationPolicy(ttl='604800s'))

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --expiration-period 7d'),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].expirationPolicy.ttl, '604800s')


class SubscriptionsCreateAlphaTest(SubscriptionsCreateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
