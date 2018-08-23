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

"""Test of the 'pubsub subscriptions {}' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsModifyMessageAckDeadlineTest(base.CloudPubsubTestBase,
                                                parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.ModifyAckDeadline

  def testSubscriptionsModify(self):
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-message-ack-deadline subs2 '
             '--ack-ids 123456 --ack-deadline 600')

    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))

  def testSubscriptionsModifyFullUri(self):
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-message-ack-deadline {} '
             '--ack-ids  123456 --ack-deadline 600'.format(sub_ref.SelfLink()))

    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))

  def testSubscriptionsModifyNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run('pubsub subscriptions modify-message-ack-deadline subs2 '
                      '--ack-ids 123456 --ack-deadline 600')

    self.assertEqual(result, self.msgs.Empty())

  def testSubscriptionsModifyAckDeadlineNoDeprecatedArgs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments: ACKID1'):
      self.Run('pubsub subscriptions modify-message-ack-deadline subs1 ACKID1 '
               '--ack-ids  123456 --ack-deadline 600')

  def testSubscriptionsModifyAckDeadlineNoAckIds(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --ack-ids: Must be specified.'):
      self.Run('pubsub subscriptions modify-message-ack-deadline subs1 '
               '--ack-deadline 600')


@parameterized.parameters(
    ('modify-ack-deadline', 'This command has been renamed. Please use '
                            '`modify-message-ack-deadline` instead.'),
    ('modify-message-ack-deadline', None)
)
class SubscriptionsModifyMessageAckDeadlineBetaTest(base.CloudPubsubTestBase,
                                                    parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.ModifyAckDeadline

  def testSubscriptionsModify(self, command, err_msg):
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions {} subs2 --ack-ids 123456'
             ' --ack-deadline 600'.format(command))

    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))
    if err_msg:
      self.AssertErrContains(err_msg)

  def testSubscriptionsModifyFullUri(self, command, err_msg):
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions {0} {1} --ack-ids 123456'
             ' --ack-deadline 600'.format(command, sub_ref.SelfLink()))

    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))
    if err_msg:
      self.AssertErrContains(err_msg)

  def testSubscriptionsModifyWithLegacyOutput(self, command, err_msg):
    properties.VALUES.pubsub.legacy_output.Set(True)
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456', '654321']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions {} subs2 '
             '--ack-ids=123456,654321 --ack-deadline 600'.format(command))

    self.AssertOutputEquals(
        'ackDeadlineSeconds: 600\n'
        'ackId:\n'
        '- \'123456\'\n'
        '- \'654321\'\n'
        'subscriptionId: {}\n'.format(sub_ref.RelativeName()))
    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))
    if err_msg:
      self.AssertErrContains(err_msg)

  def testSubscriptionsModifyDeprecationMessage(self, command, err_msg):
    sub_ref = util.ParseSubscription('subs2', self.Project())
    ack_ids = ['123456', '654321']
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyAckDeadlineRequest(
            modifyAckDeadlineRequest=self.msgs.ModifyAckDeadlineRequest(
                ackDeadlineSeconds=600,
                ackIds=ack_ids),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions {} subs2 123456 654321 '
             '--ack-deadline 600'.format(command))

    self.AssertErrContains('Positional argument `ACK_ID` is deprecated. '
                           'Please use `--ack-ids` instead.')
    self.AssertErrContains(
        'Set ackDeadlineSeconds to [600] for messages with ackId [{0}]] for '
        'subscription [{1}]'.format(','.join(ack_ids), sub_ref.RelativeName()))
    if err_msg:
      self.AssertErrContains(err_msg)

  def testSubscriptionsAcknowledgeMutuallyExlusiveArgs(self, command, err_msg):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: ACK_ID, --ack-ids'):
      self.Run('pubsub subscriptions {} subs1 ACKID1 '
               '--ack-ids ACKID2 --ack-deadline 600'.format(command))
    if err_msg:
      self.AssertErrContains(err_msg)

  def testSubscriptionsAcknowledgeMissingRequiredArgs(self, command, err_msg):
    with self.AssertRaisesExceptionMatches(
        exceptions.MinimumArgumentException,
        'One of [ACK_ID, --ack-ids] must be supplied.'):
      self.Run('pubsub subscriptions {} subs1 '
               '--ack-deadline 600'.format(command))
    if err_msg:
      self.AssertErrContains(err_msg)


if __name__ == '__main__':
  test_case.main()
