# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for `gcloud iot devices commands send`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class CommandsSendTest(base.CloudIotBase):

  def _GetSendCommandMessage(self, device_name, command_request):
    msg_name = ('CloudiotProjectsLocationsRegistries'
                'DevicesSendCommandToDeviceRequest')
    msg_type = getattr(self.messages, msg_name)
    return msg_type(name=device_name,
                    sendCommandToDeviceRequest=command_request)

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testSendWithCommandLine(self):
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    command_request = self.messages.SendCommandToDeviceRequest(
        binaryData=b'test_command')
    send_request = self._GetSendCommandMessage(device_name, command_request)
    expected_response = self.messages.SendCommandToDeviceResponse()
    (self.client.projects_locations_registries_devices.
     SendCommandToDevice.Expect(request=send_request,
                                response=expected_response))
    actual_response = self.Run('iot devices commands send --device my-device '
                               '--registry my-registry '
                               '--region us-central1 '
                               '--command-data {}'.format('test_command'))

    self.assertEqual(actual_response, expected_response)

  def testSendWithFolder(self):
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    command_request = self.messages.SendCommandToDeviceRequest(
        binaryData=b'test_command', subfolder='mydevices')
    send_request = self._GetSendCommandMessage(device_name, command_request)
    expected_response = self.messages.SendCommandToDeviceResponse()
    (self.client.projects_locations_registries_devices.
     SendCommandToDevice.Expect(request=send_request,
                                response=expected_response))
    actual_response = self.Run('iot devices commands send --device my-device '
                               '--registry my-registry '
                               '--region us-central1 '
                               '--subfolder mydevices '
                               '--command-data {}'.format('test_command'))

    self.assertEqual(actual_response, expected_response)

  def testSendWithFile(self):
    file_path = self.Touch(self.root_path, contents='command_data')
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    command_request = self.messages.SendCommandToDeviceRequest(
        binaryData=b'command_data', subfolder='mydevices')
    send_request = self._GetSendCommandMessage(device_name, command_request)
    expected_response = self.messages.SendCommandToDeviceResponse()
    (self.client.projects_locations_registries_devices.
     SendCommandToDevice.Expect(request=send_request,
                                response=expected_response))
    actual_response = self.Run('iot devices commands send --device my-device '
                               '--registry my-registry '
                               '--region us-central1 '
                               '--subfolder mydevices '
                               '--command-file {}'.format(file_path))

    self.assertEqual(actual_response, expected_response)

  def testSendWithMissingFileFails(self):
    fake_path = 'fake/path/to_file'
    with self.assertRaisesRegex(
        ValueError,
        r"Command File \[(b')?{}'?\] can not be opened".format(fake_path)):
      self.Run('iot devices commands send --device my-device '
               '--registry my-registry '
               '--region us-central1 '
               '--subfolder mydevices '
               '--command-file {}'.format(fake_path))

if __name__ == '__main__':
  test_case.main()
