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
"""Generate tests for the get-iam-policy subcommand."""
import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class GetIamPolicyTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.messages = core_apis.GetMessagesModule('compute', api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', api_version),
        real_client=core_apis.GetClientInstance('compute', api_version,
                                                no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testSimpleEmptyResponseCase(self):
    self.mock_client.subnetworks.GetIamPolicy.Expect(
        self.messages.ComputeSubnetworksGetIamPolicyRequest(
            resource='my-resource', region='my-region', project='fake-project'),
        response=test_resources.EmptyAlphaIamPolicy())

    self.Run("""
        compute networks subnets get-iam-policy --region=my-region my-resource
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))

  def testSimpleResponseCase(self):
    self.mock_client.subnetworks.GetIamPolicy.Expect(
        self.messages.ComputeSubnetworksGetIamPolicyRequest(
            resource='my-resource', region='my-region', project='fake-project'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run("""
        compute networks subnets get-iam-policy --region=my-region my-resource
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: ZXRhZ1R3bw==
            """))

  def testListCommandFilter(self):
    self.mock_client.subnetworks.GetIamPolicy.Expect(
        self.messages.ComputeSubnetworksGetIamPolicyRequest(
            resource='my-resource', region='my-region', project='fake-project'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run("""
        compute networks subnets get-iam-policy --region=my-region my-resource
        --flatten=bindings[].members --filter=bindings.role:owner
        --format='value(bindings.members)'
        """)

    self.AssertOutputContains('user:testuser@google.com')


class GetIamPolicyBetaTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testSimpleEmptyResponseCase(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.EmptyBetaIamPolicy()]),
    ])
    self.Run(
        'compute networks subnets get-iam-policy my-resource --region region-1')

    self.CheckRequests(
        [(self.compute.subnetworks,
          'GetIamPolicy',
          self.messages.ComputeSubnetworksGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              region='region-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))

  def testSimpleResponseCase(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.BetaIamPolicyWithOneBindingAndDifferentEtag()]),
    ])
    self.Run(
        'compute networks subnets get-iam-policy my-resource --region region-1')

    self.CheckRequests(
        [(self.compute.subnetworks,
          'GetIamPolicy',
          self.messages.ComputeSubnetworksGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              region='region-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: ZXRhZ1R3bw==
            """))

  def testListCommandFilter(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.BetaIamPolicyWithOneBindingAndDifferentEtag()]),
    ])
    self.Run("""
        compute networks subnets get-iam-policy my-resource --region region-1
        --flatten=bindings[].members --filter=bindings.role:owner
        --format='value(bindings.members)'
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'GetIamPolicy',
          self.messages.ComputeSubnetworksGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              region='region-1'))],
    )
    self.AssertOutputContains('user:testuser@google.com')

  def testNotFound(self):
    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test
        yield
      kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute networks subnets get-iam-policy my-resource --region region-1
          """)


class GetIamPolicyGaTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testNotInGA(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'Invalid choice:'):
      self.Run("""
          compute networks subnets get-iam-policy my-resource
          """)

if __name__ == '__main__':
  test_case.main()
