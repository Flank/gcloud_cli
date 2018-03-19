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

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import commands
from tests.lib.surface.firebase.test import e2e_base


class ArgDimensionConflictsIntegrationTests(e2e_base.TestIntegrationTestBase):
  """Integration tests for matrix dimension args in gcloud firebase test run."""

  def testArgConflicts_DeviceIdsWithDevice(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run(
          u'{cmd} --app {app} --device-ids=Nexus7 --device model=NexusLowRes'
          .format(cmd=commands.ANDROID_TEST_RUN, app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains('not allowed simultaneously: --device-ids, --device')

  def testArgConflicts_OsVersionIdsWithDevice(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run(
          u'{cmd} {argfile}:arg-conflict-1 --app {app} '
          .format(cmd=commands.ANDROID_TEST_RUN,
                  argfile=e2e_base.INTEGRATION_ARGS,
                  app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains('allowed simultaneously: --os-version-ids, --device')

  def testArgConflicts_LocalesWithDevice(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run(
          u'{cmd} {argfile}:arg-conflict-2 --app {app} '
          .format(cmd=commands.ANDROID_TEST_RUN,
                  argfile=e2e_base.INTEGRATION_ARGS,
                  app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains('allowed simultaneously: --locales, --device')

  @test_case.Filters.skip('Failing', 'b/73120615')
  def testArgConflicts_OrientationsWithDevice(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run(
          u'{cmd} {argfile}:arg-conflict-3 --app {app} '
          .format(cmd=commands.ANDROID_TEST_RUN,
                  argfile=e2e_base.INTEGRATION_ARGS,
                  app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains('allowed simultaneously: --orientations, --device')

  @test_case.Filters.skip('Failing', 'b/73120615')
  def testArgConflicts_BadDimensionNameInArgFile(self):
    with self.assertRaises(exceptions.InvalidDimensionNameError):
      self.Run(
          u'{cmd} {argfile}:bad-dimension '
          .format(cmd=commands.ANDROID_TEST_RUN,
                  argfile=e2e_base.INTEGRATION_ARGS))

    self.AssertErrContains("'brand' is not a valid dimension name.")

  @test_case.Filters.skip('Failing', 'b/73120615')
  def testArgConflicts_BadDimensionNameInFlag(self):
    with self.assertRaises(exceptions.InvalidDimensionNameError):
      self.Run(
          '{cmd} --app {app} --device model=sailfish --device codename=secret'
          .format(cmd=commands.ANDROID_TEST_RUN, app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains("'codename' is not a valid dimension name.")

  def testArgConflicts_NoDeviceDimensionsGiven(self):
    with self.assertRaises(Exception):
      self.Run(
          '{cmd} --app {app} --device '
          .format(cmd=commands.ANDROID_TEST_RUN, app=e2e_base.WALKSHARE_APP))

    self.AssertErrContains('--device: expected one argument')


if __name__ == '__main__':
  test_case.main()
