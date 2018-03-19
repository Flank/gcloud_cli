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
"""Test of the 'pubsub topics delete' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class TopicsDeleteTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_topics.Delete
    properties.VALUES.core.user_output_enabled.Set(True)

  def testSingleTopicDelete(self):
    topic_to_delete = util.ParseTopic('topic1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_delete.RelativeName()),
        response='')

    self.Run('pubsub topics delete topic1')

    self.AssertErrContains(
        'Deleted topic [{}]'.format(topic_to_delete.RelativeName()))

  def testSingleTopicDeleteFullUri(self):
    topic_to_delete = util.ParseTopic('topic1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_delete.RelativeName()),
        response='')

    self.Run('pubsub topics delete {}'.format(topic_to_delete.SelfLink()))
    self.AssertErrContains(
        'Deleted topic [{}]'.format(topic_to_delete.RelativeName()))

  def testTopicsDeleteNonExistent(self):
    topic_to_delete = util.ParseTopic('not_there', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_delete.RelativeName()),
        response='',
        exception=http_error.MakeHttpError(message='Topic does not exist.'))

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to delete the following: [not_there].'):
      self.Run('pubsub topics delete not_there')

  def testMultipleTopicsDeletionWithOutput(self):
    topic_to_succeed = util.ParseTopic('topic1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_succeed.RelativeName()),
        response='')

    topic_to_fail = util.ParseTopic('not_there', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_fail.RelativeName()),
        response='',
        exception=http_error.MakeHttpError(message='Topic does not exist.'))

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to delete the following: [not_there].'):
      self.Run('pubsub topics delete topic1 not_there'
               ' --format=csv[no-heading](name)')

    self.AssertErrContains(
        'Deleted topic [{}].'.format(topic_to_succeed.RelativeName()))
    self.AssertErrContains(
        'Failed to delete topic [{}]: Topic does not exist.'
        .format(topic_to_fail.RelativeName()))
    self.AssertErrContains(
        'Failed to delete the following: [{}].'.format(topic_to_fail.Name()))


class TopicsDeleteBetaTest(TopicsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSingleTopicDeleteWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)
    topic_to_delete = util.ParseTopic('topic1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_delete.RelativeName()),
        response='')

    result = list(self.Run('pubsub topics delete topic1'))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0]['topicId'], topic_to_delete.RelativeName())


class TopicsDeleteGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.svc = self.client.projects_topics.Delete
    self.track = calliope_base.ReleaseTrack.GA

  def testTopicsDeleteNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)
    topic_to_delete = util.ParseTopic('topic1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_to_delete.RelativeName()),
        response=self.msgs.Empty())

    result = list(self.Run('pubsub topics delete topic1'))

    self.assertEqual(result[0], self.msgs.Empty())


if __name__ == '__main__':
  test_case.main()
