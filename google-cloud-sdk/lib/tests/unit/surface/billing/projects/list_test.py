# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for surface.billing.projects.list ."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.billing import base

messages = core_apis.GetMessagesModule('cloudbilling', 'v1')


class AccountsProjectsListTest(base.BillingMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testZeroProjects(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            name=base.BILLING_ACCOUNTS[0].name,
            pageSize=100,
        ),
        messages.ListProjectBillingInfoResponse(projectBillingInfo=[])
    )

    self.Run('billing projects list --billing-account {account_id}'.format(
        account_id=base.BILLING_ACCOUNTS[0].name[16:]
    ))
    self.AssertErrContains('Listed 0 items')

  def testOneProject(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            pageSize=100,
            name=base.BILLING_ACCOUNTS[0].name
        ),
        messages.ListProjectBillingInfoResponse(
            projectBillingInfo=[
                base.PROJECTS[0]
            ]
        )
    )

    self.Run('billing projects list --billing-account {account_id}'.format(
        account_id=base.BILLING_ACCOUNTS[0].name[16:]
    ))
    self.AssertOutputContains("""\
PROJECT_ID                   BILLING_ACCOUNT_ID    BILLING_ENABLED
my-project                   000000-000000-000000  True
""", normalize_space=True)

  def testMultiplePages(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            pageSize=100,
            name=base.BILLING_ACCOUNTS[0].name
        ),
        messages.ListProjectBillingInfoResponse(
            projectBillingInfo=base.PROJECTS[:1],
            nextPageToken='A'
        )
    )

    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            pageSize=100,
            name=base.BILLING_ACCOUNTS[0].name,
            pageToken='A'
        ),
        messages.ListProjectBillingInfoResponse(
            projectBillingInfo=base.PROJECTS[1:]
        )
    )

    self.Run('billing projects list --billing-account {account_id}'.format(
        account_id=base.BILLING_ACCOUNTS[0].name[16:]
    ))

    self.AssertOutputContains("""\
PROJECT_ID                   BILLING_ACCOUNT_ID    BILLING_ENABLED
my-project                   000000-000000-000000  True
my-other-project             000000-000000-000000  True
""", normalize_space=True)

  def testLimit(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            name=base.BILLING_ACCOUNTS[0].name,
            pageSize=1,
        ),
        messages.ListProjectBillingInfoResponse(
            projectBillingInfo=base.PROJECTS
        )
    )

    self.Run(
        'billing projects list --billing-account {account_id} --limit=1'.format(
            account_id=base.BILLING_ACCOUNTS[0].name[16:]
        )
    )
    self.AssertOutputContains("""\
PROJECT_ID                   BILLING_ACCOUNT_ID    BILLING_ENABLED
my-project                   000000-000000-000000  True
""", normalize_space=True)

  def testListOldAccountFlagAlpha(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            name=base.BILLING_ACCOUNTS[0].name,
            pageSize=100),
        messages.ListProjectBillingInfoResponse(projectBillingInfo=[]))

    self.Run('billing projects list {account_id}'.format(
        account_id=base.BILLING_ACCOUNTS[0].name[16:]),
             track=calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrContains(
        'The `ACCOUNT_ID` argument has been renamed `--billing-account`.')

  def testListNewAccountFlagAlpha(self):
    self.mocked_billing.billingAccounts_projects.List.Expect(
        messages.CloudbillingBillingAccountsProjectsListRequest(
            name=base.BILLING_ACCOUNTS[0].name,
            pageSize=100),
        messages.ListProjectBillingInfoResponse(projectBillingInfo=[]))

    self.Run('billing projects list --billing-account {account_id}'.format(
        account_id=base.BILLING_ACCOUNTS[0].name[16:]),
             track=calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrNotContains(
        'The `ACCOUNT_ID` argument has been renamed `--billing-account`.')

  def testListBothAccountFlagsAlpha(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument [ACCOUNT_ID]: Exactly one of ([ACCOUNT_ID] '
        '--billing-account) must be specified.'):
      self.Run('billing projects list {account_id} '
               '    --billing-account {account_id}'.format(
                   account_id=base.BILLING_ACCOUNTS[0].name[16:]),
               track=calliope_base.ReleaseTrack.ALPHA)

  def testListNeitherAccountFlag(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --billing-account: Must be specified.'):
      self.Run('billing projects list'.format(
          account_id=base.BILLING_ACCOUNTS[0].name[16:]
      ))

  def testListOldAccountPositionalBeta(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments: 000000-000000-000000'):
      self.Run('billing projects list {account_id}'.format(
          account_id=base.BILLING_ACCOUNTS[0].name[16:]
      ))


if __name__ == '__main__':
  test_case.main()
