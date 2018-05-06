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
"""Tests for Bigtable instances get-iam-policy command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.bigtable import util
from tests.lib.surface.bigtable import base


class GetIamPolicyTest(base.BigtableV2TestBase):

  def SetUp(self):
    self.instance_ref = util.GetInstanceRef('my-instance')

  def testGetIamPolicy(self):
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/bigtable.admin', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/bigtable.viewer', members=['user:admin@foo.com'])
        ],
        etag='someUniqueEtag'.encode(),
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.BigtableadminProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=test_iam_policy)
    get_policy_request = self.Run(
        'bigtable instances get-iam-policy my-instance')
    self.assertEqual(get_policy_request, test_iam_policy)

  def testListCommandFilter(self):
    """Ensure get-iam-policy properly applies list command filters."""
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/bigtable.admin', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/bigtable.viewer', members=['user:admin@foo.com'])
        ],
        etag='someUniqueEtag'.encode(),
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.BigtableadminProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=test_iam_policy)
    self.Run("""
        bigtable instances get-iam-policy my-instance
        --flatten=bindings[].members
        --filter=bindings.role:roles/bigtable.viewer
        --format=table[no-heading](bindings.members:sort=1)
        """)
    self.AssertOutputEquals('user:admin@foo.com\n')
