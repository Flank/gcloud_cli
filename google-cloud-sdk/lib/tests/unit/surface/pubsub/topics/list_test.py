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

"""Test of the 'pubsub topics list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsListTest(base.CloudPubsubTestBase,
                     sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_topics.List

    self.project_ref = util.ParseProject(self.Project())
    self.topic_refs = [
        util.ParseTopic('topic{}'.format(i), self.Project) for i in (1, 2, 3)]
    self.topics = [
        self.msgs.Topic(name=topic_ref.RelativeName())
        for topic_ref in self.topic_refs]

  def testTopicsList(self):
    """Test 'list' works as intended and produces well-formatted output."""
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(topics=self.topics))

    self.Run('pubsub topics list')

    self.AssertOutputEquals("""\
---
name: projects/{project}/topics/topic1
---
name: projects/{project}/topics/topic2
---
name: projects/{project}/topics/topic3
""".format(project=self.Project()))

  def testTopicsListUri(self):
    """Test 'list' works as intended and produces well-formatted output."""
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(topics=self.topics))

    self.Run('pubsub topics list --uri')

    expected_output = '\n'.join([
        self.GetTopicUri(topic.name) for topic in self.topics])
    self.AssertOutputContains(expected_output)

  def testTopicsFilteredList(self):
    """Test filtered 'list' works and shows only filtered topics."""
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(topics=self.topics))

    self.Run('pubsub topics list --filter=name:topic1 '
             '--format=csv[no-heading](name)')

    self.AssertOutputEquals('{}\n'.format(self.topic_refs[0].RelativeName()))

  def testTopicsPaginationList(self):
    """Test 'list' requests additional pages when nextPageToken is not empty."""
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(
            topics=[self.topics[0]],
            nextPageToken='1234567890'))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName(),
            pageToken='1234567890'),
        response=self.msgs.ListTopicsResponse(
            topics=self.topics[1:],
            nextPageToken=''))

    self.Run('pubsub topics list')

    self.AssertOutputEquals("""\
---
name: projects/{project}/topics/topic1
---
name: projects/{project}/topics/topic2
---
name: projects/{project}/topics/topic3
""".format(project=self.Project()))

  def testTopicsPaginationListMax(self):
    """Test 'list' truncates correctly when max-results is given."""
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(
            topics=self.topics,
            nextPageToken='1234567890'))

    self.Run('pubsub topics list --limit 2 --format=csv[no-heading](name)')

    # Test that --limit works, we return fewer topics than
    # the available amount of test topics.
    self.AssertOutputEquals('{0}\n{1}\n'.format(
        self.topic_refs[0].RelativeName(), self.topic_refs[1].RelativeName()))


class TopicsListBetaTest(TopicsListTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testTopicsListWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(topics=self.topics))

    self.Run('pubsub topics list')

    self.AssertOutputEquals("""\
---
topic: projects/{0}/topics/topic1
topicId: topic1
---
topic: projects/{0}/topics/topic2
topicId: topic2
---
topic: projects/{0}/topics/topic3
topicId: topic3
""".format(self.Project()))


class TopicsListGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_topics.List
    self.topic_refs = [
        util.ParseTopic('topic{}'.format(i), self.Project) for i in (1, 2, 3)]
    self.topics = [
        self.msgs.Topic(name=topic_ref.RelativeName())
        for topic_ref in self.topic_refs]

  def testTopicsListNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    project_ref = util.ParseProject(self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsListRequest(
            project=project_ref.RelativeName()),
        response=self.msgs.ListTopicsResponse(topics=self.topics))

    self.Run('pubsub topics list')

    self.AssertOutputEquals("""\
---
name: projects/{project}/topics/topic1
---
name: projects/{project}/topics/topic2
---
name: projects/{project}/topics/topic3
""".format(project=self.Project()))


if __name__ == '__main__':
  test_case.main()
