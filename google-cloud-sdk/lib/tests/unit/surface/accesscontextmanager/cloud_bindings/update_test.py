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
"""Tests for google3.third_party.py.tests.unit.surface.accesscontextmanager.cloud_bindings.update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class BindingUpdateTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeGcpUserAccessBinding(self, access_level):
    return self.messages.GcpUserAccessBinding(accessLevels=[access_level])

  def _ExpectPatch(self, binding, binding_name):
    m = self.messages
    request_type = m.AccesscontextmanagerOrganizationsGcpUserAccessBindingsPatchRequest
    self.client.organizations_gcpUserAccessBindings.Patch.Expect(
        request_type(
            gcpUserAccessBinding=binding,
            name=binding_name,
            updateMask='access_levels'), self.messages.Operation(done=True))

  def testUpdate(self):
    self.SetUpForAPI(self.api_version)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(access_level)
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    self._ExpectPatch(binding, binding_name)
    self.Run('access-context-manager cloud-bindings update --quiet '
             '--binding {} '
             '--level {}'.format(binding_name, access_level))

  def testUpdate_resourceArg(self):
    self.SetUpForAPI(self.api_version)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(access_level)
    binding_name = 'organizations/MY_ORG/gcpUserAccessBindings/MY_BINDING'
    self._ExpectPatch(binding, binding_name)
    self.Run('access-context-manager cloud-bindings update --quiet '
             '--binding MY_BINDING --organization MY_ORG '
             '--level MY_LEVEL --policy MY_POLICY')

  def testUpdate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must be specified'):
      self.Run('access-context-manager cloud-bindings update --quiet '
               '--binding MY_BINDING --organization MY_ORG ')

  def testUpdate_OrganizationFromProperty(self):
    self.SetUpForAPI(self.api_version)

    org_id = '123'
    properties.VALUES.access_context_manager.organization.Set(org_id)
    access_level = 'accessPolicies/MY_POLICY/accessLevels/MY_LEVEL'
    binding = self._MakeGcpUserAccessBinding(access_level)
    binding_name = 'organizations/123/gcpUserAccessBindings/MY_BINDING'
    self._ExpectPatch(binding, binding_name)
    self.Run('access-context-manager cloud-bindings update --quiet '
             '--binding MY_BINDING '
             '--level {}'.format(access_level))


if __name__ == '__main__':
  test_case.main()
