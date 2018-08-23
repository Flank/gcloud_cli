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

"""Tests for `gcloud iot registries create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class RegistriesCreateTest(base.CloudIotRegistryBase):

  def _ExpectCreate(self, registry):
    self.client.projects_locations_registries.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesCreateRequest(
            parent='projects/{}/locations/us-central1'.format(self.Project()),
            deviceRegistry=registry),
        registry)

  def testCreate_NoOptions(self, track):
    self.track = track
    registry = self._CreateDeviceRegistry(registry_id='my-registry',)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1')

    self.assertEqual(results, registry)
    self.AssertLogContains('Created registry [my-registry].')

  def testCreate_RegistryUri(self, track):
    self.track = track
    registry = self._CreateDeviceRegistry(registry_id='my-registry',)
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create '
        'projects/{}/locations/us-central1/registries/my-registry'.format(
            self.Project()))

    self.assertEqual(results, registry)
    self.AssertLogContains('Created registry [my-registry].')

  def testCreate_PubSubTopicId(self, track):
    self.track = track
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

  def testCreate_PubSubFullUri(self, track):
    self.track = track
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

  def testCreate_AllOptions(self, track):
    self.track = track
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

  def testCreate_AllOptionsConfigsDisabled(self, track):
    self.track = track
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

  def testCreate_MultipleEventNotificationConfigs(self, track):
    self.track = track
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

  def testCreate_EventConfigWithOnlySubfolder(self, track):
    self.track = track
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

  def testCreate_WithCredential(self, track):
    self.track = track
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


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class RegistriesCreateDeprecatedTest(base.CloudIotRegistryBase):

  def _ExpectCreate(self, registry):
    self.client.projects_locations_registries.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesCreateRequest(
            parent='projects/{}/locations/us-central1'.format(self.Project()),
            deviceRegistry=registry),
        registry)

  def testCreate_EventPubsubDeprecated(self, track):
    self.track = track
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic').RelativeName()
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        event_notification_configs=[(event_pubsub_topic_name, None)])
    self._ExpectCreate(registry)

    results = self.Run(
        'iot registries create my-registry '
        '    --region us-central1 '
        '    --event-pubsub-topic {} '
        '    --enable-mqtt-config'.format(event_pubsub_topic_name))

    self.assertEqual(results, registry)
    self.AssertErrContains('Flag --event-pubsub-topic is deprecated. '
                           'Use --event-notification-config instead.')

  def testCreate_PubsubRemoved(self, track):
    self.track = track
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic').RelativeName()

    with self.AssertRaisesArgumentErrorMatches(
        'Flag --pubsub-topic is removed. Use --event-notification-config '
        'instead.'):
      self.Run(
          'iot registries create my-registry '
          '    --region us-central1 '
          '    --pubsub-topic {} '
          '    --enable-mqtt-config'.format(event_pubsub_topic_name))

  def testCreate_PubsubFlagsMutuallyExclusive(self, track):
    self.track = track
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --event-notification-config: At most one of '
        '--event-notification-config | --event-pubsub-topic | '
        '--pubsub-topic may be specified.'):
      self.Run(
          'iot registries create my-registry '
          '    --region us-central1 '
          '    --event-notification-config topic={0} '
          '    --event-pubsub-topic {0} '
          '    --enable-mqtt-config'.format(event_pubsub_topic_name))


if __name__ == '__main__':
  test_case.main()
