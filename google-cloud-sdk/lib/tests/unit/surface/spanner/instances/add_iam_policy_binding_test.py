# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib.surface.spanner import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class AddIamPolicyBindingTest(base.SpannerTestBase):

  def SetUp(self):
    self.new_role = 'roles/spanner.databaseAdmin'
    self.new_user = 'user:foo@google.com'

    self.instance_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.start_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com']), self.msgs.Binding(
                    role='roles/spanner.viewer',
                    members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com', self.new_user]), self.msgs.Binding(
                    role='roles/spanner.viewer',
                    members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

  def testAddIamPolicyBinding(self, track):
    """Test the standard use case."""
    self.track = track
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

    add_binding_request = self.Run("""
        spanner instances add-iam-policy-binding insId --role={0} --member={1}
        """.format(self.new_role, self.new_user))
    self.assertEqual(add_binding_request, self.new_policy)
