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

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.billing import base


class BillingAccountsSetIamPolicyTest(base.BillingMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSetIamPolicy(self):
    test_iam_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role=u'roles/billing.admin',
                members=[u'robot@foo.com']),
        ],
        etag='someUniqueEtag',
    )
    temp_file = self.Touch(
        self.temp_path,
        contents=encoding.MessageToJson(test_iam_policy))
    self.mocked_billing.billingAccounts.SetIamPolicy.Expect(
        self.messages.CloudbillingBillingAccountsSetIamPolicyRequest(
            resource=base.BILLING_ACCOUNTS[0].name,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=test_iam_policy,
                updateMask='bindings,etag',
            ),
        ),
        test_iam_policy,
    )
    result = self.Run(
        'billing accounts set-iam-policy {} {}'.format(
            base.BILLING_ACCOUNTS[0].name, temp_file))
    self.assertEqual(result, test_iam_policy)


if __name__ == '__main__':
  test_case.main()
