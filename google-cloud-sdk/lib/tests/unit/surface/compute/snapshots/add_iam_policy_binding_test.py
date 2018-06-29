# Copyright 2018 Google Inc. All Rights Reserved.
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
"""compute snapshots add-iam-policy-binding tests."""

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


class AddIamPolicyBindingTest(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('compute', 'alpha')
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', 'alpha'),
        real_client=apis.GetClientInstance('compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.track = base.ReleaseTrack.ALPHA

  def testAddOwnerToSnapshot(self):
    self.mock_client.snapshots.GetIamPolicy.Expect(
        self.messages.ComputeDisksGetIamPolicyRequest(
            resource='my-resource', project='fake-project'),
        response=test_resources.EmptyAlphaIamPolicy())
    policy = test_resources.AlphaIamPolicyWithOneBinding()
    self.mock_client.snapshots.SetIamPolicy.Expect(
        self.messages.ComputeSnapshotsSetIamPolicyRequest(
            resource='my-resource',
            project='fake-project',
            globalSetPolicyRequest=self.messages.GlobalSetPolicyRequest(
                bindings=policy.bindings, etag=policy.etag)),
        response=test_resources.AlphaIamPolicyWithOneBinding())

    self.Run("""
        compute snapshots add-iam-policy-binding my-resource
        --member user:testuser@google.com --role owner
        """)

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
