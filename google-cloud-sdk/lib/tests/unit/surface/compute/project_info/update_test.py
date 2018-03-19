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
"""Tests for the project-info update command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class ProjectInfoUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testSetDefaultNetworkTier_noParameterSpecified(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --default-network-tier: expected one argument'):
      self.Run("""
          compute project-info update --default-network-tier
          """)

  def testSetDefaultNetworkTier_updateToPremiumNetworkTier(self):
    self.Run("""
        compute project-info update --default-network-tier PREMIUM
        """)

    self.CheckRequests([
        (self.compute_alpha.projects, 'SetDefaultNetworkTier',
         self.messages.ComputeProjectsSetDefaultNetworkTierRequest(
             project='my-project',
             projectsSetDefaultNetworkTierRequest=self.
             messages.ProjectsSetDefaultNetworkTierRequest(
                 networkTier=self.messages.ProjectsSetDefaultNetworkTierRequest.
                 NetworkTierValueValuesEnum.PREMIUM)))
    ],)

  def testSetDefaultNetworkTier_updateToStandardNetworkTier(self):
    self.Run("""
        compute project-info update --default-network-tier standard
        """)

    self.CheckRequests([
        (self.compute_alpha.projects, 'SetDefaultNetworkTier',
         self.messages.ComputeProjectsSetDefaultNetworkTierRequest(
             project='my-project',
             projectsSetDefaultNetworkTierRequest=self.
             messages.ProjectsSetDefaultNetworkTierRequest(
                 networkTier=self.messages.ProjectsSetDefaultNetworkTierRequest.
                 NetworkTierValueValuesEnum.STANDARD)))
    ],)

  def testSetDefaultNetworkTier_updateToInvalidNetworkTier(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --default-network-tier: Invalid choice: \'SELECT\''):
      self.Run("""
          compute project-info update --default-network-tier SELECT
          """)

    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --default-network-tier: Invalid choice: \'INVALID-TIER\''):
      self.Run("""
          compute project-info update --default-network-tier invalid-tier
          """)


if __name__ == '__main__':
  test_case.main()
