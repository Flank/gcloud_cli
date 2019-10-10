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

"""Test of the 'pubsub subscriptions list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.pubsub import base

from six.moves import range  # pylint: disable=redefined-builtin


class SubscriptionsListTestBase(base.CloudPubsubTestBase,
                                sdk_test_base.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.List
    # List of test Cloud Pub/Sub resource objects
    self.project_ref = util.ParseProject(self.Project())
    self.subscription_refs = [
        util.ParseSubscription('subs{}'.format(i+1), self.Project())
        for i in range(3)]
    self.topic_refs = [
        util.ParseTopic('topic1', self.Project()),
        util.ParseTopic('topic2', self.Project())]
    self.subscriptions = [
        self.msgs.Subscription(
            name=self.subscription_refs[0].RelativeName(),
            ackDeadlineSeconds=180,
            messageRetentionDuration='604800s',
            retainAckedMessages=False,
            topic=self.topic_refs[0].RelativeName(),
            pushConfig=self.msgs.PushConfig(pushEndpoint=None)),
        self.msgs.Subscription(
            name=self.subscription_refs[1].RelativeName(),
            ackDeadlineSeconds=10,
            messageRetentionDuration='604800s',
            retainAckedMessages=False,
            topic=self.topic_refs[1].RelativeName(),
            pushConfig=self.msgs.PushConfig(
                pushEndpoint='https://my.appspot.com/push')),
        self.msgs.Subscription(
            name=self.subscription_refs[2].RelativeName(),
            ackDeadlineSeconds=10,
            messageRetentionDuration='604800s',
            retainAckedMessages=False,
            topic=self.topic_refs[1].RelativeName(),
            pushConfig=self.msgs.PushConfig(
                pushEndpoint='https://my.appspot.com/push'))]


class SubscriptionsListGATest(SubscriptionsListTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSubscriptionsListNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list --format=flattened[no-ad]')
    self.AssertOutputEquals("""\
---
ackDeadlineSeconds: 180
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs1
pushConfig: {{}}
retainAckedMessages: False
topic: projects/{project}/topics/topic1
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs2
pushConfig.pushEndpoint: https://my.appspot.com/push
retainAckedMessages: False
topic: projects/{project}/topics/topic2
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs3
pushConfig.pushEndpoint: https://my.appspot.com/push
retainAckedMessages: False
topic: projects/{project}/topics/topic2
""".format(project=self.Project()), normalize_space=True)


class SubscriptionsListTest(SubscriptionsListTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSubscriptionsList(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list --format=flattened[no-ad]')
    self.AssertOutputEquals("""\
---
ackDeadlineSeconds: 180
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs1
pushConfig: {{}}
retainAckedMessages: False
topic: projects/{project}/topics/topic1
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs2
pushConfig.pushEndpoint: https://my.appspot.com/push
retainAckedMessages: False
topic: projects/{project}/topics/topic2
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs3
pushConfig.pushEndpoint: https://my.appspot.com/push
retainAckedMessages: False
topic: projects/{project}/topics/topic2
""".format(project=self.Project()), normalize_space=True)

  def testSubscriptionsListUri(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list --uri')

    expected_output = '\n'.join([
        self.GetSubscriptionUri(sub.name) for sub in self.subscriptions])
    self.AssertOutputContains(expected_output, normalize_space=True)

  def testSubscriptionsListWithFilter(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list --format=csv[no-heading](name,'
             'ackDeadlineSeconds)'
             ' --filter=name:subs2')

    self.AssertOutputEquals("""\
projects/{project}/subscriptions/subs2,10
""".format(project=self.Project()))

  def testSubscriptionsListLimit(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions,
            nextPageToken='thereisanotherpage'))

    self.Run('pubsub subscriptions list --format=csv[no-heading]'
             '(name,ackDeadlineSeconds)'
             ' --limit=2')

    self.AssertOutputEquals("""\
projects/{project}/subscriptions/subs1,180
projects/{project}/subscriptions/subs2,10
""".format(project=self.Project()))

  def testSubscriptionsListPage(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions[0:2],
            nextPageToken='thereisanotherpage'))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2,
            pageToken='thereisanotherpage'),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions[2:3]))

    self.Run('pubsub subscriptions list --format=csv[no-heading]'
             '(name,ackDeadlineSeconds)'
             ' --page-size=2')

    self.AssertOutputEquals("""\
projects/{project}/subscriptions/subs1,180
projects/{project}/subscriptions/subs2,10
projects/{project}/subscriptions/subs3,10
""".format(project=self.Project()))


class SubscriptionsListBetaTest(SubscriptionsListTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSubscriptionsListUriWithlegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list --uri')

    expected_output = '\n'.join([
        self.GetSubscriptionUri(sub.name) for sub in self.subscriptions])
    self.AssertOutputContains(expected_output, normalize_space=True)

  def testSubscriptionsListLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSubscriptionsResponse(
            subscriptions=self.subscriptions))

    self.Run('pubsub subscriptions list')

    self.AssertOutputContains("""\
---
ackDeadlineSeconds: 180
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs1
projectId: {project}
pushConfig: {{}}
retainAckedMessages: false
subscriptionId: subs1
topic: projects/{project}/topics/topic1
topicId: topic1
type: PULL
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs2
projectId: {project}
pushConfig:
pushEndpoint: https://my.appspot.com/push
retainAckedMessages: false
subscriptionId: subs2
topic: projects/{project}/topics/topic2
topicId: topic2
type: PUSH
---
ackDeadlineSeconds: 10
messageRetentionDuration: 604800s
name: projects/{project}/subscriptions/subs3
projectId: {project}
pushConfig:
pushEndpoint: https://my.appspot.com/push
retainAckedMessages: false
subscriptionId: subs3
topic: projects/{project}/topics/topic2
topicId: topic2
type: PUSH
""".format(project=self.Project()), normalize_space=True)


if __name__ == '__main__':
  sdk_test_base.main()
