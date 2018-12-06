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

"""Tests for `gcloud iot devices credentials create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class CredentialsCreateTestGA(base.CloudIotBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreate_InvalidType(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        r"argument --type: Invalid choice: 'bad-type'"):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --type bad-type'
          '    --path {}'.format(new_credential_path))
      self.AssertErrContains('Invalid key type [bad-type]')

  def testCreate_MissingType(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    with self.AssertRaisesArgumentErrorMatches(
        'argument --type: Must be specified.'):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --path {}'.format(new_credential_path))

  def testCreate_InvalidPath(self):
    with self.AssertRaisesExceptionMatches(util.InvalidKeyFileError,
                                           'Could not read key file'):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --type rsa-x509-pem'
          '    --path {} '.format(os.path.join(self.temp_path, 'bad.pub')))

  def testCreate_MissingPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --type rsa-x509-pem')

  def testCreate_Empty(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    new_credential = self.messages.DeviceCredential(
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.RSA_X509_PEM,
            key=self.CERTIFICATE_CONTENTS))
    self._ExpectGet([])
    self._ExpectPatch([new_credential])

    results = self.Run(
        'iot devices credentials create '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --type rsa-x509-pem '
        '    --path {}'.format(new_credential_path))

    expected_device = self.messages.Device(id='my-device',
                                           credentials=[new_credential])
    self.assertEqual(results, expected_device)
    self.AssertLogContains('Created credentials for device [my-device].')

  def testCreate_CredentialExists(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.PUBLIC_KEY_CONTENTS)
    old_credential = self.messages.DeviceCredential(
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.RSA_X509_PEM,
            key=self.CERTIFICATE_CONTENTS))
    new_credential = self.messages.DeviceCredential(
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.ES256_PEM,
            key=self.PUBLIC_KEY_CONTENTS))

    self._ExpectGet([old_credential])
    self._ExpectPatch([old_credential, new_credential])

    results = self.Run(
        'iot devices credentials create '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --type es256-pem '
        '    --path {}'.format(new_credential_path))

    expected_device = self.messages.Device(
        id='my-device', credentials=[old_credential, new_credential])
    self.assertEqual(results, expected_device)

  def testCreate_BadExpirationTime(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Failed to parse date/time'):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --type rsa-x509-pem '
          '    --path {} '
          '    --expiration-time BADTIME'.format(new_credential_path))

  def testCreate_IncludeExpirationTime(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    new_credential = self.messages.DeviceCredential(
        expirationTime='2017-01-01T00:00:00.000Z',
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.RSA_X509_PEM,
            key=self.CERTIFICATE_CONTENTS))
    self._ExpectGet([])
    self._ExpectPatch([new_credential])

    results = self.Run(
        'iot devices credentials create '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --type rsa-x509-pem '
        '    --path {} '
        '    --expiration-time 2017-01-01T00:00Z'.format(
            new_credential_path))

    expected_device = self.messages.Device(id='my-device',
                                           credentials=[new_credential])
    self.assertEqual(results, expected_device)

  def testCreate_ThreeCredentialsExist(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    old_credential = self.messages.DeviceCredential(
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.RSA_X509_PEM,
            key=self.CERTIFICATE_CONTENTS))

    self._ExpectGet([old_credential] * 3)

    with self.AssertRaisesExceptionMatches(
        util.InvalidPublicKeySpecificationError,
        'Cannot create a new public key credential for this device; '
        'maximum 3 keys are allowed'):
      self.Run(
          'iot devices credentials create '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --type es256-pem '
          '    --path {}'.format(new_credential_path))

  def testCreate_RelativeName(self):
    new_credential_path = self.Touch(self.temp_path, 'certificate.pub',
                                     contents=self.CERTIFICATE_CONTENTS)
    new_credential = self.messages.DeviceCredential(
        publicKey=self.messages.PublicKeyCredential(
            format=self.key_format_enum.RSA_X509_PEM,
            key=self.CERTIFICATE_CONTENTS))
    self._ExpectGet([])
    self._ExpectPatch([new_credential])

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run(
        'iot devices credentials create '
        '    --device {} '
        '    --type rsa-x509-pem '
        '    --path {}'.format(device_name, new_credential_path))

    expected_device = self.messages.Device(id='my-device',
                                           credentials=[new_credential])
    self.assertEqual(results, expected_device)


class CredentialsCreateTestBeta(CredentialsCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CredentialsCreateTestAlpha(CredentialsCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()

