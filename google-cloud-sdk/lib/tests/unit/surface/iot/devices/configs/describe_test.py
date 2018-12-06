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

"""Tests for `gcloud iot devices configs describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class ConfigsDescribeTestGA(base.CloudIotBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribe(self):
    device_config = self.messages.DeviceConfig(binaryData=b'a')
    self._ExpectGet(config=device_config)

    results = self.Run(
        'iot devices configs describe '
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(results, device_config)

  def testDescribe_Output(self):
    device_config = self.messages.DeviceConfig(
        binaryData=b'a',
        cloudUpdateTime='2017-01-01T00:00Z',
        deviceAckTime='2016-01-01T00:00Z',
        version=42
    )
    self._ExpectGet(config=device_config)

    self.Run(
        'iot devices configs describe '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.AssertOutputEquals("""\
        binaryData: YQ==
        cloudUpdateTime: 2017-01-01T00:00Z
        deviceAckTime: 2016-01-01T00:00Z
        version: '42'
        """, normalize_space=True)

  def testDescribe_NoneConfig(self):
    self._ExpectGet()

    self.Run(
        'iot devices configs describe '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals('')

  def testDescribe_RelativeName(self):
    self._ExpectGet()

    device_name = ('projects/{}/locations/us-central1/registries/my-registry/'
                   'devices/my-device'.format(self.Project()))

    result = self.Run('iot devices configs describe '
                      '--format disable '
                      '--device {}'.format(device_name))

    self.assertIs(result, None)


class ConfigsDescribeTestBeta(ConfigsDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ConfigsDescribeTestAlpha(ConfigsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
