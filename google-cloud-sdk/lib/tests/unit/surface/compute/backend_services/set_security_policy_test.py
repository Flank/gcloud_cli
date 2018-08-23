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

"""Tests for the backend services set-security-policy subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class BackendServicesSetSecurityPolicyTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    messages = self.messages

    self.Run("""
        compute backend-services set-security-policy my-backend-service
          --security-policy my-policy
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='my-backend-service',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/global/securityPolicies/my-policy')))],
    )

    self.AssertErrContains('WARNING: This command is deprecated and will not '
                           'be promoted to beta. Please use '
                           '"gcloud beta backend-services update" instead.')

  def testClearPolicy(self):
    messages = self.messages

    self.Run("""
        compute backend-services set-security-policy my-backend-service
          --security-policy ''
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='my-backend-service',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy=None)))],
    )

  def testUriSupport(self):
    messages = self.messages

    self.Run("""
        compute backend-services set-security-policy my-backend-service
          --security-policy https://www.googleapis.com/compute/alpha/projects/my-project/global/securityPolicies/my-policy
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='my-backend-service',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/global/securityPolicies/my-policy')))],
    )


if __name__ == '__main__':
  test_case.main()
