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

"""Base classes for all gcloud dns tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

messages = core_apis.GetMessagesModule('cloudbilling', 'v1')
BILLING_ACCOUNTS = [
    messages.BillingAccount(
        displayName='A Billing Account',
        name='billingAccounts/000000-000000-000000',
        open=True,
    ),
    messages.BillingAccount(
        displayName='Another Billing Account',
        name='billingAccounts/111111-111111-111111',
        open=False,
    ),
    messages.BillingAccount(
        displayName='A Billing SubAccount',
        name='billingAccounts/222222-222222-222222',
        masterBillingAccount='billingAccounts/111111-111111-111111',
        open=False,
    ),
]

PROJECTS = [
    messages.ProjectBillingInfo(
        billingAccountName=BILLING_ACCOUNTS[0].name,
        billingEnabled=BILLING_ACCOUNTS[0].open,
        name='projects/my-project/billingInfo',
        projectId='my-project'
    ),
    messages.ProjectBillingInfo(
        billingAccountName=BILLING_ACCOUNTS[0].name,
        billingEnabled=BILLING_ACCOUNTS[0].open,
        name='projects/my-other-project/billingInfo',
        projectId='my-other-project'
    ),
]


class BillingMockTest(cli_test_base.CliTestBase,
                      sdk_test_base.WithFakeAuth,
                      sdk_test_base.WithTempCWD):
  """For gcloud billing tests that need a mocked billing client."""

  def SetUp(self):
    self.mocked_billing = mock.Client(
        core_apis.GetClientClass('cloudbilling', 'v1'))
    self.mocked_billing.Mock()
    self.addCleanup(self.mocked_billing.Unmock)
    self.messages = messages


class BillingMockNoDisplayTest(BillingMockTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
