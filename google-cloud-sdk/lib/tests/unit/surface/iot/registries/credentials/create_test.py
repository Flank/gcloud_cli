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
"""Tests for `gcloud iot registries credentials create`."""
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CredentialsCreateTest(base.CloudIotRegistryBase):

  def testCreate_InvalidPath(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(util.InvalidKeyFileError,
                                           'Could not read key file'):
      self.Run(
          'iot registries credentials create '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --path {} '.format(os.path.join(self.temp_path, 'bad.pub')))

  def testCreate_MissingPath(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        'argument --path: Must be specified.'):
      self.Run(
          'iot registries credentials create '
          '    --registry my-registry '
          '    --region us-central1 ')

  def testCreate_Empty(self, track):
    self.track = track
    new_credential = self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS)
    self._ExpectGet([])
    self._ExpectPatch([new_credential])

    results = self.Run(
        'iot registries credentials create '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --path {}'.format(self.certificate_key))

    expected_registry = self.messages.DeviceRegistry(
        id='my-registry', credentials=[new_credential])
    self.assertEqual(results, expected_registry)
    self.AssertLogContains('Created credentials for registry [my-registry].')

  def testCreate_CredentialExists(self, track):
    self.track = track
    old_credential = self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS)
    new_credential = self._CreateRegistryCredential(
        self.OTHER_CERTIFICATE_CONTENTS)
    new_credential_path = self.Touch(
        self.temp_path,
        'certificate2.pub',
        contents=self.OTHER_CERTIFICATE_CONTENTS)

    self._ExpectGet([old_credential])
    self._ExpectPatch([old_credential, new_credential])

    results = self.Run(
        'iot registries credentials create '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --path {}'.format(new_credential_path))

    expected_registry = self.messages.DeviceRegistry(
        id='my-registry', credentials=[old_credential, new_credential])
    self.assertEqual(results, expected_registry)

  def testCreate_RelativeName(self, track):
    self.track = track
    new_credential = self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS)
    self._ExpectGet([])
    self._ExpectPatch([new_credential])

    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    results = self.Run(
        'iot registries credentials create '
        '    --registry {}'
        '    --path {}'.format(registry_name, self.certificate_key))

    expected_registry = self.messages.DeviceRegistry(
        id='my-registry', credentials=[new_credential])
    self.assertEqual(results, expected_registry)


if __name__ == '__main__':
  test_case.main()

