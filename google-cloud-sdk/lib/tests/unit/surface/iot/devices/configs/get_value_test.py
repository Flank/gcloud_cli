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

"""Tests for `gcloud iot devices configs get-value`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base

from six.moves import range  # pylint: disable=redefined-builtin


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ConfigsGetValueTest(base.CloudIotBase):

  def testGetValue(self, track):
    self.track = track
    data = bytes(range(256))
    device_config = self.messages.DeviceConfig(binaryData=data)
    self._ExpectGet(config=device_config)

    results = self.Run(
        'iot devices configs get-value '
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(results, data)

  def testGetValue_Output(self, track):
    self.track = track
    # Before output values get written to stdout, they are converted to unicode
    # and encoded using utf-8. This means that while the output will appear the
    # same when printed, the underlying byte representation will differ.
    # In order to test this properly we need to set the encoding to 8-bit ASCII
    # so the utf-8 encoding doesn't happen, and convert the data to unicode
    # manually because python can't handle this.
    self.SetEncoding('ISO-8859-1')
    # We want to test this handles binary data. Values 0-126 work between both
    # Windows and UNIX systems.
    data = bytes(range(126))
    unicode_data = data.decode('ISO-8859-1')
    device_config = self.messages.DeviceConfig(
        binaryData=data,
        cloudUpdateTime='2017-01-01T00:00Z',
        deviceAckTime='2016-01-01T00:00Z',
        version=42
    )
    self._ExpectGet(config=device_config)

    self.Run(
        'iot devices configs get-value '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.AssertOutputEquals(unicode_data)

  def testGetValue_NoData(self, track):
    self.track = track
    device_config = self.messages.DeviceConfig()
    self._ExpectGet(config=device_config)

    self.Run(
        'iot devices configs get-value '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.AssertOutputEquals('')

  def testGetValue_NoneConfig(self, track):
    self.track = track
    self._ExpectGet()

    with self.AssertRaisesExceptionMatches(
        util.BadDeviceError,
        'Device [my-device] is missing configuration data'):
      self.Run(
          'iot devices configs get-value '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1')
    self.AssertOutputEquals('')

  def testGetValue_RelativeName(self, track):
    self.track = track
    data = bytes(range(256))
    device_config = self.messages.DeviceConfig(binaryData=data)
    self._ExpectGet(config=device_config)

    device_name = ('projects/{}/locations/us-central1/registries/my-registry/'
                   'devices/my-device'.format(self.Project()))
    results = self.Run('iot devices configs get-value --format disable '
                       '--device ' + device_name)

    self.assertEqual(results, data)


if __name__ == '__main__':
  test_case.main()

