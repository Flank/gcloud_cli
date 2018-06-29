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
"""Test of the 'source project-configs update' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.source import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.source import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class ProjectConfigUpdatePushblockTest(base.SourceTestBase):

  def _ExpectUpdateProjectConfigWithPushblockConfigured(self,
                                                        enable_pushblock,
                                                        project_name=None):
    project_config = self.messages.ProjectConfig(
        name=self._GetProjectRef(project_name).RelativeName(),
        enablePrivateKeyCheck=enable_pushblock)

    self._ExpectUpdateProjectConfig(project_config, 'enablePrivateKeyCheck')

  def testUpdate_EnablePushblock(self, track):
    self.track = track
    self._ExpectUpdateProjectConfigWithPushblockConfigured(
        enable_pushblock=True)
    self.Run('source project-configs update --enable-pushblock')

  def testUpdate_EnablePushblockWithAnotherProject(self, track):
    self.track = track
    self._ExpectUpdateProjectConfigWithPushblockConfigured(
        enable_pushblock=True, project_name='another-project')
    self.Run('source project-configs update --project=another-project '
             '--enable-pushblock')

  def testUpdate_DisablePushblock(self, track):
    self.track = track
    self._ExpectUpdateProjectConfigWithPushblockConfigured(
        enable_pushblock=False)
    self.Run('source project-configs update --disable-pushblock')


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class ProjectConfigUpdateAddTopicTest(base.SourceTestBase):

  def _InitialProjectConfig(self, topic_name, project_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.PubsubConfigsValue(
            additionalProperties=[
                self.messages.ProjectConfig.PubsubConfigsValue.
                AdditionalProperty(key=topic_name, value=pubsub_config)
            ]))

  def _UpdatedProjectConfig(self, topic_name, new_topic_name, project_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    new_pubsub_config = self._CreatePubsubConfig(new_topic_name, 'protobuf',
                                                 'b@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.
        PubsubConfigsValue(additionalProperties=[
            self.messages.ProjectConfig.PubsubConfigsValue.AdditionalProperty(
                key=topic_name, value=pubsub_config),
            self.messages.ProjectConfig.PubsubConfigsValue.AdditionalProperty(
                key=new_topic_name, value=new_pubsub_config)
        ]))

  def _ExpectUpdateProjectConfigWithAddedTopic(self,
                                               project_config,
                                               update_project_config,
                                               project_name=None):
    project_ref = self._GetProjectRef(project_name)
    self._ExpectGetProjectConfig(project_ref, project_config)
    self._ExpectUpdateProjectConfig(update_project_config, 'pubsubConfigs')

  def testAdd(self, track):
    self.track = track
    project_name = self._GetProjectRef().RelativeName()
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/{}/topics/foo2'.format(self.Project())
    initial_project_config = self._InitialProjectConfig(topic_name_1,
                                                        project_name)
    updated_project_config = self._UpdatedProjectConfig(
        topic_name_1, topic_name_2, project_name)
    self._ExpectUpdateProjectConfigWithAddedTopic(initial_project_config,
                                                  updated_project_config)

    self.Run('source project-configs update --add-topic foo2 '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testAdd_TopicProject(self, track):
    self.track = track
    project_name = self._GetProjectRef().RelativeName()
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_project_config = self._InitialProjectConfig(topic_name_1,
                                                        project_name)
    updated_project_config = self._UpdatedProjectConfig(
        topic_name_1, topic_name_2, project_name)
    self._ExpectUpdateProjectConfigWithAddedTopic(initial_project_config,
                                                  updated_project_config)

    self.Run('source project-configs update --add-topic foo2 '
             '--topic-project=another-project '
             '--message-format=protobuf --service-account=b@gmail.com')


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class ProjectConfigUpdateRemoveTest(base.SourceTestBase):

  def _InitialProjectConfig(self, topic_name, another_topic_name, project_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    new_pubsub_config = self._CreatePubsubConfig(another_topic_name, 'protobuf',
                                                 'b@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.
        PubsubConfigsValue(additionalProperties=[
            self.messages.ProjectConfig.PubsubConfigsValue.AdditionalProperty(
                key=topic_name, value=pubsub_config),
            self.messages.ProjectConfig.PubsubConfigsValue.AdditionalProperty(
                key=another_topic_name, value=new_pubsub_config)
        ]))

  def _RemovedProjectConfig(self, topic_name, project_name):
    pubsub_config = self._CreatePubsubConfig(topic_name, 'json', 'a@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.PubsubConfigsValue(
            additionalProperties=[
                self.messages.ProjectConfig.PubsubConfigsValue.
                AdditionalProperty(key=topic_name, value=pubsub_config)
            ]))

  def _ExpectUpdateProjectConfigWithRemovedTopic(self,
                                                 project_config,
                                                 removed_project_config,
                                                 project_name=None):
    project_ref = self._GetProjectRef(project_name)
    self._ExpectGetProjectConfig(project_ref, project_config)
    self._ExpectUpdateProjectConfig(removed_project_config, 'pubsubConfigs')

  def testRemove(self, track):
    self.track = track
    project_name = self._GetProjectRef().RelativeName()
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/{}/topics/foo2'.format(self.Project())
    initial_project_config = self._InitialProjectConfig(
        topic_name_1, topic_name_2, project_name)
    removed_project_config = self._RemovedProjectConfig(topic_name_1,
                                                        project_name)
    self._ExpectUpdateProjectConfigWithRemovedTopic(initial_project_config,
                                                    removed_project_config)

    self.Run('source project-configs update --remove-topic=foo2')

  def testRemove_TopicProject(self, track):
    self.track = track
    project_name = self._GetProjectRef().RelativeName()
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_project_config = self._InitialProjectConfig(
        topic_name_1, topic_name_2, project_name)
    removed_project_config = self._RemovedProjectConfig(topic_name_1,
                                                        project_name)
    self._ExpectUpdateProjectConfigWithRemovedTopic(initial_project_config,
                                                    removed_project_config)

    self.Run('source project-configs update '
             '--remove-topic=foo2 --topic-project=another-project')

  def testRemove_InvalidTopic(self, track):
    self.track = track
    project_name = self._GetProjectRef().RelativeName()
    topic_name_1 = 'projects/{}/topics/foo'.format(self.Project())
    topic_name_2 = 'projects/another-project/topics/foo2'
    initial_project_config = self._InitialProjectConfig(
        topic_name_1, topic_name_2, project_name)
    self._ExpectGetProjectConfig(self._GetProjectRef(), initial_project_config)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo3]: You must specify a '
        'topic that is already configured in the project.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source project-configs update --remove-topic=foo3')

  def testRemove_Empty(self, track):
    self.track = track
    initial_project_config = self.messages.Repo(
        name=self._GetProjectRef().RelativeName())
    self._ExpectGetProjectConfig(self._GetProjectRef(), initial_project_config)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo]: No topics are '
        'configured in the project.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source project-configs update --remove-topic=foo')


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class ProjectConfigUpdateUpdateTopicTest(base.SourceTestBase):

  def _InitialProjectConfig(self, topic_name, message_format='json'):
    project_name = self._GetProjectRef().RelativeName()
    pubsub_config = self._CreatePubsubConfig(topic_name, message_format,
                                             'a@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.PubsubConfigsValue(
            additionalProperties=[
                self.messages.ProjectConfig.PubsubConfigsValue.
                AdditionalProperty(key=topic_name, value=pubsub_config),
            ]))

  def _UpdatedProjectConfig(self, topic_name, message_format='json'):
    project_name = self._GetProjectRef().RelativeName()
    pubsub_config = self._CreatePubsubConfig(topic_name, message_format,
                                             'b@gmail.com')
    return self.messages.ProjectConfig(
        name=project_name,
        pubsubConfigs=self.messages.ProjectConfig.PubsubConfigsValue(
            additionalProperties=[
                self.messages.ProjectConfig.PubsubConfigsValue.
                AdditionalProperty(key=topic_name, value=pubsub_config)
            ]))

  def _ExpectUpdateProjectConfigWithUpdatedTopic(self, project_config,
                                                 updated_project_config):
    project_ref = self._GetProjectRef()
    self._ExpectGetProjectConfig(project_ref, project_config)
    self._ExpectUpdateProjectConfig(updated_project_config, 'pubsubConfigs')

  def testUpdate(self, track):
    self.track = track
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_project_config = self._InitialProjectConfig(topic_name)
    updated_project_config = self._UpdatedProjectConfig(topic_name, 'protobuf')
    self._ExpectUpdateProjectConfigWithUpdatedTopic(initial_project_config,
                                                    updated_project_config)

    self.Run('source project-configs update '
             '--update-topic=foo '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testUpdate_TopicProject(self, track):
    self.track = track
    topic_name = 'projects/another-project/topics/foo'
    initial_project_config = self._InitialProjectConfig(topic_name)
    updated_project_config = self._UpdatedProjectConfig(topic_name, 'protobuf')
    self._ExpectUpdateProjectConfigWithUpdatedTopic(initial_project_config,
                                                    updated_project_config)

    self.Run('source project-configs update '
             '--update-topic=foo '
             '--topic-project=another-project '
             '--message-format=protobuf --service-account=b@gmail.com')

  def testUpdate_InvalidTopic(self, track):
    self.track = track
    topic_name = 'projects/another-project/topics/foo'
    initial_project_config = self._InitialProjectConfig(topic_name)
    self._ExpectGetProjectConfig(self._GetProjectRef(), initial_project_config)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo3]: You must specify '
        'a topic that is already configured in the project.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source project-configs update --update-topic=foo3')

  def testUpdate_Empty(self, track):
    self.track = track
    initial_project_config = self.messages.ProjectConfig()
    self._ExpectGetProjectConfig(self._GetProjectRef(), initial_project_config)
    error_message = re.escape(
        'Invalid topic [projects/fake-project/topics/foo]: No topics are '
        'configured in the project.')

    with self.assertRaisesRegex(util.InvalidTopicError, error_message):
      self.Run('source project-configs update --update-topic=foo')

  def testUpdate_WithUnchangedMessageFormat(self, track):
    self.track = track
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_project_config = self._InitialProjectConfig(topic_name, 'protobuf')
    updated_project_config = self._UpdatedProjectConfig(topic_name, 'protobuf')
    self._ExpectUpdateProjectConfigWithUpdatedTopic(initial_project_config,
                                                    updated_project_config)

    self.Run('source project-configs update --update-topic=foo '
             '--service-account=b@gmail.com')

  def testUpdate_WithUnchangedData(self, track):
    self.track = track
    topic_name = 'projects/{}/topics/foo'.format(self.Project())
    initial_project_config = self._InitialProjectConfig(topic_name, 'protobuf')
    self._ExpectUpdateProjectConfigWithUpdatedTopic(initial_project_config,
                                                    initial_project_config)

    self.Run('source project-configs update --update-topic=foo ')


if __name__ == '__main__':
  test_case.main()
