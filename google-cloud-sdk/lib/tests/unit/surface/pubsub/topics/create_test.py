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

"""Test of the 'pubsub topics create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class TopicsCreateTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(False)
    self.svc = self.client.projects_topics.Create

  def _CreateTopicResourceAndMessage(self, name):
    topic_ref = util.ParseTopic(name, self.Project())
    topic_msg = self.msgs.Topic(name=topic_ref.RelativeName())
    return (topic_ref, topic_msg)

  def testSingleTopicCreate(self):
    topic_ref, topic_msg = self._CreateTopicResourceAndMessage('topic1')
    self.svc.Expect(request=topic_msg, response=topic_msg)

    result = list(self.Run('pubsub topics create topic1'))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0].name, topic_ref.RelativeName())

  def testSingleTopicCreateFullUri(self):
    topic_ref, topic_msg = self._CreateTopicResourceAndMessage('topic1')
    self.svc.Expect(request=topic_msg, response=topic_msg)

    result = list(self.Run('pubsub topics create {}'
                           .format(topic_ref.SelfLink())))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0].name, topic_ref.RelativeName())

  def testTopicsCreate(self):
    topic_ref1, topic_msg1 = self._CreateTopicResourceAndMessage('topic1')
    topic_ref2, topic_msg2 = self._CreateTopicResourceAndMessage('topic2')
    self.svc.Expect(request=topic_msg1, response=topic_msg1)
    self.svc.Expect(request=topic_msg2, response=topic_msg2)

    result = list(self.Run('pubsub topics create topic1 topic2'))

    self.assertEqual(len(result), 2)
    self.assertEqual(result[0].name, topic_ref1.RelativeName())
    self.assertEqual(result[1].name, topic_ref2.RelativeName())

  def testTopicsCreateWithFailuresAndOutput(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    exception1 = http_error.MakeHttpError(message='ERROR1')
    exception2 = http_error.MakeHttpError(message='ERROR2')
    topic_ref1, topic_msg1 = self._CreateTopicResourceAndMessage('topic1')
    topic_ref2, topic_msg2 = self._CreateTopicResourceAndMessage('topic2')

    self.svc.Expect(request=topic_msg1, response=None, exception=exception1)
    self.svc.Expect(request=topic_msg2, response=None, exception=exception2)

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to create the following: [topic1,topic2].'):
      self.Run('pubsub topics create topic1 topic2')
    self.AssertErrContains('Failed to create topic [{}]: ERROR1.'
                           .format(topic_ref1.RelativeName()))
    self.AssertErrContains('Failed to create topic [{}]: ERROR2.'
                           .format(topic_ref2.RelativeName()))


class TopicsCreateBetaTest(TopicsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSingleTopicCreateLabels(self):
    topic_ref, topic_msg = self._CreateTopicResourceAndMessage('topic1')
    labels = self.msgs.Topic.LabelsValue(
        additionalProperties=[
            self.msgs.Topic.LabelsValue.AdditionalProperty(
                key='label1', value='value1'),
            self.msgs.Topic.LabelsValue.AdditionalProperty(
                key='label2', value='value2')])
    topic_msg.labels = labels
    self.svc.Expect(request=topic_msg, response=topic_msg)

    result = list(self.Run('pubsub topics create topic1 '
                           '--labels label1=value1,label2=value2'))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0].name, topic_ref.RelativeName())

  def testSingleTopicCreateWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    topic_ref, topic_msg = self._CreateTopicResourceAndMessage('topic1')
    self.svc.Expect(request=topic_msg, response=topic_msg)

    result = list(self.Run('pubsub topics create topic1'))

    self.assertEqual(len(result), 1)
    self.assertEqual(result[0]['topicId'], topic_ref.RelativeName())


class TopicsCreateGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.svc = self.client.projects_topics.Create
    self.track = calliope_base.ReleaseTrack.GA

  def _CreateTopicResourceAndMessage(self, name):
    topic_ref = util.ParseTopic(name, self.Project())
    topic_msg = self.msgs.Topic(name=topic_ref.RelativeName())
    return (topic_ref, topic_msg)

  def testSingleTopicCreateNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    _, topic_msg = self._CreateTopicResourceAndMessage('topic1')
    self.svc.Expect(request=topic_msg, response=topic_msg)

    result = list(self.Run('pubsub topics create topic1'))

    self.assertTrue(isinstance(result[0], self.msgs.Topic))

if __name__ == '__main__':
  test_case.main()
