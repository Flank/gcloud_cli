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
"""Tests for spanner add-iam-policy-binding."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class AddIamPolicyBindingTest(base.SpannerTestBase):

  def SetUp(self):
    self.new_role = 'roles/spanner.databaseAdmin'
    self.new_user = 'user:foo@google.com'

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
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com', self.new_user]), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
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

    add_binding_request = self.Run("""
        spanner databases add-iam-policy-binding dbId --instance=insId --role={0} --member={1}
        """.format(self.new_role, self.new_user))
    self.assertEqual(add_binding_request, self.new_policy)

  def testAddIamPolicyBindingWithDefaultInstance(self):
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

    self.Run('config set spanner/instance insId')
    add_binding_request = self.Run("""
        spanner databases add-iam-policy-binding dbId --role={0} --member={1}
        """.format(self.new_role, self.new_user))
    self.assertEqual(add_binding_request, self.new_policy)
