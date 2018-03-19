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
"""E2E tests for `gcloud billing` commands.

Depends on having at least one billing account in the test project. If the
project wants to make any meaningful calls, this should already be the case.
"""

from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case


class BillingE2eTests(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA

  def testBillingE2eTests(self):
    accounts = list(self.Run('billing accounts list '
                             '    --format disable '
                             '    --filter open:true'))
    self.assertTrue(accounts)
    account_name = accounts[0].name[len('billingAccounts/'):]
    projects = self.Run('billing projects list --billing-account {} '
                        '    --format disable'.format(account_name))
    self.assertTrue(projects)


if __name__ == '__main__':
  test_case.main()
