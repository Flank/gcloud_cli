# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for surface.billing.projects.link ."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.billing import base

messages = core_apis.GetMessagesModule('cloudbilling', 'v1')


class AccountsProjectsLinkTest(base.BillingMockNoDisplayTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testLink(self):
    self.mocked_billing.projects.UpdateBillingInfo.Expect(
        messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=base.PROJECTS[0].projectId,
            ),
            projectBillingInfo=messages.ProjectBillingInfo(
                billingAccountName=base.PROJECTS[0].billingAccountName
            )
        ),
        base.PROJECTS[0]
    )

    self.assertEqual(
        self.Run('billing projects link {project_id} '
                 '--billing-account {account_id}'.format(
                     project_id=base.PROJECTS[0].projectId,
                     account_id=base.BILLING_ACCOUNTS[0].name[16:])),
        base.PROJECTS[0])

  def _RunTestFlagVariation(self, flag_variation, flag_alternate=None,
                            track=None):
    self.mocked_billing.projects.UpdateBillingInfo.Expect(
        messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=base.PROJECTS[0].projectId,
            ),
            projectBillingInfo=messages.ProjectBillingInfo(
                billingAccountName=base.PROJECTS[0].billingAccountName
            )
        ),
        base.PROJECTS[0]
    )

    account_id = base.BILLING_ACCOUNTS[0].name[16:]
    command = ('billing projects link {project_id} '
               '{flag_name} {account_id}').format(
                   project_id=base.PROJECTS[0].projectId,
                   flag_name=flag_variation,
                   account_id=account_id)
    if flag_alternate:
      command += ' {flag_name} {account_id}'.format(
          flag_name=flag_alternate,
          account_id=account_id)

    self.assertEqual(
        self.Run(command, track=track),
        base.PROJECTS[0],
    )

  def testLinkOldAccountFlagAlpha(self):
    self._RunTestFlagVariation(
        '--account-id', track=calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrContains(
        'The `--account-id` flag has been renamed `--billing-account`.')

  def testLinkNewAccountFlagAlpha(self):
    self._RunTestFlagVariation(
        '--billing-account', track=calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrNotContains(
        'The `--account-id` flag has been renamed `--billing-account`.')

  def testLinkBothAccountFlagsAlpha(self):
    self._RunTestFlagVariation(
        '--account-id',
        flag_alternate='--billing-account',
        track=calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrContains(
        'The `--account-id` flag has been renamed `--billing-account`.')

  def testLinkNeitherAccountFlagAlpha(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--account-id | --billing-account) must be specified.'):
      self.Run(
          'billing projects link {project_id}'.format(
              project_id=base.PROJECTS[0].projectId),
          track=calliope_base.ReleaseTrack.ALPHA)

  def testLinkOldAccountFlag(self):
    err = """\
 --account-id flag is available in one or more alternate release tracks. Try:

  gcloud alpha billing projects link --account-id

  --account-id (did you mean '--account'?)
  000000-000000-000000
"""
    with self.AssertRaisesArgumentErrorMatches(err):
      self.Run(
          'billing projects link {project_id} '
          '    --account-id {account_id}'.format(
              project_id=base.PROJECTS[0].projectId,
              account_id=base.BILLING_ACCOUNTS[0].name[16:]))


if __name__ == '__main__':
  test_case.main()
