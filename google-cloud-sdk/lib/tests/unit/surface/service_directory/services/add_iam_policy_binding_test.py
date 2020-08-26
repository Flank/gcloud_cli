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
"""Tests for `gcloud service-directory services add-iam-policy-binding`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.service_directory import base


class AddIamPolicyBindingTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.role = 'roles/owner'
    self.user = 'user:foo@google.com'

    self.service_ref = resources.REGISTRY.Parse(
        'my-service',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
            'namespacesId': 'my-namespace',
        },
        collection='servicedirectory.projects.locations.namespaces.services')

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
    request = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesGetIamPolicyRequest(
        resource=self.service_ref.RelativeName())
    return self.client.projects_locations_namespaces_services.GetIamPolicy.Expect(
        request=request, response=policy)

  def _ExpectSetIamPolicyRequest(self, policy):
    set_request = self.msgs.SetIamPolicyRequest(policy=policy)
    request = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesSetIamPolicyRequest(
        resource=self.service_ref.RelativeName(),
        setIamPolicyRequest=set_request)
    self.client.projects_locations_namespaces_services.SetIamPolicy.Expect(
        request=request, response=policy)

  def testAddIamPolicyBinding(self):
    self._ExpectGetIamPolicyRequest(self.start_policy)
    self._ExpectSetIamPolicyRequest(self.new_policy)

    add_binding_request = self.Run('service-directory services '
                                   'add-iam-policy-binding my-service '
                                   '--namespace my-namespace '
                                   '--location my-location '
                                   '--role={0} '
                                   '--member={1}'.format(self.role, self.user))
    self.assertEqual(add_binding_request, self.new_policy)
    self.AssertErrContains('Updated IAM policy for')

  def testAddIamPolicyBinding_InvalidRequest_Fails(self):
    request = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesGetIamPolicyRequest(
        resource=self.service_ref.RelativeName())
    exception = http_error.MakeHttpError(code=400)
    self.client.projects_locations_namespaces_services.GetIamPolicy.Expect(
        request=request, exception=exception, response=None)
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Invalid request API reason: Invalid request.'):
      self.Run('service-directory services '
               'add-iam-policy-binding my-service '
               '--namespace my-namespace '
               '--location my-location '
               '--role={0} '
               '--member={1}'.format(self.role, self.user))
    self.AssertErrNotContains('Updated IAM policy for')


class AddIamPolicyBindingTestAlpha(AddIamPolicyBindingTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
