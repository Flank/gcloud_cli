# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for billing flags module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.billing import flags
from tests.lib import completer_test_base
from tests.lib.surface.billing import base


class CompleterCommandTest(completer_test_base.CompleterBase):

  def testBillingAccountsCompleterCommand(self):
    self.RunCompleter(
        flags.BillingAccountsCompleter,
        command_only=True,
        expected_command=[
            'beta', 'billing', 'accounts', 'list', '--uri', '--quiet',
            '--format=disable',
        ],
        args={
            '--id': 'my-id',
        },
    )


class BillingAccountsCompletionTest(base.BillingMockTest,
                                    completer_test_base.CompleterBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudbilling', 'v1')
    self.track = calliope_base.ReleaseTrack.BETA

  def testClusterCompletion(self):
    self.mocked_billing.billingAccounts.List.Expect(
        self.messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
        ),
        self.messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS[:1],
            nextPageToken='A',
        )
    )

    self.mocked_billing.billingAccounts.List.Expect(
        self.messages.CloudbillingBillingAccountsListRequest(
            pageSize=100,
            pageToken='A'
        ),
        self.messages.ListBillingAccountsResponse(
            billingAccounts=base.BILLING_ACCOUNTS[1:],
        )
    )

    self.RunCompleter(
        flags.BillingAccountsCompleter,
        expected_command=[
            'beta', 'billing', 'accounts', 'list', '--uri', '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            '000000-000000-000000',
            '111111-111111-111111',
            '222222-222222-222222',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
