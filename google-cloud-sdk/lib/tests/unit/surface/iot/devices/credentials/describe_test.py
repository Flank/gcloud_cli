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

"""Tests for `gcloud iot devices credentials describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class CredentialsDescribeTestGA(base.CloudIotBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribe(self):
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)
    results = self.Run(
        'iot devices credentials describe 0'
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(results, device_credentials[0])

  def testDescribe_Output(self):
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(
            expirationTime='2017-01-01T00:00Z',
            publicKey=self.messages.PublicKeyCredential(
                format=self.key_format_enum.RSA_X509_PEM,
                key='dummy contents')),
    ]
    self._ExpectGet(device_credentials)
    self.Run(
        'iot devices credentials describe 1'
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals("""\
        expirationTime: 2017-01-01T00:00Z
        publicKey:
          format: RSA_X509_PEM
          key: dummy contents
        """, normalize_space=True)

  def testDescribe_BadIndex(self):
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)

    with self.AssertRaisesExceptionMatches(
        util.BadCredentialIndexError,
        'Invalid credential index [2]; device [my-device] has 2 credentials'):
      self.Run(
          'iot devices credentials describe 2'
          '    --format disable '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1')

  def testDescribe_RelativeName(self):
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())

    results = self.Run(
        'iot devices credentials describe 0'
        '    --format disable '
        '    --device {} '.format(device_name))

    self.assertEqual(results, device_credentials[0])


class CredentialsDescribeTestBeta(CredentialsDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CredentialsDescribeTestAlpha(CredentialsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
