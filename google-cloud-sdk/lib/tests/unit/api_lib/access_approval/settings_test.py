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

from googlecloudsdk.api_lib.access_approval import settings
from tests.lib.surface.access_approval import base


class SettingsClientTest(base.AccessApprovalTestBase):

  def testDelete_org(self):
    name = 'organizations/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalOrganizationsDeleteAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.Empty()
    self.client.organizations.DeleteAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Delete(name))

  def testDelete_folder(self):
    name = 'folders/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalFoldersDeleteAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.Empty()
    self.client.folders.DeleteAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Delete(name))

  def testDelete_project(self):
    name = 'projects/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalProjectsDeleteAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.Empty()
    self.client.projects.DeleteAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Delete(name))

  def testGet_org(self):
    name = 'organizations/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalOrganizationsGetAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.organizations.GetAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Get(name))

  def testGet_folder(self):
    name = 'folders/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalFoldersGetAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.folders.GetAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Get(name))

  def testGet_project(self):
    name = 'projects/123/accessApprovalSettings'
    req = self.msgs.AccessapprovalProjectsGetAccessApprovalSettingsRequest(
        name=name)
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.projects.GetAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Get(name))

  def testUpdate_org_emailsOnly(self):
    name = 'organizations/123/accessApprovalSettings'
    emails_list = ['foo@test.com', 'bar@test.com']
    req = self.msgs.AccessapprovalOrganizationsUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=emails_list,
            enrolledServices=[]),
        updateMask='notification_emails')
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.organizations.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Update(
        name=name,
        enrolled_services=[],
        notification_emails=emails_list,
        update_mask='notification_emails'))

  def testUpdate_folder_enrolledServicesOnly(self):
    name = 'folders/123/accessApprovalSettings'
    services = ['all']
    services_protos = [self.msgs.EnrolledService(cloudProduct='all')]
    req = self.msgs.AccessapprovalFoldersUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=[],
            enrolledServices=services_protos),
        updateMask='enrolled_services')
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.folders.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Update(
        name=name,
        enrolled_services=services,
        notification_emails=[],
        update_mask='enrolled_services'))

  def testUpdate_project_bothFields(self):
    name = 'projects/123/accessApprovalSettings'
    emails_list = ['foo@test.com', 'bar@test.com']
    services = ['all']
    services_protos = [self.msgs.EnrolledService(cloudProduct='all')]
    req = self.msgs.AccessapprovalProjectsUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=emails_list,
            enrolledServices=services_protos),
        updateMask='enrolled_services,notification_emails')
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.projects.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.assertEqual(mocked_response, settings.Update(
        name=name,
        enrolled_services=services,
        notification_emails=emails_list,
        update_mask='enrolled_services,notification_emails'))
