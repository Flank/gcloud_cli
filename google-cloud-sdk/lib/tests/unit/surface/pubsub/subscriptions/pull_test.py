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

"""Test of the 'pubsub subscriptions pull' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsPullGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

  def _GetMessageOutput(self, data, msg_id, ack_id, delivery_attempt=''):
    return '%s | %d | | %s | %s' % (data, msg_id, delivery_attempt, ack_id)

  def testSubscriptionsPull(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())

    exp_received_messages = []
    for idx, message in enumerate(self.messages):
      message.messageId = self.message_ids[idx]
      exp_received_messages.append(self.msgs.ReceivedMessage(
          ackId=str(idx),
          message=message))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=exp_received_messages))

    self.Run('pubsub subscriptions pull subs1 --limit 20')

    self.AssertOutputContains(
        self._GetMessageOutput('Hello, World!', 123456, '0'),
        normalize_space=True)
    self.AssertOutputContains(
        self._GetMessageOutput('World on Fire!', 654321, '1'),
        normalize_space=True)

  def testSubscriptionsPullFullUri(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())

    exp_received_messages = []
    for idx, message in enumerate(self.messages):
      message.messageId = self.message_ids[idx]
      exp_received_messages.append(self.msgs.ReceivedMessage(
          ackId=str(idx),
          message=message))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=exp_received_messages))

    self.Run('pubsub subscriptions pull {} --limit 20'
             .format(sub_ref.SelfLink()))

    self.AssertOutputContains(
        self._GetMessageOutput('Hello, World!', 123456, '0'),
        normalize_space=True)
    self.AssertOutputContains(
        self._GetMessageOutput('World on Fire!', 654321, '1'),
        normalize_space=True)

  def testSubscriptionsPullMessagesWithAttributes(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_attributes = [
        self.msgs.PubsubMessage.AttributesValue.AdditionalProperty(
            key='attr0', value='0'),
        self.msgs.PubsubMessage.AttributesValue.AdditionalProperty(
            key='attr1', value='1')]

    exp_received_messages = []
    for idx, message in enumerate(self.messages):
      message.messageId = self.message_ids[idx]
      message.attributes = self.msgs.PubsubMessage.AttributesValue(
          additionalProperties=exp_attributes)
      exp_received_messages.append(self.msgs.ReceivedMessage(
          ackId=str(idx),
          message=message))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=exp_received_messages))

    self.Run('pubsub subscriptions pull subs1 --limit 20')

    self.AssertOutputEquals(
        """\
+----------------+------------+------------+------------------+--------+
| DATA           | MESSAGE_ID | ATTRIBUTES | DELIVERY_ATTEMPT | ACK_ID |
+----------------+------------+------------+------------------+--------+
| Hello, World!  | 123456     | attr0=0    |                  | 0      |
|                |            | attr1=1    |                  |        |
| World on Fire! | 654321     | attr0=0    |                  | 1      |
|                |            | attr1=1    |                  |        |
| Hello ?        | 987654     | attr0=0    |                  | 2      |
|                |            | attr1=1    |                  |        |
+----------------+------------+------------+------------------+--------+
        """,
        normalize_space=True)

  def testSubscriptionsPullNoMessagesWithAutoAck(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=[]))

    self.Run('pubsub subscriptions pull subs1 --auto-ack --limit 20')

    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testSubscriptionsPullWithAutoAck(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.messages[0])
    exp_received_message.message.messageId = '123456'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.ack_svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['000']),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions pull subs1 --auto-ack')

    self.AssertOutputContains(
        self._GetMessageOutput('Hello, World!', 123456, ''),
        normalize_space=True)

  def testSubscriptionsPullOutput(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.messages[0])
    exp_received_message.message.messageId = '654321'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        'Hello, World! | 654321 | | | 000', normalize_space=True)

  def testSubscriptionsPullUrlSafeEncodedMessage(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())

    # '3c?' gets encoded to 'M2M_' (URL-safe base64). This will fail to be
    # decoded if the standard base64 implementation is used.
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.msgs.PubsubMessage(
            data=b'3c?'))
    exp_received_message.message.messageId = '654321'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        self._GetMessageOutput('3c?', 654321, '000'), normalize_space=True)

  def testSubscriptionsPullWithDeliveryAttempt(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    received_message = self.messages[0]
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=received_message, deliveryAttempt=2)
    exp_received_message.message.messageId = '1234567'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        self._GetMessageOutput(
            'Hello, World!', 1234567, '0', delivery_attempt=2),
        normalize_space=True)

  def testSubscriptionsPullNoDeprecatedArgs(self):
    err = """\
 --max-messages flag is available in one or more alternate release tracks. Try:

  gcloud alpha pubsub subscriptions pull --max-messages
  gcloud beta pubsub subscriptions pull --max-messages
