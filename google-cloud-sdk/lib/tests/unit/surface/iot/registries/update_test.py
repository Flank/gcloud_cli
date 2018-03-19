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
"""Tests for `gcloud iot registries update`."""
from googlecloudsdk.api_lib.cloudiot import registries as registries_api
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class RegistriesUpdateTest(base.CloudIotRegistryBase):

  def _ExpectUpdate(self, registry_name, registry, update_mask):
    self.client.projects_locations_registries.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
            name=registry_name,
            deviceRegistry=registry,
            updateMask=update_mask
        ),
        registry)

  def testUpdate_NoOptions(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        registries_api.NoFieldsSpecifiedError,
        'Must specify at least one field to update.'):
      self.Run('iot registries update my-registry --region us-central1')

  def testUpdate_PubSubFullUri(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_ref = self._CreatePubsubTopic('event-topic')
    state_pubsub_topic_ref = self._CreatePubsubTopic('state-topic')

    registry = self._CreateDeviceRegistry(
        event_notification_configs=[
            (event_pubsub_topic_ref.RelativeName(), None)],
        state_pubsub_topic_name=state_pubsub_topic_ref.RelativeName(),
        http_enabled=None,
        mqtt_enabled=None)
    update_mask = ','.join([
        'event_notification_configs',
        'state_notification_config.pubsub_topic_name'])
    self._ExpectUpdate(registry_name, registry, update_mask)
    result = self.Run(
        'iot registries update my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1}'.format(
            event_pubsub_topic_ref.SelfLink(),
            state_pubsub_topic_ref.SelfLink()))
    self.assertEqual(result, registry)
    self.AssertLogContains('Updated registry [my-registry].')

  def testUpdate_AllOptions(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    state_pubsub_topic_name = self._CreatePubsubTopic(
        'state-topic', project='other-project').RelativeName()

    registry = self._CreateDeviceRegistry(
        event_notification_configs=[(event_pubsub_topic_name, None)],
        state_pubsub_topic_name=state_pubsub_topic_name,
        http_enabled=False)
    update_mask = ','.join([
        'event_notification_configs',
        'state_notification_config.pubsub_topic_name',
        'mqtt_config.mqtt_enabled_state',
        'http_config.http_enabled_state'])
    self._ExpectUpdate(registry_name, registry, update_mask)

    result = self.Run(
        'iot registries update my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0} '
        '    --state-pubsub-topic {1} '
        '    --enable-mqtt-config '
        '    --no-enable-http-config'.format(event_pubsub_topic_name,
                                             state_pubsub_topic_name))

    self.assertEqual(result, registry)
    self.AssertLogContains('Updated registry [my-registry].')

  def testUpdate_RelativeName(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    registry = self._CreateDeviceRegistry()
    update_mask = ','.join([
        'mqtt_config.mqtt_enabled_state',
        'http_config.http_enabled_state'])
    self._ExpectUpdate(registry_name, registry, update_mask)

    result = self.Run(
        'iot registries update {0} '
        '    --enable-mqtt-config '
        '    --enable-http-config'.format(registry_name))

    self.assertEqual(result, registry)

  def testUpdate_MultipleEventNotificationConfigs(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    event_pubsub_topic_name2 = self._CreatePubsubTopic(
        'event-topic2', project='other-project').RelativeName()
    state_pubsub_topic_name = self._CreatePubsubTopic(
        'state-topic', project='other-project').RelativeName()

    registry = self._CreateDeviceRegistry(
        event_notification_configs=[
            (event_pubsub_topic_name, 'myFolder'),
            (event_pubsub_topic_name2, None)],
        state_pubsub_topic_name=state_pubsub_topic_name,
        http_enabled=False)
    update_mask = ','.join([
        'event_notification_configs',
        'state_notification_config.pubsub_topic_name',
        'mqtt_config.mqtt_enabled_state',
        'http_config.http_enabled_state'])
    self._ExpectUpdate(registry_name, registry, update_mask)

    result = self.Run(
        'iot registries update my-registry '
        '    --region us-central1 '
        '    --event-notification-config topic={0},subfolder=myFolder '
        '    --event-notification-config topic={1} '
        '    --state-pubsub-topic {2} '
        '    --enable-mqtt-config '
        '    --no-enable-http-config'.format(event_pubsub_topic_name,
                                             event_pubsub_topic_name2,
                                             state_pubsub_topic_name))

    self.assertEqual(result, registry)
    self.AssertLogContains('Updated registry [my-registry].')

  def testUpdate_EventConfigWithOnlySubfolder(self, track):
    self.track = track
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()

    with self.AssertRaisesArgumentErrorMatches(
        'argument --event-notification-config: Key [topic] required in dict '
        'arg but not provided'):
      self.Run(
          'iot registries update my-registry '
          '    --region us-central1 '
          '    --event-notification-config subfolder=myFolder '
          '    --event-notification-config topic={0} '
          .format(event_pubsub_topic_name))


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class RegistriesUpdateDeprecatedTest(base.CloudIotRegistryBase):

  def _ExpectUpdate(self, registry_name, registry, update_mask):
    self.client.projects_locations_registries.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
            name=registry_name,
            deviceRegistry=registry,
            updateMask=update_mask
        ),
        registry)

  def testUpdate_EventPubsubDeprecated(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    registry = self._CreateDeviceRegistry(
        event_notification_configs=[(event_pubsub_topic_name, None)])
    update_mask = ','.join([
        'event_notification_configs',
        'mqtt_config.mqtt_enabled_state',
        'http_config.http_enabled_state'])
    self._ExpectUpdate(registry_name, registry, update_mask)

    result = self.Run(
        'iot registries update {0} '
        '    --event-pubsub-topic {1} '
        '    --enable-mqtt-config '
        '    --enable-http-config'.format(registry_name,
                                          event_pubsub_topic_name))

    self.assertEqual(result, registry)
    self.AssertErrContains('Flag --event-pubsub-topic is deprecated. '
                           'Use --event-notification-config instead.')

  def testUpdate_PubsubRemoved(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()

    with self.AssertRaisesArgumentErrorMatches(
        'Flag --pubsub-topic is removed. Use --event-notification-config '
        'instead.'):
      self.Run(
          'iot registries update {0} '
          '    --pubsub-topic {1} '
          '    --enable-mqtt-config '
          '    --enable-http-config'.format(registry_name,
                                            event_pubsub_topic_name))

  def testUpdate_PubsubFlagsMutuallyExclusive(self, track):
    self.track = track
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    event_pubsub_topic_name = self._CreatePubsubTopic(
        'event-topic', project='other-project').RelativeName()
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --event-notification-config: At most one of '
        '--event-notification-config | --event-pubsub-topic | '
        '--pubsub-topic may be specified.'):
      self.Run(
          'iot registries update {0} '
          '    --event-pubsub-topic {1} '
          '    --event-notification-config topic={1} '
          '    --enable-mqtt-config'.format(registry_name,
                                            event_pubsub_topic_name))


if __name__ == '__main__':
  test_case.main()
