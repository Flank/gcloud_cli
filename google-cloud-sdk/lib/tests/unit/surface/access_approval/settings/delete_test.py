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
"""Tests for Access Approval settings delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib.surface.access_approval import base

# Note: we don't validate the responses here because the tests under api_lib
# do that already. These tests are to make sure we've wired everthing together
# correctly.


class DeleteTestAlpha(base.AccessApprovalTestAlpha):
  """Access Approval delete test."""

  def testDelete(self):
    name = 'folders/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalFoldersDeleteAccessApprovalSettingsRequest(
        name=name)
    mocked_response = self.msgs.Empty()
    self.client.folders.DeleteAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval settings delete --folder=123')

  def testDelete_defaultToCoreProject(self):
    name = 'projects/my-project-123/accessApprovalSettings'
    req = self.msgs.AccessapprovalProjectsDeleteAccessApprovalSettingsRequest(
        name=name)
    mocked_response = self.msgs.Empty()
    self.client.projects.DeleteAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    properties.VALUES.core.project.Set('my-project-123')
    self.Run('access-approval settings delete')

  def testMissingParent_coreProjectNotSet(self):
    with self.assertRaises(Exception):
      self.Run('access-approval settings delete')
