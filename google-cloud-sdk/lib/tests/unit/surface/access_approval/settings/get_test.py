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
"""Tests for Access Approval settings get command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib.surface.access_approval import base

# Note: we don't validate the responses here because the tests under api_lib
# do that already. These tests are to make sure we've wired everthing together
# correctly.


class GetTestAlpha(base.AccessApprovalTestAlpha):
  """Access Approval get test."""

  def testGet(self):
    name = 'organizations/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalOrganizationsGetAccessApprovalSettingsRequest(
        name=name)
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.organizations.GetAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval settings get --organization=123')

  def testGet_defaultToCoreProject(self):
    name = 'projects/my-project-123/accessApprovalSettings'
    req = self.msgs.AccessapprovalProjectsGetAccessApprovalSettingsRequest(
        name=name)
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.projects.GetAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    properties.VALUES.core.project.Set('my-project-123')
    self.Run('access-approval settings get')

  def testMissingParent_coreProjectNotSet(self):
    with self.assertRaises(Exception):
      self.Run('access-approval settings get')
