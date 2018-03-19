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

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class AddIamPolicyBindingTest(base.SpannerTestBase):

  def SetUp(self):
    self.role_to_remove = 'roles/spanner.databaseAdmin'
    self.user_to_remove = 'user:jgreet@google.com'

    self.instance_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.start_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com', self.user_to_remove]),
            self.msgs.Binding(
                role=u'roles/spanner.viewer', members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)

  def testAddIamPolicyBinding(self):
    """Test the standard use case."""
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=self.start_policy)

    set_request = self.msgs.SetIamPolicyRequest(policy=self.new_policy)
    self.client.projects_instances.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesSetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.new_policy)

    remove_binding_request = self.Run("""
        spanner instances remove-iam-policy-binding insId
        --role={0} --member={1}
        """.format(self.role_to_remove, self.user_to_remove))
    self.assertEqual(remove_binding_request, self.new_policy)
