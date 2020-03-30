# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the security policy update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UpdateTestAlpha(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def ExpectedSecurityPolicyRequest(self, **kwargs):
    self.make_requests.side_effect = iter([[
        self.messages.SecurityPolicy(
            description='old-description', fingerprint=b'aBSd123')
    ], []])

  def CheckSecurityPolicyRequest(self, security_policy):
    self.CheckRequests(
        [(self.compute.securityPolicies, 'Get',
          self.messages.ComputeSecurityPoliciesGetRequest(
              project='my-project',
              securityPolicy='my-policy'))],
        [(self.compute.securityPolicies, 'Patch',
          self.messages.ComputeSecurityPoliciesPatchRequest(
              project='my-project',
              securityPolicy='my-policy',
              securityPolicyResource=security_policy))])

  def testUpdateSecurityPolicy(self):
    self.ExpectedSecurityPolicyRequest()

    self.Run('compute security-policies update my-policy '
             '--description new-description --enable-ml')
    security_policy = self.messages.SecurityPolicy(
        description='new-description',
        cloudArmorConfig=self.messages.SecurityPolicyCloudArmorConfig(
            enableMl=True),
        fingerprint=b'aBSd123')

    self.CheckSecurityPolicyRequest(security_policy)

  def testUpdateSecurityPolicyNoArgs(self):
    self.ExpectedSecurityPolicyRequest()

    with self.AssertRaisesExceptionRegexp(
        exceptions.MinimumArgumentException,
        'Please specify at least one property to update'):
      self.Run('compute security-policies update my-policy')


if __name__ == '__main__':
  test_case.main()
