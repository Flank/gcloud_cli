# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base class for all ml platform tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock


from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.api_lib.cloudiot import registries as registries_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from six.moves import range


class CloudIotBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                   sdk_test_base.WithLogCapture):
  """Base class for Cloud IoT unit tests."""
  ENABLE_DEVICE_DEPRECATION_WARNING = ('WARNING: Flag --[no-]enable-device is '
                                       'deprecated. Use --[no-]blocked '
                                       'instead.')

  CERTIFICATE_CONTENTS = ('-----BEGIN CERTIFICATE-----\n'
                          '000000000000000000000000000\n'
                          '-----END CERTIFICATE-----\n'
                          '-----BEGIN CERTIFICATE-----\n'
                          '111111111111111111111111111\n'
                          '-----END CERTIFICATE-----')

  PUBLIC_KEY_CONTENTS = ('-----BEGIN PUBLIC KEY-----\n'
                         '000000000000000000000000000\n'
                         '-----END PUBLIC KEY-----\n'
                         '-----BEGIN PUBLIC KEY-----\n'
                         '111111111111111111111111111\n'
                         '-----END PUBLIC KEY-----')

  def _GetGateway(self, name='my-gateway', num_id=12345):
    gateway_enum = (
        self.messages.GatewayConfig.GatewayTypeValueValuesEnum.GATEWAY)
    auth_method_enum = (
        self.messages.GatewayConfig.GatewayAuthMethodValueValuesEnum.
        ASSOCIATION_ONLY)

    return self.messages.Device(
        id=name,
        numId=num_id,
        blocked=False,
        gatewayConfig=self.messages.GatewayConfig(
            gatewayType=gateway_enum, gatewayAuthMethod=auth_method_enum))

  def _ExpectGet(self, credentials=None, config=None):
    credentials = credentials or []
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesGetRequest(
            name=device_name),
        self.messages.Device(
            id='my-device',
            credentials=credentials,
            config=config))

  def _ExpectPatch(self, credentials):
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=self.messages.Device(credentials=credentials),
            updateMask='credentials'),
        self.messages.Device(id='my-device', credentials=credentials))

  def _CreateAdditionalProperty(self, key, value):
    return self.messages.Device.MetadataValue.AdditionalProperty(key=key,
                                                                 value=value)

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(client_class=apis.GetClientClass('cloudiot',
                                                               'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('cloudiot', 'v1')
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('cloudiot', 'v1')

    self.certificate_key = self.Touch(self.temp_path, 'certificate.pub',
                                      contents=self.CERTIFICATE_CONTENTS)
    self.public_key = self.Touch(self.temp_path, 'public.pub',
                                 contents=self.PUBLIC_KEY_CONTENTS)
    self.key_format_enum = (
        self.messages.PublicKeyCredential.FormatValueValuesEnum)


class CloudIotRegistryBase(CloudIotBase):
  """Base Class for Cloud IoT Registry unit tests."""

  OTHER_CERTIFICATE_CONTENTS = ('-----BEGIN CERTIFICATE-----\n'
                                '111111111111111111111111111\n'
                                '-----END CERTIFICATE-----\n'
                                '-----BEGIN CERTIFICATE-----\n'
                                '000000000000000000000000000\n'
                                '-----END CERTIFICATE-----')

  def SetUp(self):
    self.registries_client = registries_api.RegistriesClient(self.client,
                                                             self.messages)

    # For convenience
    self.mqtt_enabled = self.registries_client.mqtt_config_enum.MQTT_ENABLED
    self.mqtt_disabled = self.registries_client.mqtt_config_enum.MQTT_DISABLED

    self.http_enabled = self.registries_client.http_config_enum.HTTP_ENABLED
    self.http_disabled = self.registries_client.http_config_enum.HTTP_DISABLED
    self.registries_client = registries_api.RegistriesClient(self.client,
                                                             self.messages)

  def _GetRegistryRef(self, project_id, registry_id):
    return self.resources.Create(
        'cloudiot.projects.locations.registries',
        locationsId='us-central1', projectsId=project_id,
        registriesId=registry_id)

  def _ExpectPatch(self, credentials):
    registry_name = self._GetRegistryRef(
        self.Project(), 'my-registry').RelativeName()
    self.client.projects_locations_registries.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
            name=registry_name,
            deviceRegistry=
            self.messages.DeviceRegistry(credentials=credentials),
            updateMask='credentials'),
        self.messages.DeviceRegistry(id='my-registry', credentials=credentials))

  def _ExpectGet(self, credentials=None):
    credentials = credentials or []
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    self.client.projects_locations_registries.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesGetRequest(
            name=registry_name),
        self.messages.DeviceRegistry(
            id='my-registry',
            credentials=credentials))

  def _CreateRegistryCredential(self, contents, x509_details=None):
    format_enum = self.messages.PublicKeyCertificate.FormatValueValuesEnum
    return self.messages.RegistryCredential(
        publicKeyCertificate=self.messages.PublicKeyCertificate(
            certificate=contents,
            format=format_enum.X509_CERTIFICATE_PEM,
            x509Details=x509_details))

  def _CreatePubsubTopic(self, name, project=None):
    project = project or self.Project()
    return self.resources.Create(
        'pubsub.projects.topics',
        projectsId=project, topicsId=name)

  def _CreateDeviceRegistry(self,
                            registry_id=None,
                            credentials=None,
                            mqtt_enabled=True,
                            http_enabled=True,
                            event_notification_configs=None,
                            state_pubsub_topic_name=None,
                            log_level=None):
    credentials = credentials or []
    event_configs = []
    if event_notification_configs is not None:
      event_configs = [
          self.messages.EventNotificationConfig(
              pubsubTopicName=config[0], subfolderMatches=config[1])
          for config in event_notification_configs]
    state_notification_config = None
    if state_pubsub_topic_name is not None:
      state_notification_config = self.messages.StateNotificationConfig(
          pubsubTopicName=state_pubsub_topic_name)

    if mqtt_enabled is not None:
      mqtt_state = self.mqtt_enabled if mqtt_enabled else self.mqtt_disabled
      mqtt_config = self.messages.MqttConfig(mqttEnabledState=mqtt_state)
    else:
      mqtt_config = None
    if http_enabled is not None:
      http_state = self.http_enabled if http_enabled else self.http_disabled
      http_config = self.messages.HttpConfig(httpEnabledState=http_state)
    else:
      http_config = None

    if log_level is not None:
      log_level = (
          self.messages.DeviceRegistry.LogLevelValueValuesEnum(log_level))

    registry = self.messages.DeviceRegistry(
        id=registry_id,
        credentials=credentials,
        eventNotificationConfigs=event_configs,
        stateNotificationConfig=state_notification_config,
        mqttConfig=mqtt_config,
        httpConfig=http_config,
        logLevel=log_level)

    return registry

  def _MakeRegistries(self, n=10, project=None):
    registries = []
    for i in range(n):
      registry_name = 'projects/{}/locations/us-central1/registries/r{}'.format(
          project or self.Project(), i)
      registry = self.messages.DeviceRegistry(name=registry_name)
      registries.append(registry)
    return registries

  def _ExpectListRegistries(self, registries, project=None):
    project = project or self.Project()
    self.client.projects_locations_registries.List.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesListRequest(
            parent='projects/{}/locations/us-central1'.format(project)),
        self.messages.ListDeviceRegistriesResponse(
            deviceRegistries=registries))


class CloudIotDeviceBase(CloudIotBase):
  """Base for testing devices commands."""

  def _MakeDevices(self, n=10, registry='my-registry', project=None,
                   gateway_config=None):
    devices = []
    for i in range(n):
      device_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/{}/'
                     'devices/d{}').format(project or self.Project(),
                                           registry, i)
      device = self.messages.Device(
          name=device_name,
          id='d{}'.format(i),
          numId=i,
          blocked=False,
          gatewayConfig=gateway_config,
      )
      devices.append(device)
    return devices

  def _ExpectListDevices(self, devices, device_ids=None, device_num_ids=None,
                         registry='my-registry', field_mask='blocked,name',
                         project=None, gateway_type=None,
                         gateway_list_device=None):
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/{}').format(project or self.Project(),
                                             registry)
    self.client.projects_locations_registries_devices.List.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesListRequest(
            parent=registry_name,
            deviceIds=device_ids or [],
            deviceNumIds=device_num_ids or [],
            fieldMask=field_mask,
            gatewayListOptions_gatewayType=gateway_type,
            gatewayListOptions_associationsGatewayId=gateway_list_device
        ),
        self.messages.ListDevicesResponse(
            devices=devices))
