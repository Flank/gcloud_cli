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
"""Tests for iot registries add-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class AddIamPolicyBindingTest(base.CloudIotBase):

  def SetUp(self):
    self.new_role = 'roles/owner'
    self.new_user = 'user:foo@google.com'
    self.start_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['domain:foo.com']),
            self.messages.Binding(
                role='roles/viewer',
                members=['user:admin@foo.com'],
            )
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.new_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['domain:foo.com', self.new_user]),
            self.messages.Binding(
                role='roles/viewer', members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)

  def testAddIamPolicyBinding(self, track):
    self.track = track
    self.client.projects_locations_registries.GetIamPolicy.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry')),
        response=self.start_policy)

    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry'),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.new_policy)),
        response=self.new_policy)

    req = self.Run('iot registries add-iam-policy-binding my-registry '
                   '--region=us-central1 --role={0} '
                   '--member={1}'.format(self.new_role, self.new_user))
    self.assertEqual(req, self.new_policy)
