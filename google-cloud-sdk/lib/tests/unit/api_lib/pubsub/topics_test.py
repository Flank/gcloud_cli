# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests for the Cloud Pub/Sub Topics library."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.pubsub import base

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class TopicsTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.topics_client = topics.TopicsClient(self.client, self.msgs)
    self.topics_service = self.client.projects_topics

  def testCreate(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = self.msgs.Topic(name=topic_ref.RelativeName())
    self.topics_service.Create.Expect(topic, topic)
    result = self.topics_client.Create(topic_ref)
    self.assertEqual(result, topic)

  def testCreateLabels(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    labels = self.msgs.Topic.LabelsValue(additionalProperties=[
        self.msgs.Topic.LabelsValue.AdditionalProperty(
            key='label1', value='value1')])
    topic = self.msgs.Topic(name=topic_ref.RelativeName(), labels=labels)
    self.topics_service.Create.Expect(topic, topic)
    result = self.topics_client.Create(topic_ref, labels=labels)
    self.assertEqual(result, topic)

  def testDelete(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    self.topics_service.Delete.Expect(
        self.msgs.PubsubProjectsTopicsDeleteRequest(
            topic=topic_ref.RelativeName()),
        self.msgs.Empty())
    self.topics_client.Delete(topic_ref)

  def testGet(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = self.msgs.Topic(name=topic_ref.RelativeName())
    self.topics_service.Get.Expect(
        self.msgs.PubsubProjectsTopicsGetRequest(
            topic=topic_ref.RelativeName()),
        topic)
    self.assertEqual(self.topics_client.Get(topic_ref), topic)

  def testList(self):
    project_ref = util.ParseProject(self.Project())
    topics_list = [self.msgs.Topic(name=str(i)) for i in range(200)]
    slices, token_pairs = list_slicer.SliceList(topics_list, 100)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.topics_service.List.Expect(
          self.msgs.PubsubProjectsTopicsListRequest(
              project=project_ref.RelativeName(),
              pageSize=100,
              pageToken=current_token),
          self.msgs.ListTopicsResponse(
              topics=topics_list[slice_],
              nextPageToken=next_token))

    result = self.topics_client.List(project_ref)
    self.assertEqual(list(result), topics_list)

  def testListSubscriptions(self):
    list_subs_service = self.client.projects_topics_subscriptions

    topic_ref = util.ParseTopic('topic1', self.Project())
    subs = [str(i) for i in range(200)]
    slices, token_pairs = list_slicer.SliceList(subs, 100)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      list_subs_service.List.Expect(
          self.msgs.PubsubProjectsTopicsSubscriptionsListRequest(
              topic=topic_ref.RelativeName(),
              pageSize=100,
              pageToken=current_token),
          self.msgs.ListTopicSubscriptionsResponse(
              subscriptions=subs[slice_],
              nextPageToken=next_token))

    result = self.topics_client.ListSubscriptions(topic_ref)
    self.assertEqual(list(result), subs)

  def testPublish(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    message_body = b'Pubsub message'
    attributes = [
        self.msgs.PubsubMessage.AttributesValue.AdditionalProperty(
            key='key',
            value='value',)
    ]
    message = self.msgs.PubsubMessage(
        attributes=self.msgs.PubsubMessage.AttributesValue(
            additionalProperties=attributes),
        data=message_body
    )
    self.topics_service.Publish.Expect(
        self.msgs.PubsubProjectsTopicsPublishRequest(
            publishRequest=self.msgs.PublishRequest(
                messages=[message]),
            topic=topic_ref.RelativeName()),
        self.msgs.PublishResponse(messageIds=['123']))
    result = self.topics_client.Publish(topic_ref, message_body, attributes)
    self.assertEqual(result.messageIds[0], '123')

  def testPatch(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    labels = self.msgs.Topic.LabelsValue(additionalProperties=[
        self.msgs.Topic.LabelsValue.AdditionalProperty(
            key='label', value='value')])
    topic = self.msgs.Topic(
        name=topic_ref.RelativeName(),
        labels=labels)
    self.topics_service.Patch.Expect(
        self.msgs.PubsubProjectsTopicsPatchRequest(
            name=topic_ref.RelativeName(),
            updateTopicRequest=self.msgs.UpdateTopicRequest(
                topic=topic,
                updateMask='labels')),
        topic)
    self.assertEqual(self.topics_client.Patch(topic_ref, labels), topic)

  def testPatchNoFieldsSpecified(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    with self.assertRaises(topics.NoFieldsSpecifiedError):
      self.topics_client.Patch(topic_ref)


if __name__ == '__main__':
  test_case.main()

