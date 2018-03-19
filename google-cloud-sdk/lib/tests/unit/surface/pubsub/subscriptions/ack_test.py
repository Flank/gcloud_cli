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

"""Test of the 'pubsub subscriptions ack' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsAckTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Acknowledge

  def testSubscriptionsAcknowledge(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['ACKID1', 'ACKID2']),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run(
        'pubsub subscriptions ack subs1 --ack-ids="ACKID1,ACKID2"')

    self.assertEquals(result, self.msgs.Empty())
    self.AssertErrContains('Acked the messages with the following ackIds: '
                           '[ACKID1,ACKID2]')

  def testSubscriptionsAcknowledgeFullUri(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['ACKID1', 'ACKID2']),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run(
        'pubsub subscriptions ack {} --ack-ids="ACKID1,ACKID2"'
        .format(sub_ref.SelfLink()))

    self.assertEquals(result, self.msgs.Empty())
    self.AssertErrContains('Acked the messages with the following ackIds: '
                           '[ACKID1,ACKID2]')


class SubscriptionsAckGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Acknowledge

  def testSubscriptionsAcknowledgeNoDeprecatedArgs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments: ACKID1'):
      self.Run('pubsub subscriptions ack subs1 ACKID1 '
               '--ack-ids="ACKID1,ACKID2"')

  def testSubscriptionsAcknowledgeNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['ACKID1', 'ACKID2']),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run(
        'pubsub subscriptions ack subs1 --ack-ids="ACKID1,ACKID2"')

    self.assertEquals(result, self.msgs.Empty())
    self.AssertErrContains('Acked the messages with the following ackIds: '
                           '[ACKID1,ACKID2]')


class SubscriptionsAckBetaTest(SubscriptionsAckTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Acknowledge

  def testSubscriptionsAcknowledgeDeprecationMessage(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['ACKID1', 'ACKID2']),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run(
        'pubsub subscriptions ack subs1 ACKID1 ACKID2')

    self.assertEquals(result, self.msgs.Empty())
    self.AssertErrContains('Acked the messages with the following ackIds: '
                           '[ACKID1,ACKID2]')
    self.AssertErrContains('Positional argument `ACK_ID` is deprecated. '
                           'Please use `--ack-ids` instead.')

  def testSubscriptionsAcknowledgeLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    sub_ref = util.ParseSubscription('subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsAcknowledgeRequest(
            acknowledgeRequest=self.msgs.AcknowledgeRequest(
                ackIds=['ACKID1', 'ACKID2']),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run(
        'pubsub subscriptions ack subs1 --ack-ids="ACKID1,ACKID2"')

    self.AssertErrContains('Acked the messages with the following ackIds: '
                           '[ACKID1,ACKID2]')
    self.assertEquals(result['ackIds'], ['ACKID1', 'ACKID2'])
    self.assertEquals(result['subscriptionId'], sub_ref.RelativeName())

  def testSubscriptionsAcknowledgeMutuallyExlusiveArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: ACK_ID, --ack-ids'):
      self.Run('pubsub subscriptions ack subs1 ACKID1 --ack-ids ACKID2')

  def testSubscriptionsAcknowledgeMissingRequiredArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.MinimumArgumentException,
        'One of [ACK_ID, --ack-ids] must be supplied.'):
      self.Run('pubsub subscriptions ack subs1')


if __name__ == '__main__':
  test_case.main()
