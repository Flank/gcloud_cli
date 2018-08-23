# -*- coding: utf-8 -*- #
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
"""compute instance templates add-iam-policy-binding tests."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


@parameterized.parameters(
    (base.ReleaseTrack.ALPHA, 'alpha'),
    (base.ReleaseTrack.BETA, 'beta'))
class AddIamPolicyBindingTest(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase,
                              parameterized.TestCase):

  def _SetUp(self, track, api_version):
    self.messages = apis.GetMessagesModule('compute', api_version)
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', api_version),
        real_client=apis.GetClientInstance(
            'compute', api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.track = track

  def testAddOwnerToInstanceTemplate(self, track, api_version):
    self._SetUp(track, api_version)
    self.mock_client.instanceTemplates.GetIamPolicy.Expect(
        self.messages.ComputeInstanceTemplatesGetIamPolicyRequest(
            resource='my-resource', project='fake-project'),
        response=test_resources.EmptyIamPolicy(self.messages))
    policy = test_resources.IamPolicyWithOneBinding(self.messages)
    self.mock_client.instanceTemplates.SetIamPolicy.Expect(
        self.messages.ComputeInstanceTemplatesSetIamPolicyRequest(
            resource='my-resource',
            project='fake-project',
            globalSetPolicyRequest=self.messages.GlobalSetPolicyRequest(
                policy=policy)),
        response=test_resources.IamPolicyWithOneBinding(self.messages))

    self.Run("""
        compute instance-templates add-iam-policy-binding my-resource
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
