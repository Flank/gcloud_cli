# -*- coding: utf-8 -*- #
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

"""Test of the 'pubsub topics describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsDescribeTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_topics.Get

  def testTopicsAcknowledge(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = self.msgs.Topic(name=topic_ref.RelativeName())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsGetRequest(
            topic=topic_ref.RelativeName()),
        response=topic)

    result = self.Run('pubsub topics describe topic1')

    self.assertEqual(result, topic)

  def testTopicsDescribeFullUri(self):
    topic_ref = util.ParseTopic('topic1', self.Project())
    topic = self.msgs.Topic(name=topic_ref.RelativeName())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsGetRequest(
            topic=topic_ref.RelativeName()),
        response=topic)

    result = self.Run(
        'pubsub topics describe {}'.format(topic_ref.SelfLink()))

    self.assertEqual(result, topic)


if __name__ == '__main__':
  test_case.main()
