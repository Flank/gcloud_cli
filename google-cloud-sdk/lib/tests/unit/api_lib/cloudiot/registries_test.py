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
"""Tests for the Cloud IOT Registries library."""
from googlecloudsdk.api_lib.cloudiot import registries as registries_api
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.cloudiot import base


class RegistriesTest(base.CloudIotRegistryBase):

  def SetUp(self):
    self.registries_client = registries_api.RegistriesClient(self.client,
                                                             self.messages)
    self.location_ref = resources.REGISTRY.Create(
        'cloudiot.projects.locations',
        locationsId='us-central1', projectsId=self.Project())
    self.registry_ref = resources.REGISTRY.Create(
        'cloudiot.projects.locations.registries',
        locationsId='us-central1', projectsId=self.Project(),
        registriesId='my-registry')

    # Define separately from registry_ref because we know that this is what the
    # API expects
    self.registry_name = (
        'projects/{}/locations/us-central1/registries/my-registry'.format(
            self.Project()))

  def _ExpectCreate(self, registry):
    self.client.projects_locations_registries.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesCreateRequest(
            parent='projects/{}/locations/us-central1'.format(self.Project()),
            deviceRegistry=registry),
        registry)

  def testCreate_NoOptions(self):
    registry = self.messages.DeviceRegistry(id='my-registry')
    self._ExpectCreate(registry)

    result = self.registries_client.Create(self.location_ref, 'my-registry')

    self.assertEqual(result, registry)

  def testCreate_AllOptions(self):
    event_pubsub_topic_ref = self._CreatePubsubTopic('event-topic')
    event_configs = [
        self.messages.EventNotificationConfig(
            pubsubTopicName=event_pubsub_topic_ref.RelativeName())]
    state_pubsub_topic_ref = self._CreatePubsubTopic('state-topic')
    format_enum = self.messages.PublicKeyCertificate.FormatValueValuesEnum
    credentials = [self.messages.RegistryCredential(
        publicKeyCertificate=self.messages.PublicKeyCertificate(
            certificate=self.CERTIFICATE_CONTENTS,
            format=format_enum.X509_CERTIFICATE_PEM))]
    registry = self._CreateDeviceRegistry(
        registry_id='my-registry',
        http_enabled=False,
        credentials=credentials,
        event_notification_configs=[
            (event_pubsub_topic_ref.RelativeName(), None)],
        state_pubsub_topic_name=state_pubsub_topic_ref.RelativeName())
    self._ExpectCreate(registry)

    result = self.registries_client.Create(
        self.location_ref, 'my-registry',
        credentials=credentials,
        event_notification_configs=event_configs,
        state_pubsub_topic=state_pubsub_topic_ref,
        mqtt_enabled_state=self.mqtt_enabled,
        http_enabled_state=self.http_disabled)

    self.assertEqual(result, registry)

  def testDelete(self):
    self.client.projects_locations_registries.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDeleteRequest(
            name=self.registry_name),
        self.messages.Empty())

    result = self.registries_client.Delete(self.registry_ref)

    self.assertEqual(result, self.messages.Empty())

  def testGet(self):
    registry = self.messages.DeviceRegistry(id='my-registry')
    self.client.projects_locations_registries.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesGetRequest(
            name=self.registry_name),
        registry)

    result = self.registries_client.Get(self.registry_ref)

    self.assertEqual(result, registry)

  def _ExpectList(self, registries, batch_size=100, limit=None):
    """Create expected List() call(s).

    Based on the number of registries and batching parameters.

    Args:
      registries: list of DeviceRegistry
      batch_size: int, the number of results in each page
      limit: int or None, the total number of registries to limit
    """
    if limit:
      registries = registries[:limit]

    slices, token_pairs = list_slicer.SliceList(registries, batch_size)

    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.client.projects_locations_registries.List.Expect(
          self.messages.CloudiotProjectsLocationsRegistriesListRequest(
              parent='projects/{}/locations/us-central1'.format(self.Project()),
              pageToken=current_token, pageSize=batch_size),
          self.messages.ListDeviceRegistriesResponse(
              deviceRegistries=registries[slice_],
              nextPageToken=next_token))

  def testList(self):
    registries = [
        self.messages.DeviceRegistry(id='r{}'.format(i)) for i in range(200)
    ]
    self._ExpectList(registries)

    result = self.registries_client.List(self.location_ref)

    self.assertEqual(list(result), registries)

  def testList_AllOptions(self):
    limit = 150
    page_size = 50
    registries = [
        self.messages.DeviceRegistry(id='r{}'.format(i)) for i in range(200)
    ]
    self._ExpectList(registries, batch_size=page_size, limit=limit)

    result = self.registries_client.List(self.location_ref, limit=limit,
                                         page_size=page_size)

    # Verify that only `limit` items were returned
    self.assertEqual(list(result), registries[:limit])

  def testPatch_NoOptions(self):
    with self.AssertRaisesExceptionMatches(
        registries_api.NoFieldsSpecifiedError, 'at least one field to update'):
      self.registries_client.Patch(self.registry_ref)

  def testPatch_SomeOptions(self):
    registry = self._CreateDeviceRegistry(mqtt_enabled=True, http_enabled=None)
    self.client.projects_locations_registries.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
            name=self.registry_name,
            deviceRegistry=registry,
            updateMask=(
                'mqtt_config.mqtt_enabled_state')),
        registry)

    result = self.registries_client.Patch(
        self.registry_ref,
        mqtt_enabled_state=self.mqtt_enabled)

    self.assertEqual(result, registry)

  def testPatch_AllOptions(self):
    event_pubsub_topic_ref = self._CreatePubsubTopic('event-topic')
    event_configs = [
        self.messages.EventNotificationConfig(
            pubsubTopicName=event_pubsub_topic_ref.RelativeName())]
    state_pubsub_topic_ref = self._CreatePubsubTopic('state-topic')
    format_enum = self.messages.PublicKeyCertificate.FormatValueValuesEnum
    credentials = [self.messages.RegistryCredential(
        publicKeyCertificate=self.messages.PublicKeyCertificate(
            certificate=self.CERTIFICATE_CONTENTS,
            format=format_enum.X509_CERTIFICATE_PEM))]
    registry = self._CreateDeviceRegistry(
        credentials=credentials,
        event_notification_configs=[
            (event_pubsub_topic_ref.RelativeName(), None)],
        state_pubsub_topic_name=state_pubsub_topic_ref.RelativeName(),
        mqtt_enabled=True,
        http_enabled=True)

    self.client.projects_locations_registries.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
            name=self.registry_name,
            deviceRegistry=registry,
            updateMask=(
                'credentials,'
                'event_notification_configs,'
                'state_notification_config.pubsub_topic_name,'
                'mqtt_config.mqtt_enabled_state,'
                'http_config.http_enabled_state')),
        registry)

    result = self.registries_client.Patch(
        self.registry_ref,
        credentials=credentials,
        event_notification_configs=event_configs,
        state_pubsub_topic=state_pubsub_topic_ref,
        mqtt_enabled_state=self.mqtt_enabled,
        http_enabled_state=self.http_enabled)

    self.assertEqual(result, registry)


if __name__ == '__main__':
  test_case.main()
