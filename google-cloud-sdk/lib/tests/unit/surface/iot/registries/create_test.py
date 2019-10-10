# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for `gcloud iot registries create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class RegistriesCreateTestGA(base.CloudIotRegistryBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectCreate(self, registry):
    self.client.projects_locations_registries.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesCreateRequest(
            parent='projects/{}/locations/us-central1'.format(self.Project()),
            deviceRegistry=registry),
        registry)

  def testCreate_NoOptions(self):
    registry = self._CreateDeviceRegistry(registry_id='my-registry',)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1')

    self.assertEqual(results, registry)
    self.AssertLogContains('Created registry [my-registry].')

  def testCreate_RegistryUri(self):
    registry = self._CreateDeviceRegistry(registry_id='my-registry',)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create '
        'projects/{}/locations/us-central1/registries/my-registry'.format(
            self.Project()))

    self.assertEqual(results, registry)
    self.AssertLogContains('Created registry [my-registry].')

  def testCreate_PubSubTopicId(self):
    event_pubsub_topic_ref = self._CreatePubsubTopic('event-topic')
    state_pubsub_topic_ref = self._CreatePubsubTopic('state-topic')
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[
            (event_pubsub_topic_ref.RelativeName(), None)],
        state_pubsub_topic_name=state_pubsub_topic_ref.RelativeName())
    self._ExpectCreate(registry)
    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1} '.format(
            event_pubsub_topic_ref.Name(),
            state_pubsub_topic_ref.Name()))
    self.assertEqual(results, registry)

  def testCreate_PubSubFullUri(self):
    event_pubsub_topic_ref = self._CreatePubsubTopic('event-topic')
    state_pubsub_topic_ref = self._CreatePubsubTopic('state-topic')
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[
            (event_pubsub_topic_ref.RelativeName(), None)],
        state_pubsub_topic_name=state_pubsub_topic_ref.RelativeName())
    self._ExpectCreate(registry)
    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1} '.format(
            event_pubsub_topic_ref.SelfLink(),
            state_pubsub_topic_ref.SelfLink()))
    self.assertEqual(results, registry)

  def testCreate_AllOptions(self):
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    state_pubsub_topic_name = self._CreatePubsubTopic(
        'state-topic', project='other-project').RelativeName()
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[(event_pubsub_topic_name, None)],
        state_pubsub_topic_name=state_pubsub_topic_name)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1} '
        '    --enable-mqtt-config '
        '    --enable-http-config'.format(event_pubsub_topic_name,
                                          state_pubsub_topic_name))

    self.assertEqual(results, registry)

  def testCreate_AllOptionsConfigsDisabled(self):
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic').RelativeName()
    state_pubsub_topic_name = self._CreatePubsubTopic(
        'state-topic').RelativeName()
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[(event_pubsub_topic_name, None)],
        state_pubsub_topic_name=state_pubsub_topic_name,
        mqtt_enabled=False,
        http_enabled=False)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1} '
        '    --no-enable-mqtt-config '
        '    --no-enable-http-config'.format(event_pubsub_topic_name,
                                             state_pubsub_topic_name))

    self.assertEqual(results, registry)

  def testCreate_MultipleEventNotificationConfigs(self):
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic').RelativeName()
    event_pubsub_topic_name2 = self._CreatePubsubTopic(
        'event-topic2').RelativeName()
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[
            (event_pubsub_topic_name, 'myFolder'),
            (event_pubsub_topic_name2, None)])
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0},subfolder=myFolder '
        '    --event-notification-config topic={1} '
        .format(event_pubsub_topic_name,
                event_pubsub_topic_name2))

    self.assertEqual(results, registry)

  def testCreate_EventConfigWithOnlySubfolder(self):
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic').RelativeName()

    with self.AssertRaisesArgumentErrorMatches(
        'argument --event-notification-config: Key [topic] required in dict '
        'arg but not provided'):
      self.Run(
          'iot registries create my-registry '
          '    --region us-central1 '
          '    --event-notification-config subfolder=myFolder '
          '    --event-notification-config topic={0} '
          .format(event_pubsub_topic_name))

  def testCreate_WithCredential(self):
    public_key_path = self.Touch(self.temp_path, 'cert1.txt',
                                 self.CERTIFICATE_CONTENTS)
    credentials = [self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS)]
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        credentials=credentials)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --public-key-path {0} '.format(public_key_path))

    self.assertEqual(results, registry)

  @parameterized.parameters(
      ('none', 'NONE'), ('info', 'INFO'), ('error', 'ERROR'), ('Info', 'INFO'),
      ('ErRoR', 'ERROR'), ('NONE', 'NONE'), ('debug', 'DEBUG'),
      ('dEbUg', 'DEBUG'), ('DEBUG', 'DEBUG'))
  def testCreate_WithLogLevel(self, log_level, log_level_enum):
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry', log_level=log_level_enum)
    self._ExpectCreate(registry)

    results = self.Run('iot registries create my-registry '
                       '    --region us-central1'
                       '    --log-level {}'.format(log_level))

    self.assertEqual(results, registry)
    self.AssertLogContains('Created registry [my-registry].')

  def testCreate_WithInvalidLogLevel(self):
    with self.AssertRaisesArgumentErrorMatches(
        "argument --log-level: Invalid choice: 'just-whenever-dude'"):
      self.Run('iot registries create my-registry '
               '    --region us-central1'
               '    --log-level just-whenever-dude')


class RegistriesCreateTestBeta(RegistriesCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RegistriesCreateTestAlpha(RegistriesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
