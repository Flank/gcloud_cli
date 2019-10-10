# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for Spanner instances get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class GetIamPolicyTestGA(base.SpannerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.instance_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')

  def testGetIamPolicy(self):
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com']), self.msgs.Binding(
                    role='roles/spanner.viewer',
                    members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            getIamPolicyRequest=self.msgs.GetIamPolicyRequest(
                options=self.msgs.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))),
        response=test_iam_policy)
    get_policy_request = self.Run(
        'spanner instances get-iam-policy insId')
    self.assertEqual(get_policy_request, test_iam_policy)

  def testListCommandFilter(self):
    test_iam_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin',
                members=['domain:foo.com']), self.msgs.Binding(
                    role='roles/spanner.viewer',
                    members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            getIamPolicyRequest=self.msgs.GetIamPolicyRequest(
                options=self.msgs.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))),
        response=test_iam_policy)
    self.Run("""
        spanner instances get-iam-policy insId
        --flatten=bindings[].members
        --filter=bindings.role:roles/spanner.viewer
        --format=table[no-heading](bindings.members:sort=1)
        """)
    self.AssertOutputEquals('user:admin@foo.com\n')


class GetIamPolicyTestBeta(GetIamPolicyTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class GetIamPolicyTestAlpha(GetIamPolicyTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

