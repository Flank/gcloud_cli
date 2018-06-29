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
"""Tests for Spanner remove-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class AddIamPolicyBindingTest(base.SpannerTestBase):

  def SetUp(self):
    self.role_to_remove = 'roles/spanner.databaseAdmin'
    self.user_to_remove = 'user:jgreet@google.com'

    self.database_ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.databases')
    self.start_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com', self.user_to_remove]),
            self.msgs.Binding(
                role='roles/spanner.viewer', members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com']), self.msgs.Binding(
                    role='roles/spanner.viewer',
                    members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

  def testAddIamPolicyBinding(self):
    """Test the standard use case."""
    self.client.projects_instances_databases.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
            resource=self.database_ref.RelativeName()),
        response=self.start_policy)

    set_request = self.msgs.SetIamPolicyRequest(policy=self.new_policy)
    self.client.projects_instances_databases.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
            resource=self.database_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.new_policy)

    remove_binding_request = self.Run(
        'spanner databases remove-iam-policy-binding dbId --role={0} '
        '--member={1} --instance=insId'.format(self.role_to_remove,
                                               self.user_to_remove))
    self.assertEqual(remove_binding_request, self.new_policy)

  def testAddIamPolicyBindingWithDefaultInstance(self):
    self.client.projects_instances_databases.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
            resource=self.database_ref.RelativeName()),
        response=self.start_policy)

    set_request = self.msgs.SetIamPolicyRequest(policy=self.new_policy)
    self.client.projects_instances_databases.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
            resource=self.database_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.new_policy)

    self.Run('config set spanner/instance insId')
    remove_binding_request = self.Run(
        'spanner databases remove-iam-policy-binding dbId --role={0} '
        '--member={1}'.format(self.role_to_remove, self.user_to_remove))
    self.assertEqual(remove_binding_request, self.new_policy)
