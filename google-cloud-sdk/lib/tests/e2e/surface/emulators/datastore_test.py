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
"""Integration tests for the emulators datastore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


def IsGCDComponentInstalled():
  try:
    util.EnsureComponentIsInstalled('gcd-emulator',
                                    datastore_util.DATASTORE_TITLE)
  except:  # pylint:disable=bare-except
    return False
  return True


def IsCloudDatastoreEmulatorComponentInstalled():
  try:
    util.EnsureComponentIsInstalled('cloud-datastore-emulator',
                                    datastore_util.DATASTORE_TITLE)
  except:  # pylint:disable=bare-except
    return False
  return True


@test_case.Filters.SkipOnWindows('Failing on Windows', 'b/36216325')
class DatastoreTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  def SetUp(self):
    # Verify that Java is installed or skip these tests
    with self.SkipTestIfRaises(java.JavaError):
      java.RequireJavaInstalled('test')

  def Project(self):
    return 'fake-project'

  @test_case.Filters.RunOnlyIf(IsGCDComponentInstalled(),
                               'Need GCD')
  def testStartLegacyEmulatorAndPrintEnv(self):
    self.doTestStartEmulatorAndPrintEnv(True)

  @test_case.Filters.RunOnlyIf(IsCloudDatastoreEmulatorComponentInstalled(),
                               'Need Cloud Datastore Emulator')
  def testStartDefaultEmulatorAndPrintEnv(self):
    self.doTestStartEmulatorAndPrintEnv(None)

  @test_case.Filters.RunOnlyIf(IsCloudDatastoreEmulatorComponentInstalled(),
                               'Need Cloud Datastore Emulator')
  def testLegacyEmulatorAndPrintEnv(self):
    self.doTestStartEmulatorAndPrintEnv(False)

  def doTestStartEmulatorAndPrintEnv(self, legacy):
    port = self.GetPort()
    args = ['beta', 'emulators', 'datastore', 'start',
            '--host-port=localhost:' + port,]
    if legacy:
      args.append('--legacy')
    elif legacy is not None:
      args.append('--no-legacy')

    # The default should have the same characteristics as no-legacy.
    if legacy:
      match_text = '[datastore] INFO: Dev App Server is now running'
    else:
      match_text = 'Dev App Server is now running.'

    with self.ExecuteScriptAsync(
        'gcloud',
        args,
        match_strings=[match_text],
        timeout=60):

      data = encoding.Decode(
          six.moves.urllib.request.urlopen('http://localhost:' + port).read(),
          'utf-8')
      if legacy:
        self.assertTrue('Cloud Datastore service' in data,
                        'Datastore was not started')
      else:
        self.assertTrue('Ok' in data,
                        'Datastore was not started')

    self.Run('beta emulators datastore env-init')
    self.AssertOutputContains('DATASTORE_HOST=http://localhost:' + port)
    self.AssertOutputContains('DATASTORE_EMULATOR_HOST=localhost:' + port)
    self.AssertOutputContains(
        'DATASTORE_EMULATOR_HOST_PATH=localhost:' + port + '/datastore')
    self.AssertOutputContains('DATASTORE_DATASET=' + self.Project())
    self.AssertOutputContains('DATASTORE_PROJECT_ID=' + self.Project())

    # Test that the environment can be properly unset.
    self.Run('beta emulators datastore env-unset')
    if self.IsOnWindows():
      self.AssertOutputContains('set DATASTORE_HOST=')
      self.AssertOutputContains('set DATASTORE_EMULATOR_HOST=')
      self.AssertOutputContains('set DATASTORE_EMULATOR_HOST_PATH=')
      self.AssertOutputContains('set DATASTORE_DATASET=')
      self.AssertOutputContains('set DATASTORE_PROJECT_ID=')
    else:
      self.AssertOutputContains('unset DATASTORE_HOST')
      self.AssertOutputContains('unset DATASTORE_EMULATOR_HOST')
      self.AssertOutputContains('unset DATASTORE_EMULATOR_HOST_PATH')
      self.AssertOutputContains('unset DATASTORE_DATASET')
      self.AssertOutputContains('unset DATASTORE_PROJECT_ID')

  @test_case.Filters.skip('Very flaky', 'b/62056917')
  @test_case.Filters.RunOnlyIf(IsCloudDatastoreEmulatorComponentInstalled(),
                               'Need Cloud Datastore Emulator')
  def testDefaultPort(self):
    args = ['beta', 'emulators', 'datastore', 'start']
    match_text = 'Dev App Server is now running.'
    with self.ExecuteScriptAsync(
        'gcloud',
        args,
        match_strings=[match_text],
        timeout=120):
      self.Run('beta emulators datastore env-init')
      self.AssertOutputContains('DATASTORE_EMULATOR_HOST=localhost:8081')

if __name__ == '__main__':
  test_case.main()
