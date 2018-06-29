# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
"""compute snapshots get-iam-policy tests."""

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.compute import test_resources


class GetIamPolicyUnitTest(sdk_test_base.WithFakeAuth,
                           cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('compute', 'alpha')
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', 'alpha'),
        real_client=apis.GetClientInstance('compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.track = base.ReleaseTrack.ALPHA

  def testEmptyPolicyCase(self):
    self.mock_client.snapshots.GetIamPolicy.Expect(
        self.messages.ComputeSnapshotsGetIamPolicyRequest(
            resource='my-resource', project='fake-project'),
        response=test_resources.EmptyAlphaIamPolicy())

    self.Run('compute snapshots get-iam-policy my-resource')
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))

  def testSimpleResponseCase(self):
    self.mock_client.snapshots.GetIamPolicy.Expect(
        self.messages.ComputeSnapshotsGetIamPolicyRequest(
            resource='my-resource', project='fake-project'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run('compute snapshots get-iam-policy my-resource')
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
    self.mock_client.snapshots.GetIamPolicy.Expect(
        self.messages.ComputeDisksGetIamPolicyRequest(
            resource='my-resource', project='fake-project'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run("""
        compute snapshots get-iam-policy my-resource
        --flatten=bindings[].members --filter=bindings.role:owner
        --format='value(bindings.members)'
        """)

    self.AssertOutputContains('user:testuser@google.com')

  def testGetIamPolicySnapshotRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument SNAPSHOT_NAME: Must be specified.'):
      self.Run('compute snapshots get-iam-policy')
