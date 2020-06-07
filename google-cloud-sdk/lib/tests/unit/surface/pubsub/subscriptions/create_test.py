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

"""Test of the 'pubsub subscriptions create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
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


class SubscriptionsCreateTest(SubscriptionsCreateTestBase,
                              parameterized.TestCase):

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

  def testNoExpirationSubscriptionCreate(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        expirationPolicy=self.msgs.ExpirationPolicy())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1'
         ' --expiration-period never'), [req_subscription])

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
         ' --expiration-period 7d'), [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].expirationPolicy.ttl, '604800s')

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

  @parameterized.parameters(
      (' --dead-letter-topic topic2 --max-delivery-attempts 5', 'topic2', 5),
      (' --dead-letter-topic topic2 --max-delivery-attempts 100', 'topic2',
       100), (' --dead-letter-topic topic2', 'topic2', None),
      (' --dead-letter-topic projects/other-project/topics/topic2 '
       '--max-delivery-attempts 5', 'projects/other-project/topics/topic2', 5),
      (' --dead-letter-topic topic2 --max-delivery-attempts 5 '
       '--dead-letter-topic-project other-project',
       'projects/other-project/topics/topic2', 5))
  def testDeadLetterPolicyPullSubscriptionsCreate(self, dead_letter_flags,
                                                  dead_letter_topic,
                                                  max_delivery_attempts):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    dead_letter_policy = self.msgs.DeadLetterPolicy(
        deadLetterTopic=util.ParseTopic(dead_letter_topic,
                                        self.Project()).RelativeName(),
        maxDeliveryAttempts=max_delivery_attempts)
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        deadLetterPolicy=dead_letter_policy)

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1' +
         dead_letter_flags), [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].deadLetterPolicy, dead_letter_policy)

  @parameterized.parameters(
      (' --dead-letter-topic topic2 --max-delivery-attempts 4',
       cli_test_base.MockArgumentError,
       'argument --max-delivery-attempts: Value must be greater than or equal '
       'to 5; received: 4'),
      (' --dead-letter-topic topic2 --max-delivery-attempts 101',
       cli_test_base.MockArgumentError,
       'argument --max-delivery-attempts: Value must be less than or equal to '
       '100; received: 101'),
      (' --max-delivery-attempts 5', exceptions.RequiredArgumentException,
       'Missing required argument [DEAD_LETTER_TOPIC]: --dead-letter-topic'))
  def testDeadLetterPolicyExceptionPullSubscriptionsCreate(
      self, dead_letter_flags, exception, exception_message):
    with self.AssertRaisesExceptionMatches(exception, exception_message):
      self.Run('pubsub subscriptions create subs1 --topic topic1' +
               dead_letter_flags)

  @parameterized.parameters(
      (' --min-retry-delay 20s --max-retry-delay 50s', '20s', '50s'),
      (' --min-retry-delay 20s', '20s', None),
      (' --max-retry-delay 50s', None, '50s'))
  def testRetryPolicyPullSubscriptionsCreate(self, retry_policy_flags,
                                             min_retry_delay, max_retry_delay):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    retry_policy = self.msgs.RetryPolicy(
        minimumBackoff=min_retry_delay, maximumBackoff=max_retry_delay)
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        retryPolicy=retry_policy)

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1' +
         retry_policy_flags), [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].retryPolicy, retry_policy)

  @parameterized.parameters(
      (' --min-retry-delay 0s --max-retry-delay 700s',
       cli_test_base.MockArgumentError,
       'argument --max-retry-delay: value must be less than or equal '
       'to 600s; received: 700s'),
      (' --min-retry-delay 800s --max-retry-delay 500s',
       cli_test_base.MockArgumentError,
       'argument --min-retry-delay: value must be less than or equal '
       'to 600s; received: 800s'))
  def testRetryPolicyExceptionPullSubscriptionsCreate(self, retry_flags,
                                                      exception,
                                                      exception_message):
    with self.AssertRaisesExceptionMatches(exception, exception_message):
      self.Run('pubsub subscriptions create subs1 --topic topic1' + retry_flags)


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

  def testSubscriptionsCreateAuthenticatedPush(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        pushConfig=self.msgs.PushConfig(
            pushEndpoint='https://example.com/push',
            oidcToken=self.msgs.OidcToken(
                serviceAccountEmail='account@example.com',
                audience='my-audience')))

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 '
        '--push-endpoint=https://example.com/push '
        '--push-auth-service-account=account@example.com '
        '--push-auth-token-audience=my-audience', [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].pushConfig.pushEndpoint,
                     'https://example.com/push')
    self.assertEqual(result[0].pushConfig.oidcToken.serviceAccountEmail,
                     'account@example.com')
    self.assertEqual(result[0].pushConfig.oidcToken.audience, 'my-audience')

  def testSubscriptionsCreateAuthenticatedPushNoAudience(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        pushConfig=self.msgs.PushConfig(
            pushEndpoint='https://example.com/push',
            oidcToken=self.msgs.OidcToken(
                serviceAccountEmail='account@example.com')))

    result = self.ExpectCreatedSubscriptions(
        'pubsub subscriptions create subs1 --topic topic1 '
        '--push-endpoint=https://example.com/push '
        '--push-auth-service-account=account@example.com', [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].pushConfig.pushEndpoint,
                     'https://example.com/push')
    self.assertEqual(result[0].pushConfig.oidcToken.serviceAccountEmail,
                     'account@example.com')
    self.assertEqual(result[0].pushConfig.oidcToken.audience, None)


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


class SubscriptionsCreateAlphaTest(SubscriptionsCreateBetaTest,
                                   parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @parameterized.parameters((' --enable-message-ordering', True),
                            (' --no-enable-message-ordering', False))
  def testOrderedPullSubscriptionsCreate(self, ordering_flag,
                                         ordering_property):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    req_subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        enableMessageOrdering=ordering_property,
        topic=topic_ref.RelativeName())

    result = self.ExpectCreatedSubscriptions(
        ('pubsub subscriptions create subs1 --topic topic1' + ordering_flag),
        [req_subscription])

    self.assertEqual(result[0].name, sub_ref.RelativeName())
    self.assertEqual(result[0].topic, topic_ref.RelativeName())
    self.assertEqual(result[0].enableMessageOrdering, ordering_property)


if __name__ == '__main__':
  test_case.main()
