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

"""Tests that ensure getting an IAM policy works properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class GetIamPolicyTestGA(base.CloudIotBase, test_case.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testGetIamPolicy(self):
    policy = self.messages.Policy(
        version=1,
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.messages.Binding(role='roles/viewer', members=['allUsers'])
        ])

    self.client.projects_locations_registries.GetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry')),
        response=policy)

    result = self.Run('iot registries get-iam-policy --format=disable '
                      'my-registry --region us-central1 ')

    self.assertEqual(result, policy)

  def testListCommandFilter(self):
    policy = self.messages.Policy(
        version=1,
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.messages.Binding(role='roles/viewer', members=['allUsers'])
        ])

    self.client.projects_locations_registries.GetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry')),
        response=policy)

    self.Run("""
        iot registries get-iam-policy my-registry --region us-central1
        --flatten=bindings[].members
        --filter=bindings.role:roles/owner
        --format=value(bindings.members)
        """)

    self.AssertOutputEquals('user:test-user@gmail.com\n')

  def testGetIamPolicy_RelativeName(self):
    policy = self.messages.Policy(
        version=1,
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.messages.Binding(role='roles/viewer', members=['allUsers'])
        ])

    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')
    self.client.projects_locations_registries.GetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource=registry_name),
        response=policy)

    result = self.Run('iot registries get-iam-policy --format=disable '
                      '{}'.format(registry_name))

    self.assertEqual(result, policy)


class GetIamPolicyTestBeta(GetIamPolicyTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class GetIamPolicyTestAlpha(GetIamPolicyTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
