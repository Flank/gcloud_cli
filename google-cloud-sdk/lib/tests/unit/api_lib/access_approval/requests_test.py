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
"""Tests for Access Approval requests library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.access_approval import requests
from tests.lib.surface.access_approval import base


class RequestsClientTest(base.AccessApprovalTestBase):

  def testApprove_org(self):
    name = 'organizations/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalOrganizationsApprovalRequestsApproveRequest(
        name=name)
    # this doesn't reflect a realistic response after an approve but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.organizations_approvalRequests.Approve.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Approve(name))

  def testApprove_folder(self):
    name = 'folders/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalFoldersApprovalRequestsApproveRequest(
        name=name)
    # this doesn't reflect a realistic response after an approve but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.folders_approvalRequests.Approve.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Approve(name))

  def testApprove_project(self):
    name = 'projects/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalProjectsApprovalRequestsApproveRequest(
        name=name)
    # this doesn't reflect a realistic response after an approve but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.projects_approvalRequests.Approve.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Approve(name))

  def testDismiss_org(self):
    name = 'organizations/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalOrganizationsApprovalRequestsDismissRequest(
        name=name)
    # this doesn't reflect a realistic response after a dismiss but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.organizations_approvalRequests.Dismiss.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Dismiss(name))

  def testDismiss_folder(self):
    name = 'folders/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalFoldersApprovalRequestsDismissRequest(
        name=name)
    # this doesn't reflect a realistic response after a dismiss but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.folders_approvalRequests.Dismiss.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Dismiss(name))

  def testDismiss_project(self):
    name = 'projects/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalProjectsApprovalRequestsDismissRequest(
        name=name)
    # this doesn't reflect a realistic response after a dismiss but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.projects_approvalRequests.Dismiss.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Dismiss(name))

  def testGet_org(self):
    name = 'organizations/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalOrganizationsApprovalRequestsGetRequest(
        name=name)
    # this doesn't reflect a realistic response from a get but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.organizations_approvalRequests.Get.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Get(name))

  def testGet_folder(self):
    name = 'folders/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalFoldersApprovalRequestsGetRequest(
        name=name)
    # this doesn't reflect a realistic response from a get but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.folders_approvalRequests.Get.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Get(name))

  def testGet_project(self):
    name = 'projects/123/approvalRequests/abcdefg1234567'
    req = self.msgs.AccessapprovalProjectsApprovalRequestsGetRequest(
        name=name)
    # this doesn't reflect a realistic response from a get but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ApprovalRequest(name=name)
    self.client.projects_approvalRequests.Get.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, requests.Get(name))

  def testList_org_noFilter(self):
    parent = 'organizations/123'
    req = self.msgs.AccessapprovalOrganizationsApprovalRequestsListRequest(
        parent=parent,
        filter='PENDING',
        pageSize=100)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    approval_requests = [self.msgs.ApprovalRequest(
        name=parent+'approvalRequests/123')]
    mocked_response = self.msgs.ListApprovalRequestsResponse(
        approvalRequests=approval_requests)
    self.client.organizations_approvalRequests.List.Expect(
        request=req,
        response=mocked_response)
    self.assertCountEqual(approval_requests, requests.List(parent))

  def testList_folder_allFilter(self):
    parent = 'folders/123'
    req = self.msgs.AccessapprovalFoldersApprovalRequestsListRequest(
        parent=parent,
        filter='ALL',
        pageSize=100)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    approval_requests = [self.msgs.ApprovalRequest(
        name=parent+'approvalRequests/123')]
    mocked_response = self.msgs.ListApprovalRequestsResponse(
        approvalRequests=approval_requests)
    self.client.folders_approvalRequests.List.Expect(
        request=req,
        response=mocked_response)
    self.assertCountEqual(approval_requests, requests.List(parent, 'ALL'))

  def testList_project_emptyResponse(self):
    parent = 'projects/123'
    req = self.msgs.AccessapprovalProjectsApprovalRequestsListRequest(
        parent=parent,
        filter='PENDING',
        pageSize=100)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.ListApprovalRequestsResponse(
        approvalRequests=[])
    self.client.projects_approvalRequests.List.Expect(
        request=req,
        response=mocked_response)
    self.assertCountEqual([], requests.List(parent))
