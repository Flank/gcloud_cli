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
"""Tests for google3.third_party.py.tests.unit.surface.accesscontextmanager.cloud_bindings.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class BindingDescribeTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeGcpUserAccessBinding(self, name, group_key, access_level):
    return self.messages.GcpUserAccessBinding(
        name=name, groupKey=group_key, accessLevels=[access_level])

  def _ExpectGet(self, binding):
    m = self.messages
    get_req_type = m.AccesscontextmanagerOrganizationsGcpUserAccessBindingsGetRequest
    self.client.organizations_gcpUserAccessBindings.Get.Expect(
        get_req_type(name=binding.name), binding)

  def testDescribe(self):
    self.SetUpForAPI(self.api_version)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectGet(binding)
    results = self.Run('access-context-manager cloud-bindings describe '
                       '--binding MY_BINDING --organization MY_ORG ')
    self.assertEqual(results, binding)

  def testDescribe_OutputFormat(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)

    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectGet(binding)
    self.Run('access-context-manager cloud-bindings describe '
             '--binding MY_BINDING --organization MY_ORG ')

    self.AssertOutputEquals(
        """\
        accessLevels:
        - accessPolicies/MY_POLICY/accessLevels/MY_LEVEL
        groupKey: MY_GROUP_KEY
        name: organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING
        """,
        normalize_space=True)

  def testDescribe_OrganizationFromProperty(self):
    org_id = '123'
    properties.VALUES.access_context_manager.organization.Set(org_id)

    self.SetUpForAPI(self.api_version)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    group_key = 'MY_GROUP_KEY'
    binding_name = 'organizations/123/gcpUserAccessBindings/MY_BINDING'
    binding = self._MakeGcpUserAccessBinding(binding_name, group_key,
                                             access_level)
    self._ExpectGet(binding)
    results = self.Run('access-context-manager cloud-bindings describe '
                       '--binding MY_BINDING')
    self.assertEqual(results, binding)


if __name__ == '__main__':
  test_case.main()
