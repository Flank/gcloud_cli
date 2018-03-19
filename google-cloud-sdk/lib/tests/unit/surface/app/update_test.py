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

"""Tests for app update command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib import test_case
from tests.lib.surface.app import app_update_base


class UpdateGaTest(app_update_base.AppUpdateBase):

  def testUpdateSplitHealthChecksTrue(self):
    self.ExpectPatchApplicationRequest(
        self.Project(),
        update_mask='featureSettings.splitHealthChecks,',
        split_health_checks=True)

    self.Run('app update --split-health-checks')
    self.AssertErrContains('Updating the app [{0}]'.format(self.Project()))

  def testUpdateSplitHealthChecksFalse(self):
    self.ExpectPatchApplicationRequest(
        self.Project(),
        update_mask='featureSettings.splitHealthChecks,',
        split_health_checks=False)

    self.Run('app update --no-split-health-checks')
    self.AssertErrContains('Updating the app [{0}]'.format(self.Project()))

  def testBaseUpdate(self):
    self.Run('app update')
    self.AssertErrContains('Nothing to update.')


class UpdateBetaTest(UpdateGaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testUpdateUseContainerOptimizedOsTrue(self):
    self.ExpectPatchApplicationRequest(
        self.Project(),
        update_mask='featureSettings.useContainerOptimizedOs,',
        use_container_optimized_os=True)

    self.Run('app update --use-container-optimized-os')
    self.AssertErrContains('Updating the app [{0}]'.format(self.Project()))

  def testUpdateUseContainerOptimizedOsFalse(self):
    self.ExpectPatchApplicationRequest(
        self.Project(),
        update_mask='featureSettings.useContainerOptimizedOs,',
        use_container_optimized_os=False)

    self.Run('app update --no-use-container-optimized-os')
    self.AssertErrContains('Updating the app [{0}]'.format(self.Project()))


class UpdateAlphaTest(UpdateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
