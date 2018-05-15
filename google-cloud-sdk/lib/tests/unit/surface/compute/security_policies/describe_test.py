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
"""Tests for the security policies describe subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class SecurityPoliciesDescribeTestAlpha(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def testSimpleCase(self):
    my_policy = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')
    self.make_requests.side_effect = iter([
        [test_resources.MakeSecurityPolicy(self.messages, my_policy)],
    ])
    self.Run("""
        compute security-policies describe my-policy
        """)

    self.CheckRequests(
        [(self.compute.securityPolicies, 'Get',
          self.messages.ComputeSecurityPoliciesGetRequest(
              project='my-project', securityPolicy='my-policy'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            description: my description
            fingerprint: PWfLGDWQDLY=
            id: \'123\'
            name: my-policy
            rules:
            - action: allow
              description: default rule
              match:
                config:
                  srcIpRanges:
                  - \'*\'
                versionedExpr: SRC_IPS_V1
              preview: false
              priority: 2147483647
            selfLink: {self_link}
            """.format(self_link=my_policy.SelfLink())))


class SecurityPoliciesDescribeTestBeta(SecurityPoliciesDescribeTestAlpha):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')


if __name__ == '__main__':
  test_case.main()
