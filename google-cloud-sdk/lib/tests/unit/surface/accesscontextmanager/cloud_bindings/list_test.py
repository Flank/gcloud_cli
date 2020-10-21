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
"""Tests for google3.third_party.py.tests.unit.surface.accesscontextmanager.cloud_bindings.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class BindingListTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeGcpUserAccessBinding(self, name, group_key, access_level):
    return self.messages.GcpUserAccessBinding(
        name=name, groupKey=group_key, accessLevels=[access_level])

  def _ExpectList(self, bindings, organization):
    organization_name = 'organizations/{}'.format(organization)
    m = self.messages
    list_req_type = m.AccesscontextmanagerOrganizationsGcpUserAccessBindingsListRequest
    self.client.organizations_gcpUserAccessBindings.List.Expect(
        list_req_type(parent=organization_name),
        self.messages.ListGcpUserAccessBindingsResponse(
            gcpUserAccessBindings=bindings))

  def testList(self):
    self.SetUpForAPI(self.api_version)
    organization_id = 'MY_ORG'
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectList([binding], organization_id)
    results = self.Run(
        'access-context-manager cloud-bindings list --organization MY_ORG')
    self.assertEqual(results, [binding])

  def testList_OutputFormat(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)

    organization_id = 'MY_ORG'
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectList([binding], organization_id)
    self.Run('access-context-manager cloud-bindings list --organization MY_ORG')

    self.AssertOutputEquals(
        """\
        NAME  GROUP_KEY  ACCESS_LEVEL
        {}    {}         {}
        """.format(binding_name, group_key, access_level),
        normalize_space=True)

  def testList_OrganizationFromProperty(self):
    self.SetUpForAPI(self.api_version)

    organization_id = '123'
    properties.VALUES.access_context_manager.organization.Set(organization_id)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectList([binding], organization_id)
    results = self.Run(
        'access-context-manager cloud-bindings list')
    self.assertEqual(results, [binding])


if __name__ == '__main__':
  test_case.main()
