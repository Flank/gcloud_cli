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

"""Tests for `gcloud iot devices credentials list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class CredentialsListTestGA(base.CloudIotBase):

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

  def testList(self):
    self._ExpectGet(self.device_credentials)

    results = self.Run(
        'iot devices credentials list'
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(
        list(results),
        [
            {
                'expirationTime': '2016-01-01T00:00Z',
                'publicKey': {
                    'format': 'RSA_X509_PEM',
                    'key': self.CERTIFICATE_CONTENTS
                },
                'index': 0
            },
            {
                'expirationTime': '2017-01-01T00:00Z',
                'publicKey': {
                    'format': 'ES256_PEM',
                    'key': self.PUBLIC_KEY_CONTENTS
                },
                'index': 1
            },
        ])

  def testList_Output(self):
    self._ExpectGet(self.device_credentials)

    self.Run(
        'iot devices credentials list'
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals("""\
        INDEX  FORMAT        EXPIRATION_TIME
        0      RSA_X509_PEM  2016-01-01T00:00Z
        1      ES256_PEM     2017-01-01T00:00Z
        """, normalize_space=True)

  def testList_RelativeName(self):
    self._ExpectGet(self.device_credentials)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.Run(
        'iot devices credentials list'
        '    --device {}'.format(device_name))
    self.AssertOutputEquals("""\
        INDEX  FORMAT        EXPIRATION_TIME
        0      RSA_X509_PEM  2016-01-01T00:00Z
        1      ES256_PEM     2017-01-01T00:00Z
        """, normalize_space=True)


class CredentialsListTestBeta(CredentialsListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CredentialsListTestAlpha(CredentialsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
