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
"""Tests for Access Approval settings update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib.surface.access_approval import base

# Note: we don't validate the responses here because the tests under api_lib
# do that already. These tests are to make sure we've wired everthing together
# correctly.


class UpdateTestAlpha(base.AccessApprovalTestAlpha):
  """Access Approval update test."""

  def testUpdate_emailsOnly(self):
    name = 'organizations/123/accessApprovalSettings'
    emails_list = ['foo@test.com', 'bar@test.com']
    req = self.msgs.AccessapprovalOrganizationsUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=emails_list,
            enrolledServices=[]),
        updateMask='notification_emails')
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.organizations.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval settings update --organization=123 '
             '--notification_emails='+','.join(emails_list))

  def testUpdate_servicesOnly(self):
    name = 'folders/123/accessApprovalSettings'
    services_protos = [self.msgs.EnrolledService(cloudProduct='all')]
    req = self.msgs.AccessapprovalFoldersUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=[],
            enrolledServices=services_protos),
        updateMask='enrolled_services')
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.folders.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.Run('access-approval settings update --folder=123 '
             '--enrolled_services=all')

  def testUpdate_bothFields(self):
    name = 'organizations/123/accessApprovalSettings'
    emails_list = ['foo@test.com', 'bar@test.com']
    services = ['storage.googleapis.com', 'compute.googleapis.com']
    services_protos = [
        self.msgs.EnrolledService(cloudProduct='storage.googleapis.com'),
        self.msgs.EnrolledService(cloudProduct='compute.googleapis.com')]
    req = self.msgs.AccessapprovalOrganizationsUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=self.msgs.AccessApprovalSettings(
            name=name,
            notificationEmails=emails_list,
            enrolledServices=services_protos),
        updateMask='notification_emails,enrolled_services')
    # this doesn't reflect a realistic response but we don't
    # really care what it looks like because the library just passes the
    # response unmodified and doesn't look at it at all.
    mocked_response = self.msgs.AccessApprovalSettings(name=name)
    self.client.organizations.UpdateAccessApprovalSettings.Expect(
        request=req,
        response=mocked_response)
    self.Run(
        'access-approval settings update --organization=123 '
        '--enrolled_services=\'' + ', '.join(services) + '\' '
        '--notification_emails=\'' + ', '.join(emails_list) + '\'')

  def testUpdate_noFieldsToUpdate(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run('access-approval settings update --organization=123')

