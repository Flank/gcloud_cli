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

"""Tests for `gcloud iot devices create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
from dateutil import tz

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class DevicesCreateTest(base.CloudIotBase, parameterized.TestCase):

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

    self.StartObjectPatch(times, 'LOCAL', tz.tzutc())

    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectCreate(self, device):
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    self.client.projects_locations_registries_devices.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesCreateRequest(
            parent=registry_name,
            device=device),
        device)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_NoOptions(self, track):
    self.track = track
    device = self.messages.Device(
        id='my-device',
        blocked=False
    )
    self._ExpectCreate(device)

    results = self.Run(
        'iot devices create my-device '
        '    --registry my-registry'
        '    --region us-central1')

    self.assertEqual(results, device)
    self.AssertLogContains('Created device [my-device].')

  @parameterized.parameters(itertools.product(
      [calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA,
       calliope_base.ReleaseTrack.GA],
      [(True, '--blocked'),
       (False, '--no-blocked')]
  ))
  def testCreate_BlockedFlags(self, track, data):
    blocked, blocked_flag = data
    self.track = track
    device = self.messages.Device(
        id='my-device',
        blocked=blocked,
    )
    self._ExpectCreate(device)

    results = self.Run(
        'iot devices create my-device '
        '    --registry my-registry'
        '    --region us-central1'
        '    {} '.format(blocked_flag)
    )

    self.assertEqual(results, device)

  @parameterized.parameters(itertools.product(
      [calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA,
       calliope_base.ReleaseTrack.GA],
      [('rsa-pem', 'RSA_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
       ('RSA_PEM', 'RSA_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
       ('es256-pem', 'ES256_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
       ('ES256_PEM', 'ES256_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
       ('rsa-x509-pem', 'RSA_X509_PEM', base.CloudIotBase.CERTIFICATE_CONTENTS),
       ('RSA_X509_PEM', 'RSA_X509_PEM', base.CloudIotBase.CERTIFICATE_CONTENTS),
       ('es256-x509-pem', 'ES256_X509_PEM',
        base.CloudIotBase.CERTIFICATE_CONTENTS),
       ('ES256_X509_PEM', 'ES256_X509_PEM',
        base.CloudIotBase.CERTIFICATE_CONTENTS),]
  ))
  def testCreate_ValidCredentialTypes(self, track, data):
    key_type, type_enum, key_contents = data
    self.track = track
    key_path = self.Touch(self.temp_path, 'temp.pub', contents=key_contents)
    expiration_time = '2017-01-01T00:00:00.000Z'
    device = self.messages.Device(
        id='my-device',
        blocked=False,
        credentials=[
            self.messages.DeviceCredential(
                expirationTime=expiration_time,
                publicKey=self.messages.PublicKeyCredential(
                    format=getattr(self.key_format_enum, type_enum),
                    key=key_contents))]
    )

    self._ExpectCreate(device)

    results = self.Run(
        ('iot devices create my-device '
         '    --registry my-registry'
         '    --region us-central1'
         '    --public-key '
         '      path={},type={},expiration-time={}').format(key_path,
                                                            key_type,
                                                            expiration_time))
    self.assertEqual(results, device)
    self.AssertLogContains('Created device [my-device].')

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_WithCredentialsDeprecatedTypes(self, track):
    self.track = track
    new_credential_cert_path = self.Touch(self.temp_path, 'certificate.pub',
                                          contents=self.CERTIFICATE_CONTENTS)
    new_credential_key_path = self.Touch(self.temp_path, 'key.pub',
                                         contents=self.PUBLIC_KEY_CONTENTS)
    device = self.messages.Device(
        id='my-device',
        blocked=False,
        credentials=[
            self.messages.DeviceCredential(
                expirationTime='2017-01-01T00:00:00.000Z',
                publicKey=self.messages.PublicKeyCredential(
                    format=self.key_format_enum.RSA_X509_PEM,
                    key=self.CERTIFICATE_CONTENTS
                )
            ),
            self.messages.DeviceCredential(
                publicKey=self.messages.PublicKeyCredential(
                    format=self.key_format_enum.ES256_PEM,
                    key=self.PUBLIC_KEY_CONTENTS
                )
            )
        ]
    )
    self._ExpectCreate(device)

    results = self.Run(
        ('iot devices create my-device '
         '    --registry my-registry'
         '    --region us-central1'
         '    --public-key '
         '      path={},type=rs256,expiration-time=2017-01-01T00:00:00Z'
         '    --public-key path={},type=es256').format(new_credential_cert_path,
                                                       new_credential_key_path))
    self.assertEqual(results, device)
    self.AssertLogContains('Created device [my-device].')

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_WithCredentialsBadKeySpecification(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'valid keys are [expiration-time, path, type]; received: bad-key'):
      self.Run(
          ('iot devices create my-device '
           '      --registry my-registry'
           '    --region us-central1'
           '    --public-key path={},type=es256,bad-key=bad-value').format(
               self.public_key))

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_WithCredentialsBadKeyType(self, track):
    self.track = track
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.PUBLIC_KEY_CONTENTS)
    with self.assertRaisesRegex(
        ValueError, r'Invalid key type \[bad-key-type\]'):
      self.Run(
          ('iot devices create my-device '
           '    --registry my-registry'
           '    --region us-central1'
           '    --public-key path={},type=bad-key-type,').format(
               new_credential_path))

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_WithCredentialsBadDateTime(self, track):
    self.track = track
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.PUBLIC_KEY_CONTENTS)
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Failed to parse date/time'):
      self.Run(
          ('iot devices create my-device '
           '    --registry my-registry'
           '    --region us-central1'
           '    --public-key path={},type=es256,expiration-time=not-a-datetime,'
          ).format(new_credential_path))

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_WithMetadata(self, track):
    self.track = track
    metadata_path = self.Touch(self.temp_path, 'value.txt', 'file_value')
    device = self.messages.Device(
        id='my-device',
        blocked=False,
        metadata=self.messages.Device.MetadataValue(
            additionalProperties=[
                self._CreateAdditionalProperty('key', 'value'),
                self._CreateAdditionalProperty('file_key', 'file_value')])
    )
    self._ExpectCreate(device)

    self.Run(
        ('iot devices create my-device '
         '    --registry my-registry'
         '    --region us-central1'
         '    --metadata=key=value '
         '    --metadata-from-file=file_key={} '.format(metadata_path)))

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testCreate_RelativeName(self, track):
    self.track = track
    device = self.messages.Device(
        id='my-device',
        blocked=False
    )
    self._ExpectCreate(device)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run(
        'iot devices create {}'.format(device_name))

    self.assertEqual(results, device)


if __name__ == '__main__':
  test_case.main()
