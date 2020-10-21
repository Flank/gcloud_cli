# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.accesscontextmanager.cloud_bindings.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class BindingCreateTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeGcpUserAccessBinding(self, group_key, access_level, name=None):
    return self.messages.GcpUserAccessBinding(
        name=name, groupKey=group_key, accessLevels=[access_level])

  def _ExpectCreate(self, org_id, group_key, access_level, binding):
    m = self.messages
    request_type = m.AccesscontextmanagerOrganizationsGcpUserAccessBindingsCreateRequest
    self.client.organizations_gcpUserAccessBindings.Create.Expect(
        request_type(
            parent='organizations/{}'.format(org_id),
            gcpUserAccessBinding=self._MakeGcpUserAccessBinding(
                group_key, access_level)), self.messages.Operation(done=True))

  def testCreate(self):
    self.SetUpForAPI(self.api_version)

    org_id = 'MY_ORG'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(
        group_key, 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL',
        binding_name)
    self._ExpectCreate(org_id, group_key, access_level, binding)

    self.Run('access-context-manager cloud-bindings create --quiet '
             '--organization MY_ORG --group-key MY_GROUP_KEY '
             '--level accessPolicies/MY_POLICY/accessLevels/MY_LEVEL')

  def testCreate_resourceArg(self):
    self.SetUpForAPI(self.api_version)

    org_id = 'MY_ORG'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(
        group_key, 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL',
        binding_name)
    self._ExpectCreate(org_id, group_key, access_level, binding)

    self.Run('access-context-manager cloud-bindings create --quiet '
             '--organization MY_ORG --group-key MY_GROUP_KEY '
             '--level MY_LEVEL --policy MY_POLICY')

  def testCreate_orgnizationFromProperty(self):
    self.SetUpForAPI(self.api_version)

    org_id = '123'
    properties.VALUES.access_context_manager.organization.Set(org_id)
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/123/gcpUserAccessBindings/MY_BINDING'
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(
        group_key, 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL',
        binding_name)
    self._ExpectCreate(org_id, group_key, access_level, binding)

    self.Run('access-context-manager cloud-bindings create --quiet '
             '--group-key MY_GROUP_KEY --level MY_LEVEL --policy MY_POLICY')


if __name__ == '__main__':
  test_case.main()
