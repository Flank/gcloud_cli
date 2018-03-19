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
"""Tests for the security policies delete subcommand."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SecurityPoliciesDeleteTestAlpha(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testWithSingleSecurityPolicy(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute security-policies delete my-policy
        """)

    self.CheckRequests(
        [(self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy'))],
    )

  def testWithManySecurityPolicies(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute security-policies delete my-policy my-policy2 my-policy3
        """)

    self.CheckRequests(
        [(self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy')),

         (self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy2')),

         (self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy3'))],
    )

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute security-policies delete my-policy1 my-policy2 my-policy3
        """)

    self.CheckRequests(
        [(self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy1')),

         (self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy2')),

         (self.compute.securityPolicies,
          'Delete',
          messages.ComputeSecurityPoliciesDeleteRequest(
              project='my-project',
              securityPolicy='my-policy3'))],
    )
    self.AssertErrContains(textwrap.dedent("""\
        The following security policies will be deleted:
         - [my-policy1]
         - [my-policy2]
         - [my-policy3]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute security-policies delete my-policy my-policy2 my-policy3
          """)

    self.CheckRequests()


class SecurityPoliciesDeleteTestBeta(SecurityPoliciesDeleteTestAlpha):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)


if __name__ == '__main__':
  test_case.main()
