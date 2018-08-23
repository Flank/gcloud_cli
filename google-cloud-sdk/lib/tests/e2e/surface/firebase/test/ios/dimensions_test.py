# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.firebase.test import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import e2e_base
from tests.lib.surface.firebase.test.ios import commands

IOS_XCTEST = os.path.join(e2e_base.E2E_TEST_DATA_PATH, 'ios-app.zip')


class IosDeviceDimensionsIntegrationTests(e2e_base.TestIntegrationTestBase):
  """Integration tests for device dimensions in gcloud firebase test ios run."""

  def testArgConflicts_BadDimensionNameInArgFile(self):
    with self.assertRaises(exceptions.InvalidDimensionNameError):
      self.Run('{cmd} {argfile}:ios-bad-dimension '.format(
          cmd=commands.IOS_TEST_RUN, argfile=e2e_base.INTEGRATION_ARGS))

    self.AssertErrContains("'brand' is not a valid dimension name.")

  def testArgConflicts_BadDimensionNameInFlag(self):
    with self.assertRaises(exceptions.InvalidDimensionNameError):
      self.Run(
          '{cmd} --test {zip} --device model=iphone8 --device codename=secret'
          .format(cmd=commands.IOS_TEST_RUN, zip=IOS_XCTEST))

    self.AssertErrContains("'codename' is not a valid dimension name.")

  def testArgConflicts_NoDeviceDimensionsGiven(self):
    with self.assertRaises(Exception):
      self.Run('{cmd} --test {zip} --device '.format(
          cmd=commands.IOS_TEST_RUN, zip=IOS_XCTEST))

    self.AssertErrContains('--device: expected one argument')


if __name__ == '__main__':
  test_case.main()
