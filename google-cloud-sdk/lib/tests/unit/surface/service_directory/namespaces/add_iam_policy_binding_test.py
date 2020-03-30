# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud service-directory namespaces add-iam-policy-binding`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class AddIamPolicyBindingTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.role = 'roles/owner'
    self.user = 'user:foo@google.com'

    self.namespace_ref = resources.REGISTRY.Parse(
        'my-namespace',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
        },
        collection='servicedirectory.projects.locations.namespaces')

    self.start_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(role='roles/owner', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/viewer', members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.new_policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/owner', members=['domain:foo.com', self.user]),
            self.msgs.Binding(
                role='roles/viewer', members=['user:admin@foo.com']),
        ],
        etag=b'someUniqueEtag',
        version=1)

  def _ExpectGetIamPolicyRequest(self, policy):
    request = self.msgs.ServicedirectoryProjectsLocationsNamespacesGetIamPolicyRequest(
        resource=self.namespace_ref.RelativeName())
    return self.client.projects_locations_namespaces.GetIamPolicy.Expect(
        request=request, response=policy)

  def _ExpectSetIamPolicyRequest(self, policy):
    set_request = self.msgs.SetIamPolicyRequest(policy=policy)
    request = self.msgs.ServicedirectoryProjectsLocationsNamespacesSetIamPolicyRequest(
        resource=self.namespace_ref.RelativeName(),
        setIamPolicyRequest=set_request)
    self.client.projects_locations_namespaces.SetIamPolicy.Expect(
        request=request, response=policy)

  def testAddIamPolicyBinding(self):
    self._ExpectGetIamPolicyRequest(self.start_policy)
    self._ExpectSetIamPolicyRequest(self.new_policy)

    add_binding_request = self.Run('service-directory namespaces '
                                   'add-iam-policy-binding my-namespace '
                                   '--location my-location '
                                   '--role={0} '
                                   '--member={1}'.format(self.role, self.user))
    self.assertEqual(add_binding_request, self.new_policy)


class AddIamPolicyBindingTestAlpha(AddIamPolicyBindingTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
