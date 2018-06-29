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
"""Unit tests for the `gcloud compute disks get-iam-policy`."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


messages = core_apis.GetMessagesModule('compute', 'alpha')


class GetIamPolicyTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', 'alpha'),
        real_client=core_apis.GetClientInstance('compute', 'alpha',
                                                no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.track = base.ReleaseTrack.ALPHA

  def testSimpleEmptyResponseCase(self):
    self.mock_client.disks.GetIamPolicy.Expect(
        messages.ComputeDisksGetIamPolicyRequest(
            resource='my-resource', project='fake-project', zone='zone-1'),
        response=test_resources.EmptyAlphaIamPolicy())

    self.Run("""
        compute disks get-iam-policy my-resource --zone zone-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            etag: dGVzdA==
            """))

  def testSimpleResponseCase(self):
    self.mock_client.disks.GetIamPolicy.Expect(
        messages.ComputeDisksGetIamPolicyRequest(resource='my-resource',
                                                 project='fake-project',
                                                 zone='zone-1'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run("""
        compute disks get-iam-policy my-resource --zone zone-1
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
    self.mock_client.disks.GetIamPolicy.Expect(
        messages.ComputeDisksGetIamPolicyRequest(resource='my-resource',
                                                 project='fake-project',
                                                 zone='zone-1'),
        response=test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag())

    self.Run("""
        compute disks get-iam-policy my-resource --zone zone-1
        --flatten=bindings[].members --filter=bindings.role:owner
        --format='value(bindings.members)'
        """)

    self.AssertOutputContains('user:testuser@google.com')


if __name__ == '__main__':
  test_case.main()
