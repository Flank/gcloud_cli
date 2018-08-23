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

"""Test of the 'pubsub topics publish' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsPublishTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_topics.Publish

  def testSimpleTopicsPublish(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish topic1 --message "{0}"'.format(
        self.message_data[0]))

    self.assertEqual(result.messageIds, ['123456'])

  def testSimpleTopicsPublishFullUri(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish {0} --message "{1}"'.format(
        topic_ref.SelfLink(), self.message_data[0]))

    self.assertEqual(result.messageIds, ['123456'])

  def testTopicsPublishMessageWithAttributes(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    attr_msg = self.msgs.PubsubMessage.AttributesValue.AdditionalProperty
    message = self.messages[0]
    message.attributes = self.msgs.PubsubMessage.AttributesValue(
        additionalProperties=[attr_msg(key='attr0', value='0'),
                              attr_msg(key='attr1', value='1')])

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(messages=[message]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run(('pubsub topics publish topic1 --message "{0}"'
                       ' --attribute attr0=0,attr1=1').format(
                           self.message_data[0]))

    self.assertEqual(result.messageIds, ['123456'])

  def testTopicsPublishMessageWithOnlyAttributes(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    attr_msg = self.msgs.PubsubMessage.AttributesValue.AdditionalProperty
    message = self.messages[0]
    message.data = None
    message.attributes = self.msgs.PubsubMessage.AttributesValue(
        additionalProperties=[attr_msg(key='attr0', value='0')])

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(messages=[message]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish topic1 --attribute attr0=0')
    self.assertEqual(result.messageIds, ['123456'])

  def testTopicsPublishEmptyMessageShouldFail(self):
    with self.assertRaisesRegex(
        topics.EmptyMessageException,
        'You cannot send an empty message. You must specify either a '
        'MESSAGE, one or more ATTRIBUTE, or both.'):
      self.Run('pubsub topics publish topic1')

  def testTopicsPublishMessageWithMalformedAttributes(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'^argument --attribute: Bad syntax for dict arg: \[a_b\]\. Please see '
        r'`gcloud topic escaping` if you would like information on escaping '
        r'list or dictionary flag values\.$'):
      self.Run('pubsub topics publish topic1 --attribute a_b')

  def testTopicsPublishMessageWithOutput(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    self.Run('pubsub topics publish --format=csv[no-heading](messageIds) topic1'
             ' --message "{0}"'.format(self.message_data[0]))
    self.AssertOutputContains('123456')

  def testMalformedResponseFails(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=[]))

    with self.assertRaises(topics.PublishOperationException):
      self.Run('pubsub topics publish topic1'
               ' --message "{0}"'.format(
                   self.message_data[0]))


class TopicsPublishBetaTest(TopicsPublishTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testTopicsPublishDeprecationMessage(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish topic1 "{0}"'.format(
        self.message_data[0]))

    self.assertEqual(result.messageIds, ['123456'])
    self.AssertErrContains('Positional argument `MESSAGE_BODY` is deprecated. '
                           'Please use `--message` instead.')

  def testTopicsPublishWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish topic1 --message "{0}" '
                      .format(self.message_data[0]))

    self.assertEqual(result['messageIds'], '123456')

  def testSubscriptionsAcknowledgeMutuallyExlusiveArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: MESSAGE_BODY, --message'):
      self.Run('pubsub topics publish topic1 msg1 --message msg2')


class TopicsPublishGATest(base.CloudPubsubTestBase, parameterized.TestCase):

  def SetUp(self):
    self.svc = self.client.projects_topics.Publish
    self.track = calliope_base.ReleaseTrack.GA

  def testSimpleTopicsPublish(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = topic_ref.RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=self.messages[0:1]),
            topic=topic),
        response=self.msgs.PublishResponse(messageIds=self.message_ids[0:1]))

    result = self.Run('pubsub topics publish topic1 --message "{0}"'.format(
        self.message_data[0]))

    self.assertEqual(result.messageIds, ['123456'])

  def testSubscriptionsAcknowledgeNoDeprecatedArgs(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments: a message'):
      self.Run('pubsub topics publish topic1 "a message" ')

if __name__ == '__main__':
  test_case.main()
