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

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'alpha')


class GetIamPolicyTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testSimpleEmptyResponseCase(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.EmptyAlphaIamPolicy()]),
    ])
    self.Run("""
        compute instances get-iam-policy my-resource --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          messages.ComputeInstancesGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))

  def testSimpleResponseCase(self):
    self.make_requests.side_effect = iter([
        iter([test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag()]),
    ])
    self.Run("""
        compute instances get-iam-policy my-resource --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          messages.ComputeInstancesGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              zone='zone-1'))],
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
        iter([test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag()]),
    ])
    self.Run("""
        compute instances get-iam-policy my-resource --zone zone-1
        --flatten=bindings[].members --filter=bindings.role:owner
        --format='value(bindings.members)'
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'GetIamPolicy',
          messages.ComputeInstancesGetIamPolicyRequest(
              resource='my-resource',
              project='my-project',
              zone='zone-1'))],
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
          compute instances get-iam-policy my-resource --zone zone-1
          """)


class GetIamPolicyTestBeta(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testNotInGA(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'Invalid choice:'):
      self.Run("""
          compute instances get-iam-policy my-resource
          """)


class GetIamPolicyTestGa(test_base.BaseTest, test_case.WithOutputCapture):

  def testNotInBeta(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'Invalid choice: \'get-iam-policy\''):
      self.Run("""
          beta compute instances get-iam-policy my-resource
          """)


if __name__ == '__main__':
  test_case.main()
