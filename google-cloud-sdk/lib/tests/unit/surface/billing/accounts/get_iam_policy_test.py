# Copyright 2018 Google Inc. All Rights Reserved.
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

"""`billing accounts get-iam-policy` command tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import http_encoding
from tests.lib import test_case
from tests.lib.surface.billing import base


class BillingAccountsGetIamPolicyTest(base.BillingMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testGetIamPolicy(self):
    test_iam_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/billing.admin', members=['robot@foo.com']),
        ],
        etag=http_encoding.Encode('someUniqueEtag'),
    )
    self.mocked_billing.billingAccounts.GetIamPolicy.Expect(
        self.messages.CloudbillingBillingAccountsGetIamPolicyRequest(
            resource=base.BILLING_ACCOUNTS[0].name
        ),
        test_iam_policy,
    )
    result = self.Run(
        'billing accounts get-iam-policy ' + base.BILLING_ACCOUNTS[0].name)
    self.assertEqual(result, test_iam_policy)

if __name__ == '__main__':
  test_case.main()
