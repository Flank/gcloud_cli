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
"""Tests for `gcloud service-directory namespaces get-iam-policy`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class GetIamPolicyTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.namespace_name = 'projects/fake-project/locations/my-location/namespaces/my-namespace'
    self.iam_policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.msgs.Binding(role='roles/viewer', members=['allUsers'])
        ])

  def _ExpectGetIamPolicy(self):
    self.client.projects_locations_namespaces.GetIamPolicy.Expect(
        request=self.msgs
        .ServicedirectoryProjectsLocationsNamespacesGetIamPolicyRequest(
            resource=self.namespace_name),
        response=self.iam_policy)

  def testGetIamPolicy(self):
    self._ExpectGetIamPolicy()

    result = self.Run(
        'service-directory namespaces get-iam-policy my-namespace '
        '--format=disable '
        '--location my-location ')

    self.assertEqual(result, self.iam_policy)

  def testListCommandFilter(self):
    self._ExpectGetIamPolicy()

    self.Run('service-directory namespaces get-iam-policy my-namespace '
             '--location my-location '
             '--flatten=bindings[].members '
             '--filter=bindings.role:roles/owner '
             '--format=value(bindings.members)')

    self.AssertOutputEquals('user:test-user@gmail.com\n')

  def testGetIamPolicy_RelativeName(self):
    self._ExpectGetIamPolicy()

    result = self.Run(
        'service-directory namespaces get-iam-policy --format=disable {}'
        .format(self.namespace_name))

    self.assertEqual(result, self.iam_policy)


class GetIamPolicyTestAlpha(GetIamPolicyTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
