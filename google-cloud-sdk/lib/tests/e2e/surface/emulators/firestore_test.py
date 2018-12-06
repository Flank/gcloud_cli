# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for the emulators firestore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.emulators import firestore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


def IsCloudFirestoreEmulatorComponentInstalled():
  try:
    util.EnsureComponentIsInstalled('cloud-firestore-emulator',
                                    firestore_util.FIRESTORE_TITLE)
  except:  # pylint:disable=bare-except
    return False
  return True


@test_case.Filters.SkipOnWindows('Failing on Windows', 'b/117842934')
class FirestoreTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  def SetUp(self):
    # Verify that Java is installed or skip these tests
    with self.SkipTestIfRaises(java.JavaError):
      java.RequireJavaInstalled('test')

  @test_case.Filters.RunOnlyIf(IsCloudFirestoreEmulatorComponentInstalled(),
                               'Need Cloud Firestore Emulator')
  def testStartDefaultEmulatorAlpha(self):
    self.doTestStartDefaultEmulator('alpha')

  @test_case.Filters.RunOnlyIf(IsCloudFirestoreEmulatorComponentInstalled(),
                               'Need Cloud Firestore Emulator')
  def testStartDefaultEmulatorBeta(self):
    self.doTestStartDefaultEmulator('beta')

  def doTestStartDefaultEmulator(self, release_cycle):
    """Asserts that the emulator starts.

    Checks that the Firestore emulator starts up correctly by waiting for it to
    print a specific string.

    Args:
      release_cycle: either "alpha" or "beta"
    """
    port = self.GetPort()
    args = [
        release_cycle,
        'emulators',
        'firestore',
        'start',
        '--host-port=localhost:' + port,
    ]

    with self.ExecuteScriptAsync(
        'gcloud', args, match_strings=['API endpoint:'], timeout=60):

      data = encoding.Decode(
          six.moves.urllib.request.urlopen('http://localhost:' + port).read(),
          'utf-8')
      self.assertTrue('Ok' in data, 'Firestore emulator did not start')


if __name__ == '__main__':
  test_case.main()