"""
    with self.AssertRaisesExceptionRegexp(
        cli_test_base.MockArgumentError,
        err):
      self.Run('pubsub subscriptions pull subs1 --max-messages')


class SubscriptionsPullBetaTest(SubscriptionsPullGATest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

  def _GetMessageOutput(self,
                        data,
                        msg_id,
                        ack_id,
                        ordering_key='',
                        delivery_attempt=''):
    return '%s | %d | %s | | %s | %s' % (data, msg_id, ordering_key,
                                         delivery_attempt, ack_id)

  def testSubscriptionsPullMaxMessagesDeprecated(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())

    exp_received_messages = []
    for idx, message in enumerate(self.messages):
      message.messageId = self.message_ids[idx]
      exp_received_messages.append(self.msgs.ReceivedMessage(
          ackId=str(idx),
          message=message))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20,
                returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=exp_received_messages))

    self.Run('pubsub subscriptions pull subs1 --max-messages 20')

    self.AssertOutputContains(
        self._GetMessageOutput('Hello, World!', 123456, '0'),
        normalize_space=True)
    self.AssertOutputContains(
        self._GetMessageOutput('World on Fire!', 654321, '1'),
        normalize_space=True)
    self.AssertErrContains('`--max-messages` is deprecated. Please use --limit '
                           'instead.')

  def testSubscriptionsPullMutuallyExclusiveLimitArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --max-messages, --limit'):
      self.Run('pubsub subscriptions pull subs1 --max-messages 5 --limit 20')

  def testSubscriptionsPullWithDeliveryAttempt(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    received_message = self.messages[0]
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=received_message, deliveryAttempt=2)
    exp_received_message.message.messageId = '1234567'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        self._GetMessageOutput(
            'Hello, World!', 1234567, '0', delivery_attempt=2),
        normalize_space=True)

  def testSubscriptionsPullMessagesWithAttributes(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_attributes = [
        self.msgs.PubsubMessage.AttributesValue.AdditionalProperty(
            key='attr0', value='0'),
        self.msgs.PubsubMessage.AttributesValue.AdditionalProperty(
            key='attr1', value='1')
    ]

    exp_received_messages = []
    for idx, message in enumerate(self.messages):
      message.messageId = self.message_ids[idx]
      message.attributes = self.msgs.PubsubMessage.AttributesValue(
          additionalProperties=exp_attributes)
      exp_received_messages.append(
          self.msgs.ReceivedMessage(ackId=str(idx), message=message))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=20, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(receivedMessages=exp_received_messages))

    self.Run('pubsub subscriptions pull subs1 --limit 20')

    self.AssertOutputEquals(
        """\
+----------------+------------+--------------+------------+------------------+--------+
| DATA           | MESSAGE_ID | ORDERING_KEY | ATTRIBUTES | DELIVERY_ATTEMPT | ACK_ID |
+----------------+------------+--------------+------------+------------------+--------+
| Hello, World!  | 123456     |              | attr0=0    |                  | 0      |
|                |            |              | attr1=1    |                  |        |
| World on Fire! | 654321     |              | attr0=0    |                  | 1      |
|                |            |              | attr1=1    |                  |        |
| Hello ?        | 987654     |              | attr0=0    |                  | 2      |
|                |            |              | attr1=1    |                  |        |
+----------------+------------+--------------+------------+------------------+--------+
        """,
        normalize_space=True)

  def testSubscriptionsPullOutput(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.messages[0], deliveryAttempt=0)
    exp_received_message.message.messageId = '654321'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        self._GetMessageOutput(
            'Hello, World!', 654321, '000', delivery_attempt=0),
        normalize_space=True)

  def testSubscriptionsPullWithOrderingKey(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    received_message = self.messages[0]
    received_message.orderingKey = 'in-order'
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=received_message)
    exp_received_message.message.messageId = '1234567'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1, returnImmediately=True),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1')

    self.AssertOutputContains(
        self._GetMessageOutput(
            'Hello, World!', 1234567, '0', ordering_key='in-order'),
        normalize_space=True)

  def testSubscriptionsPullNoDeprecatedArgs(self):
    pass


class SubscriptionsPullAlphaTest(SubscriptionsPullBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

  def testSubscriptionsPullWithWait(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.messages[0], deliveryAttempt=0)
    exp_received_message.message.messageId = '1234567'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1, returnImmediately=False),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1 --wait')

    self.AssertOutputContains(
        self._GetMessageOutput(
            'Hello, World!', 1234567, '000', delivery_attempt=0),
        normalize_space=True)

  def testSubscriptionsPullNoDeprecatedArgs(self):
    pass


if __name__ == '__main__':
  test_case.main()
