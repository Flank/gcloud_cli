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

"""Tests for `gcloud iot devices credentials update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class CredentialsUpdateTestGA(base.CloudIotBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.device_credentials = [
        self.messages.DeviceCredential(
            expirationTime='2016-01-01T00:00Z',
            publicKey=self.messages.PublicKeyCredential(
                format=self.key_format_enum.RSA_X509_PEM,
                key=self.CERTIFICATE_CONTENTS
            )),
        self.messages.DeviceCredential(
            expirationTime='2017-01-01T00:00Z',
            publicKey=self.messages.PublicKeyCredential(
                format=self.key_format_enum.ES256_PEM,
                key=self.PUBLIC_KEY_CONTENTS
            ))
    ]

  def testUpdate(self):
    new_device_credential = self.messages.DeviceCredential(
        expirationTime='2018-01-01T00:00:00.000Z',
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.ES256_PEM,
            key=self.PUBLIC_KEY_CONTENTS))
    self._ExpectGet(self.device_credentials)
    self._ExpectPatch([self.device_credentials[0], new_device_credential])

    result = self.Run(
        'iot devices credentials update 1'
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --expiration-time 2018-01-01T00:00Z')

    expected_device = self.messages.Device(
        id='my-device',
        credentials=[self.device_credentials[0], new_device_credential])
    self.assertEqual(result, expected_device)
    self.AssertLogContains('Updated credentials for device [my-device].')

  def testUpdate_BadIndex(self):
    self._ExpectGet(self.device_credentials)

    with self.AssertRaisesExceptionMatches(util.BadCredentialIndexError,
                                           'z'):
      self.Run(
          'iot devices credentials update 2'
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --expiration-time 2018-01-01T00:00Z')

  def testUpdate_NoChange(self):
    self._ExpectGet(self.device_credentials)
    self._ExpectPatch(self.device_credentials)

    result = self.Run(
        'iot devices credentials update 1'
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    expected_device = self.messages.Device(
        id='my-device',
        credentials=self.device_credentials)
    self.assertEqual(result, expected_device)

  def testUpdate_InvalidTime(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Failed to parse date/time'):
      self.Run(
          'iot devices credentials update 2'
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1'
          '    --expiration-time bad-time')

  def testUpdate_RelativeName(self):
    new_device_credential = self.messages.DeviceCredential(
        expirationTime='2018-01-01T00:00:00.000Z',
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.ES256_PEM,
            key=self.PUBLIC_KEY_CONTENTS))
    self._ExpectGet(self.device_credentials)
    self._ExpectPatch([self.device_credentials[0], new_device_credential])

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    result = self.Run(
        'iot devices credentials update 1'
        '    --device {} '
        '    --expiration-time 2018-01-01T00:00Z'.format(device_name))

    expected_device = self.messages.Device(
        id='my-device',
        credentials=[self.device_credentials[0], new_device_credential])
    self.assertEqual(result, expected_device)


class CredentialsUpdateTestBeta(CredentialsUpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CredentialsUpdateTestAlpha(CredentialsUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
