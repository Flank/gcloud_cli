# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for Spanner databases get-iam-policy command."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib.surface.spanner import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class GetIamPolicyTest(base.SpannerTestBase):

  def SetUp(self):
    self.database_ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.databases')

  def testGetIamPolicy(self, track):
    self.track = track
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)
    self.client.projects_instances_databases.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
            resource=self.database_ref.RelativeName()),
        response=test_iam_policy)
    get_policy_request = self.Run(
        'spanner databases get-iam-policy dbId --instance=insId')
    self.assertEqual(get_policy_request, test_iam_policy)

  def testListCommandFilter(self, track):
    self.track = track
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)
    self.client.projects_instances_databases.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
            resource=self.database_ref.RelativeName()),
        response=test_iam_policy)

    self.Run("""
        spanner databases get-iam-policy dbId --instance=insId
        --flatten=bindings[].members
        --filter=bindings.role:roles/spanner.viewer
        --format=table[no-heading](bindings.members:sort=1)
        """)

    self.AssertOutputEquals('user:admin@foo.com\n')
