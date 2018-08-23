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

"""Tests for `gcloud iot registries credentials delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CredentialsDeleteTest(base.CloudIotRegistryBase):

  def SetUp(self):
    self.registry_credentials = [
        self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS),
        self._CreateRegistryCredential(self.OTHER_CERTIFICATE_CONTENTS)
    ]

  def testDelete(self, track):
    self.track = track
    self.WriteInput('y')
    self._ExpectGet(self.registry_credentials)
    self._ExpectPatch(self.registry_credentials[1:])

    results = self.Run(
        'iot registries credentials delete 0'
        '    --format disable '
        '    --registry my-registry '
        '    --region us-central1')

    expected_registry = self.messages.DeviceRegistry(
        id='my-registry', credentials=self.registry_credentials[1:])
    self.assertEqual(results, expected_registry)
    self.AssertErrContains('This will delete the following credential:')
    self.AssertErrContains(self.CERTIFICATE_CONTENTS.replace('\n', r'\\n'))
    self.AssertLogContains('Deleted credential at index [0] for registry '
                           '[my-registry].')

  def testDelete_BadIndex(self, track):
    self.track = track
    self._ExpectGet(self.registry_credentials)

    with self.AssertRaisesExceptionMatches(
        util.BadCredentialIndexError,
        'Invalid credential index [2]; registry [my-registry] has 2 '
        'credentials'):
      self.Run(
          'iot registries credentials delete 2'
          '    --format disable '
          '    --registry my-registry '
          '    --region us-central1')

  def testDelete_Cancel(self, track):
    self.track = track
    self.WriteInput('n')
    credential = self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS)
    self._ExpectGet([credential])

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          'iot registries credentials delete 0'
          '    --format disable '
          '    --registry my-registry '
          '    --region us-central1')
    self.AssertErrContains('This will delete the following credential:')

  def testDelete_RelativeName(self, track):
    self.track = track
    self.WriteInput('y')
    self._ExpectGet(self.registry_credentials)
    self._ExpectPatch(self.registry_credentials[1:])

    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    results = self.Run(
        'iot registries credentials delete 0'
        '    --format disable '
        '    --registry {}'.format(registry_name))

    expected_registry = self.messages.DeviceRegistry(
        id='my-registry', credentials=self.registry_credentials[1:])
    self.assertEqual(results, expected_registry)
    self.AssertErrContains('This will delete the following credential:')
    self.AssertErrContains(self.CERTIFICATE_CONTENTS.replace('\n', r'\\n'))


if __name__ == '__main__':
  test_case.main()
