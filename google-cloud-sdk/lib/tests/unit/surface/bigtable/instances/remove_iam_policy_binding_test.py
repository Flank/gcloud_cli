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
"""Tests for bigtable remove-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.bigtable import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class RemoveIamPolicyBindingTest(base.BigtableV2TestBase):

  def SetUp(self):
    self.role_to_remove = 'roles/bigtable.admin'
    self.user_to_remove = 'user:example@google.com'

    self.instance_ref = util.GetInstanceRef('my-instance')
    self.start_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/bigtable.admin',
                members=['domain:foo.com', self.user_to_remove]),
            self.msgs.Binding(
                role='roles/bigtable.viewer', members=['user:admin@foo.com'])
        ],
        etag='someUniqueEtag'.encode(),
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/bigtable.admin', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/bigtable.viewer', members=['user:admin@foo.com'])
        ],
        etag='someUniqueEtag'.encode(),
        version=1)

  def testRemoveIamPolicyBinding(self, track):
    """Test the standard use case."""
    self.track = track
    self.client.projects_instances.GetIamPolicy.Expect(
        request=self.msgs.BigtableadminProjectsInstancesGetIamPolicyRequest(
            resource=self.instance_ref.RelativeName()),
        response=self.start_policy)

    set_request = self.msgs.SetIamPolicyRequest(policy=self.new_policy)
    self.client.projects_instances.SetIamPolicy.Expect(
        request=self.msgs.BigtableadminProjectsInstancesSetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.new_policy)

    remove_binding_request = self.Run("""
        bigtable instances remove-iam-policy-binding my-instance
        --role={0} --member={1}
        """.format(self.role_to_remove, self.user_to_remove))
    self.assertEqual(remove_binding_request, self.new_policy)
