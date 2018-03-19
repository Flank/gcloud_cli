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
"""Tests for surface.billing.accounts.list ."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.billing import base

messages = core_apis.GetMessagesModule('cloudbilling', 'v1')


class AccountsListTest(base.BillingMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testZeroAccounts(self):
    self.mocked_billing.billingAccounts.List.Expect(
        messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
        ),
        messages.ListBillingAccountsResponse(billingAccounts=[])
    )

    self.Run('billing accounts list')
    self.AssertErrContains('Listed 0 items')

  def testOneAccount(self):
    self.mocked_billing.billingAccounts.List.Expect(
        messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
        ),
        messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS[:1],
        )
    )

    self.Run('billing accounts list')
    self.AssertOutputContains("""\
ID                    NAME                  OPEN
000000-000000-000000  A Billing Account     True
""", normalize_space=True)

  def testMultiplePages(self):
    self.mocked_billing.billingAccounts.List.Expect(
        messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
        ),
        messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS[:1],
            nextPageToken='A',
        )
    )

    self.mocked_billing.billingAccounts.List.Expect(
        messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
            pageToken='A'
        ),
        messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS[1:],
        )
    )
    self.Run('billing accounts list')
    self.AssertOutputContains("""\
ID                    NAME                    OPEN
000000-000000-000000  A Billing Account       True
000000-000000-000001  Another Billing Account False
""", normalize_space=True)

  def testLimit(self):
    self.mocked_billing.billingAccounts.List.Expect(
        messages.CloudbillingBillingAccountsListRequest(
            pageSize=1,
        ),
        messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS,
        )
    )
    self.Run('billing accounts list --limit=1')
    self.AssertOutputContains("""\
ID                    NAME                    OPEN
000000-000000-000000  A Billing Account       True
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
