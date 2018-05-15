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
"""Tests for the instances add-iam-policy-binding subcommand."""


import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'alpha')


class AddIamPolicyBindingTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testAddOwnerToInstance(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.EmptyAlphaIamPolicy()]),
        iter([test_resources.AlphaIamPolicyWithOneBinding()]),
    ])

    self.Run("""
        compute instances add-iam-policy-binding resource --zone zone-1
        --member user:testuser@google.com --role owner
        """)
    policy = test_resources.AlphaIamPolicyWithOneBinding()
    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          messages.ComputeInstancesGetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1')),],
        [(self.compute.instances,
          'SetIamPolicy',
          messages.ComputeInstancesSetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1',
              zoneSetPolicyRequest=messages.ZoneSetPolicyRequest(
                  bindings=policy.bindings,
                  etag=policy.etag))),
        ]
    )

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: dGVzdA==
            """))


if __name__ == '__main__':
  test_case.main()
