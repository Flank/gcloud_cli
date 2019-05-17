# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Test of the 'source repos topics add' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.source import util
from tests.lib import test_case
from tests.lib.surface.source import base


class TopicsAddTestGA(base.SourceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.repo_name = 'projects/{}/repos/my-repo'.format(self.Project())
    self.repo_ref = self._GetRepoRef()

  def _InitialRepo(self, topic_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config)
            ]))

  def _UpdatedRepo(self, topic_name, new_topic_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    new_pubsub_config = self._CreatePubsubConfig(new_topic_name, 'protobuf',
                                                 'b@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config),
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=new_topic_name, value=new_pubsub_config)
            ]))

  def testAdd(self):
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/{}/topics/foo2'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name_1)
    updated_repo = self._UpdatedRepo(topic_name_1, topic_name_2)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(updated_repo)

    self.Run('source repos update my-repo --add-topic foo2 '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testAdd_TopicProject(self):
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_repo = self._InitialRepo(topic_name_1)
    updated_repo = self._UpdatedRepo(topic_name_1, topic_name_2)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(updated_repo)

    self.Run('source repos update my-repo '
             '--add-topic foo2 --topic-project=another-project '
             '--message-format=protobuf --service-account=b@gmail.com')


class TopicsAddTestBeta(TopicsAddTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class TopicsAddTestAlpha(TopicsAddTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class TopicsRemoveTestGA(base.SourceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.repo_ref = self._GetRepoRef()
    self.repo_name = self.repo_ref.RelativeName()

  def _InitialRepo(self, topic_name, another_topic_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    new_pubsub_config = self._CreatePubsubConfig(another_topic_name, 'protobuf',
                                                 'b@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config),
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=another_topic_name, value=new_pubsub_config)
            ]))

  def _RemovedRepo(self, topic_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config)
            ]))

  def testRemove(self):
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/{}/topics/foo2'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name_1, topic_name_2)
    removed_repo = self._RemovedRepo(topic_name_1)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(removed_repo)

    self.Run('source repos update my-repo --remove-topic=foo2')

  def testRemove_TopicProject(self):
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_repo = self._InitialRepo(topic_name_1, topic_name_2)
    removed_repo = self._RemovedRepo(topic_name_1)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(removed_repo)

    self.Run('source repos update my-repo '
             '--remove-topic=foo2 --topic-project=another-project')

  def testRemove_InvalidTopic(self):
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_repo = self._InitialRepo(topic_name_1, topic_name_2)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo3]: You must specify a '
        'topic that is already configured in the repo.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source repos update my-repo --remove-topic=foo3')

  def testRemove_Empty(self):
    initial_repo = self.messages.Repo(name=self.repo_name)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo]: No topics are '
        'configured in the repo.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source repos update my-repo --remove-topic=foo')


class TopicsRemoveTestBeta(TopicsRemoveTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class TopicsRemoveTestAlpha(TopicsRemoveTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class TopicsUpdateTestGA(base.SourceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.repo_ref = self._GetRepoRef()
    self.repo_name = self.repo_ref.RelativeName()

  def _InitialRepo(self, topic_name, message_format='json'):
    pubsub_config = self._CreatePubsubConfig(topic_name, message_format,
                                             'a@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config)
            ]))

  def _UpdatedRepo(self, topic_name, message_format='json'):
    pubsub_config = self._CreatePubsubConfig(topic_name, message_format,
                                             'b@gmail.com')
    return self.messages.Repo(
        name=self.repo_name,
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=pubsub_config)
            ]))

  def testUpdate(self):
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name)
    updated_repo = self._UpdatedRepo(topic_name, 'protobuf')
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(updated_repo)

    self.Run('source repos update my-repo --update-topic=foo '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testUpdate_TopicProject(self):
    topic_name = 'projects/another-project/topics/foo'
    initial_repo = self._InitialRepo(topic_name)
    updated_repo = self._UpdatedRepo(topic_name, 'protobuf')
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(updated_repo)

    self.Run('source repos update my-repo --update-topic=foo '
             '--topic-project=another-project '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testUpdate_InvalidTopic(self):
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo3]: You must specify '
        'a topic that is already configured in the repo.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source repos update my-repo --update-topic=foo3')

  def testUpdate_Empty(self):
    initial_repo = self.messages.Repo(name=self.repo_name)
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo]: No topics are '
        'configured in the repo.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source repos update my-repo --update-topic=foo')

  def testUpdate_WithUnchangedMessageFormat(self):
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name, 'protobuf')
    updated_repo = self._UpdatedRepo(topic_name, 'protobuf')
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(updated_repo)

    self.Run('source repos update my-repo --update-topic=foo '
             '--service-account=b@gmail.com')

  def testUpdate_WithUnchangedData(self):
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_repo = self._InitialRepo(topic_name, 'protobuf')
    self._ExpectGetRepo(self.repo_ref, initial_repo)
    self._ExpectPatchRepo(initial_repo)

    self.Run('source repos update my-repo --update-topic=foo ')


class TopicsUpdateTestBeta(TopicsUpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class TopicsUpdateTestAlpha(TopicsUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
