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

"""Tests for `gcloud iot devices credentials clear`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CredentialsClearTest(base.CloudIotBase):

  def testClear(self, track):
    self.track = track
    self.WriteInput('y')
    self._ExpectPatch([])

    results = self.Run(
        'iot devices credentials clear '
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(
        results, self.messages.Device(id='my-device', credentials=[]))
    self.AssertErrContains(
        'This will delete ALL CREDENTIALS for device [my-device]')
    self.AssertLogContains('Cleared all credentials for device [my-device].')

  def testClear_Cancel(self, track):
    self.track = track
    self.WriteInput('n')

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iot devices credentials clear '
               '    --device my-device '
               '    --registry my-registry '
               '    --region us-central1')

    self.AssertErrContains(
        'This will delete ALL CREDENTIALS for device [my-device]')

  def testClear_RelativeName(self, track):
    self.track = track
    self.WriteInput('y')
    self._ExpectPatch([])

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run(
        'iot devices credentials clear '
        '    --format disable '
        '    --device {}'.format(device_name))

    self.assertEqual(
        results, self.messages.Device(id='my-device', credentials=[]))
    self.AssertErrContains(
        'This will delete ALL CREDENTIALS for device [my-device]')


if __name__ == '__main__':
  test_case.main()
