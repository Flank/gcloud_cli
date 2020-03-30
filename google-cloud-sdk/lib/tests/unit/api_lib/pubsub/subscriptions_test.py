# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the Cloud Pub/Sub Subscriptions library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.pubsub import base

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class MockArgs(object):
  push_endpoint = None


class SubscriptionsTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.subscriptions_client = subscriptions.SubscriptionsClient(self.client,
                                                                  self.msgs)
    self.subscriptions_service = self.client.projects_subscriptions

  def testAck(self):
    ack_ids = [str(i) for i in range(3)]
    sub_ref = util.ParseSubscription('sub1', self.Project())

    self.subscriptions_service.Acknowledge.Expect(
        self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        self.msgs.Empty())
    self.subscriptions_client.Ack(ack_ids, sub_ref)

  def testCreate(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())
    labels = self.msgs.Subscription.LabelsValue(additionalProperties=[
        self.msgs.Subscription.LabelsValue.AdditionalProperty(
            key='label1', value='value1')])
    subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        ackDeadlineSeconds=20,
        enableMessageOrdering=True,
        deadLetterPolicy=self.msgs.DeadLetterPolicy(
            deadLetterTopic='topic2', maxDeliveryAttempts=5),
        retryPolicy=self.msgs.RetryPolicy(
            minimumBackoff='20s', maximumBackoff='500s'),
        labels=labels)
    self.subscriptions_service.Create.Expect(subscription, subscription)
    result = self.subscriptions_client.Create(
        sub_ref,
        topic_ref,
        20,
        labels=labels,
        enable_message_ordering=True,
        dead_letter_topic='topic2',
        max_delivery_attempts=5,
        min_retry_delay='20s',
        max_retry_delay='500s')
    self.assertEqual(result, subscription)

  def testDelete(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())

    self.subscriptions_service.Delete.Expect(
        self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=sub_ref.RelativeName()),
        self.msgs.Empty())
    self.subscriptions_client.Delete(sub_ref)

  def testList(self):
    project_ref = util.ParseProject(self.Project())
    subs = [self.msgs.Subscription(name=str(i))
            for i in range(200)]
    slices, token_pairs = list_slicer.SliceList(subs, 100)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.subscriptions_service.List.Expect(
          self.msgs.PubsubProjectsSubscriptionsListRequest(
              project=project_ref.RelativeName(),
              pageSize=100,
              pageToken=current_token),
          self.msgs.ListSubscriptionsResponse(
              subscriptions=subs[slice_],
              nextPageToken=next_token))

    result = self.subscriptions_client.List(project_ref)
    self.assertEqual(list(result), subs)

  def testModifyAckDeadline(self):
    ack_ids = [str(i) for i in range(3)]
    sub_ref = util.ParseSubscription('sub1', self.Project())

    self.subscriptions_service.ModifyAckDeadline.Expect(
        self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=20,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        self.msgs.Empty())
    self.subscriptions_client.ModifyAckDeadline(sub_ref, ack_ids, 20)

  def testModifyPushConfig(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    args = MockArgs()
    args.push_endpoint = 'endpoint'
    push_config = util.ParsePushConfig(args)
    self.subscriptions_service.ModifyPushConfig.Expect(
        self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=push_config),
            subscription=sub_ref.RelativeName()),
        self.msgs.Empty())
    self.subscriptions_client.ModifyPushConfig(sub_ref, push_config)

  def testPull(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    received_messages = [self.msgs.ReceivedMessage(ackId=str(i), message=msg)
                         for i, msg in enumerate(self.messages)]
    self.subscriptions_service.Pull.Expect(
        self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=2, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        self.msgs.PullResponse(receivedMessages=received_messages))
    result = self.subscriptions_client.Pull(sub_ref, 2)
    self.assertEqual(result.receivedMessages, received_messages)

  def _ExpectSeek(self, sub_ref, time=None, snapshot_ref=None):
    snapshot = snapshot_ref.RelativeName() if snapshot_ref else None
    self.subscriptions_service.Seek.Expect(
        self.msgs.PubsubProjectsSubscriptionsSeekRequest(
            seekRequest=self.msgs.SeekRequest(
                snapshot=snapshot, time=time),
            subscription=sub_ref.RelativeName()),
        self.msgs.SeekResponse())

  def testSeek_time(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    time = '2017-10-18T18:25:00.05Z'
    self._ExpectSeek(sub_ref, time=time)
    self.subscriptions_client.Seek(sub_ref, time=time)

  def testSeek_snapshot(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    snapshot_ref = util.ParseSnapshot('snap1', self.Project())
    self._ExpectSeek(sub_ref, snapshot_ref=snapshot_ref)
    self.subscriptions_client.Seek(sub_ref, snapshot_ref=snapshot_ref)

  def testPatch_NoOptions(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    with self.AssertRaisesExceptionMatches(
        subscriptions.NoFieldsSpecifiedError, 'at least one field to update'):
      self.subscriptions_client.Patch(sub_ref)

  def testPatch_AllOptions(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    args = MockArgs()
    args.push_endpoint = 'endpoint'
    push_config = util.ParsePushConfig(args)
    labels = self.msgs.Subscription.LabelsValue(additionalProperties=[
        self.msgs.Subscription.LabelsValue.AdditionalProperty(
            key='label1', value='label1')])
    subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=20,
        pushConfig=push_config,
        retainAckedMessages=True,
        labels=labels,
        messageRetentionDuration='30s',
        deadLetterPolicy=self.msgs.DeadLetterPolicy(
            deadLetterTopic='topic3', maxDeliveryAttempts=100))
    self.subscriptions_service.Patch.Expect(
        self.msgs.PubsubProjectsSubscriptionsPatchRequest(
            updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
                subscription=subscription,
                updateMask=('ackDeadlineSeconds,pushConfig,'
                            'retainAckedMessages,messageRetentionDuration,'
                            'labels,'
                            'deadLetterPolicy')),
            name=sub_ref.RelativeName()), subscription)
    result = self.subscriptions_client.Patch(
        sub_ref,
        ack_deadline=20,
        push_config=push_config,
        retain_acked_messages=True,
        message_retention_duration='30s',
        dead_letter_topic='topic3',
        max_delivery_attempts=100,
        labels=labels)
    self.assertEqual(result, subscription)

  def testPatch_MessageRetentionDefault(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=20,
        messageRetentionDuration=None)
    self.subscriptions_service.Patch.Expect(
        self.msgs.PubsubProjectsSubscriptionsPatchRequest(
            updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
                subscription=subscription,
                updateMask=('ackDeadlineSeconds,messageRetentionDuration')),
            name=sub_ref.RelativeName()),
        subscription)
    result = self.subscriptions_client.Patch(
        sub_ref,
        ack_deadline=20,
        message_retention_duration='default')
    self.assertEqual(result, subscription)

  def testPatch_ClearDeadLetterPolicy(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    args = MockArgs()
    args.push_endpoint = 'endpoint'
    subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(), deadLetterPolicy=None)
    self.subscriptions_service.Patch.Expect(
        self.msgs.PubsubProjectsSubscriptionsPatchRequest(
            updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
                subscription=subscription, updateMask=('deadLetterPolicy')),
            name=sub_ref.RelativeName()), subscription)
    result = self.subscriptions_client.Patch(
        sub_ref, clear_dead_letter_policy=True)
    self.assertEqual(result, subscription)

  def testPatch_ClearRetryPolicy(self):
    sub_ref = util.ParseSubscription('sub1', self.Project())
    args = MockArgs()
    args.push_endpoint = 'endpoint'
    subscription = self.msgs.Subscription(
        name=sub_ref.RelativeName(), retryPolicy=None)
    self.subscriptions_service.Patch.Expect(
        self.msgs.PubsubProjectsSubscriptionsPatchRequest(
            updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
                subscription=subscription, updateMask=('retryPolicy')),
            name=sub_ref.RelativeName()), subscription)
    result = self.subscriptions_client.Patch(sub_ref, clear_retry_policy=True)
    self.assertEqual(result, subscription)


if __name__ == '__main__':
  test_case.main()
