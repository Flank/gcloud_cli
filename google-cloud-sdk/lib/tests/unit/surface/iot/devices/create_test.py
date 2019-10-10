# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from dateutil import tz

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import util as command_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class DevicesCreateTestGA(base.CloudIotBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
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

  def testCreate_NoOptions(self):
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

  @parameterized.parameters(
      (True, '--blocked'),
      (False, '--no-blocked')
  )
  def testCreate_BlockedFlags(self, blocked, blocked_flag):
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

  @parameterized.parameters(
      ('rsa-pem', 'RSA_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
      ('RSA_PEM', 'RSA_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
      ('es256-pem', 'ES256_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
      ('ES256_PEM', 'ES256_PEM', base.CloudIotBase.PUBLIC_KEY_CONTENTS),
      ('rsa-x509-pem', 'RSA_X509_PEM', base.CloudIotBase.CERTIFICATE_CONTENTS),
      ('RSA_X509_PEM', 'RSA_X509_PEM', base.CloudIotBase.CERTIFICATE_CONTENTS),
      ('es256-x509-pem', 'ES256_X509_PEM',
       base.CloudIotBase.CERTIFICATE_CONTENTS),
      ('ES256_X509_PEM', 'ES256_X509_PEM',
       base.CloudIotBase.CERTIFICATE_CONTENTS),
  )
  def testCreate_ValidCredentialTypes(self, key_type, type_enum, key_contents):
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

  def testCreate_WithCredentialsDeprecatedTypes(self):
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

  def testCreate_WithCredentialsBadKeySpecification(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'valid keys are [expiration-time, path, type]; received: bad-key'):
      self.Run(
          ('iot devices create my-device '
           '      --registry my-registry'
           '    --region us-central1'
           '    --public-key path={},type=es256,bad-key=bad-value').format(
               self.public_key))

  def testCreate_WithCredentialsBadKeyType(self):
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

  def testCreate_WithCredentialsBadDateTime(self):
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

  def testCreate_WithMetadata(self):
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

  def testCreate_RelativeName(self):
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


class DevicesCreateTestBeta(DevicesCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  @parameterized.parameters(
      ('none', 'NONE'), ('info', 'INFO'), ('error', 'ERROR'), ('Info', 'INFO'),
      ('ErRoR', 'ERROR'), ('NONE', 'NONE'), ('debug', 'DEBUG'),
      ('dEbUg', 'DEBUG'), ('DEBUG', 'DEBUG'))
  def testCreate_WithLogLevel(self, log_level, log_level_enum):
    device = self.messages.Device(
        id='my-device',
        blocked=False,
        logLevel=self.messages.Device.LogLevelValueValuesEnum(log_level_enum))
    self._ExpectCreate(device)

    results = self.Run('iot devices create my-device '
                       '    --registry my-registry'
                       '    --region us-central1'
                       '    --log-level {}'.format(log_level))

    self.assertEqual(results, device)
    self.AssertLogContains('Created device [my-device].')

  def testCreate_WithInvalidLogLevel(self):
    with self.AssertRaisesArgumentErrorMatches(
        "argument --log-level: Invalid choice: 'just-whenever-dude'"):
      self.Run('iot devices create my-device '
               '    --registry my-registry'
               '    --region us-central1'
               '    --log-level just-whenever-dude')

  @parameterized.parameters('gateway', 'non-gateway')
  def testCreate_WithGatewayType(self, gateway_type):
    gateway_enum = flags.CREATE_GATEWAY_ENUM_MAPPER.GetEnumForChoice(
        gateway_type)
    device = self.messages.Device(
        id='my-device',
        blocked=False,
        gatewayConfig=self.messages.GatewayConfig(gatewayType=gateway_enum)
    )
    self._ExpectCreate(device)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run(
        'iot devices create {} --device-type {}'.format(device_name,
                                                        gateway_type))

    self.assertEqual(results, device)

  @parameterized.parameters('association-only', 'device-auth-token-only',
                            'association-and-device-auth-token')
  def testCreate_WithAuthMethod(self, auth_method):
    gateway_enum = (
        self.messages.GatewayConfig.GatewayTypeValueValuesEnum.GATEWAY)
    auth_method_enum = (
        self.messages.GatewayConfig.GatewayAuthMethodValueValuesEnum
        .lookup_by_name(auth_method.upper().replace('-', '_')))

    device = self.messages.Device(
        id='my-device',
        blocked=False,
        gatewayConfig=self.messages.GatewayConfig(
            gatewayType=gateway_enum, gatewayAuthMethod=auth_method_enum))
    self._ExpectCreate(device)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run('iot devices create {} --device-type gateway '
                       '--auth-method {}'.format(device_name, auth_method))

    self.assertEqual(results, device)

  def testCreate_WithAuthTypeAndNoGatewayTypeFails(self):
    with self.AssertRaisesExceptionMatches(command_util.InvalidAuthMethodError,
                                           'auth_method can only be set on '
                                           'gateway devices.'):
      self.Run('iot devices create my-device'
               ' --registry my-registry'
               ' --region us-central1 --device-type non-gateway'
               ' --auth-method association-only')

    with self.AssertRaisesExceptionMatches(command_util.InvalidAuthMethodError,
                                           'auth_method can only be set on '
                                           'gateway devices.'):
      self.Run('iot devices create my-device'
               ' --registry my-registry'
               ' --region us-central1 --auth-method association-only')


class DevicesCreateTestAlpha(DevicesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
