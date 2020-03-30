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
"""Tests for Access Approval requests list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.access_approval import base

# Note: we don't validate the responses here because the tests under api_lib
# do that already. These tests are to make sure we've wired everthing together
# correctly.


class ListTestAlpha(base.AccessApprovalTestAlpha):
  """Access Approval list test."""

  def testList_defaultFilter(self):
    parent = 'folders/123'
    req = self.msgs.AccessapprovalFoldersApprovalRequestsListRequest(
        parent=parent,
        filter='PENDING',
        pageSize=100)
    approval_requests = [self.msgs.ApprovalRequest(
        name=parent+'approvalRequests/123')]
    mocked_response = self.msgs.ListApprovalRequestsResponse(
        approvalRequests=approval_requests)
    self.client.folders_approvalRequests.List.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval requests list --folder=123')

  def testList_filterPassed(self):
    parent = 'projects/123'
    req = self.msgs.AccessapprovalProjectsApprovalRequestsListRequest(
        parent=parent,
        filter='ALL',
        pageSize=100)
    approval_requests = [self.msgs.ApprovalRequest(
        name=parent+'approvalRequests/123')]
    mocked_response = self.msgs.ListApprovalRequestsResponse(
        approvalRequests=approval_requests)
    self.client.projects_approvalRequests.List.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval requests list --project=123 --state=all')
