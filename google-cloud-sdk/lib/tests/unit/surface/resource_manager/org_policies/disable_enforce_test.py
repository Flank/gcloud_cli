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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OrgPoliciesDisableEnforceTest(testbase.OrgPoliciesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDisableEnforceOrgPolicy(self):
    test_policy = self.TestPolicy()
    test_policy.booleanPolicy.enforced = False

    self.mock_projects.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.PROJECT_ARG, test_policy), test_policy)
    self.mock_organizations.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.ORG_ARG, test_policy), test_policy)
    self.mock_folders.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.FOLDER_ARG, test_policy), test_policy)
    self.assertEqual(self.DoRequest(self.PROJECT_ARG), test_policy)
    self.assertEqual(self.DoRequest(self.ORG_ARG), test_policy)
    self.assertEqual(self.DoRequest(self.FOLDER_ARG), test_policy)

  def DoRequest(self, args):
    return self.RunOrgPolicies('disable-enforce', self.TEST_CONSTRAINT, *args)


class OrgPoliciesDisableEnforceAlphaTest(OrgPoliciesDisableEnforceTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class OrgPoliciesDisableEnforceBetaTest(OrgPoliciesDisableEnforceTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

if __name__ == '__main__':
  test_case.main()
