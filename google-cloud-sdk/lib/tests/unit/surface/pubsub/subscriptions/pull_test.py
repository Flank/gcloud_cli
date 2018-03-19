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

"""Test of the 'pubsub subscriptions pull' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsPullTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

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

    self.AssertOutputContains('Hello, World! | 123456 | | 0',
                              normalize_space=True)
    self.AssertOutputContains('| World on Fire! | 654321 | | 1 |',
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

    self.AssertOutputContains('Hello, World! | 123456 | | 0',
                              normalize_space=True)
    self.AssertOutputContains('| World on Fire! | 654321 | | 1 |',
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

    self.AssertOutputEquals("""\
+----------------+------------+------------+--------+
| DATA           | MESSAGE_ID | ATTRIBUTES | ACK_ID |
+----------------+------------+------------+--------+
| Hello, World!  | 123456     | attr0=0    | 0      |
|                |            | attr1=1    |        |
| World on Fire! | 654321     | attr0=0    | 1      |
|                |            | attr1=1    |        |
+----------------+------------+------------+--------+
        """, normalize_space=True)

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

    self.AssertOutputContains('| Hello, World! | 123456 | |',
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

    self.AssertOutputContains('Hello, World! | 654321 | | 000',
                              normalize_space=True)

  def testSubscriptionsPullUrlSafeEncodedMessage(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())

    # '3c?' gets encoded to 'M2M_' (URL-safe base64). This will fail to be
    # decoded if the standard base64 implementation is used.
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.msgs.PubsubMessage(
            data='3c?'))
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

    self.AssertOutputContains('3c? | 654321 | | 000',
                              normalize_space=True)


class SubscriptionsPullAlphaTest(SubscriptionsPullTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

  def testSubscriptionsPullWithWait(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    exp_received_message = self.msgs.ReceivedMessage(
        ackId='000', message=self.messages[0])
    exp_received_message.message.messageId = '1234567'

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsPullRequest(
            pullRequest=self.msgs.PullRequest(
                maxMessages=1,
                returnImmediately=False),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.PullResponse(
            receivedMessages=[exp_received_message]))

    self.Run('pubsub subscriptions pull subs1 --wait')

    self.AssertOutputContains('| Hello, World! | 1234567 | |',
                              normalize_space=True)


class SubscriptionsPullBetaTest(SubscriptionsPullAlphaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Pull
    self.ack_svc = self.client.projects_subscriptions.Acknowledge

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

    self.AssertOutputContains('Hello, World! | 123456 | | 0',
                              normalize_space=True)
    self.AssertOutputContains('| World on Fire! | 654321 | | 1 |',
                              normalize_space=True)
    self.AssertErrContains('`--max-messages` is deprecated. Please use --limit '
                           'instead.')

  def testSubscriptionsPullMutuallyExclusiveLimitArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --max-messages, --limit'):
      self.Run('pubsub subscriptions pull subs1 --max-messages 5 --limit 20')


class SubscriptionsPullGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSubscriptionsPullNoDeprecatedArgs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments: --max-messages'):
      self.Run('pubsub subscriptions pull subs1 --max-messages')


if __name__ == '__main__':
  test_case.main()
