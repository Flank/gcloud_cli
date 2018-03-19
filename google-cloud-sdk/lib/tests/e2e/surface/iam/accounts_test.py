# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/deleting IAM service accounts."""

from tests.lib.surface.iam import e2e_test_base


# This test requires the 'Google Identity and Access Management' API to be
# enabled on the current project.
class AccountsTest(e2e_test_base.ServiceAccountBaseTest):

  def testAccounts(self):
    self.CreateAccount()
    self.DescribeAccount()
    self.UpdateAccount()
    self.ListAccount()
    self.DeleteAccount()

  def ClearOutputs(self):
    self.ClearOutput()
    self.ClearErr()

  def CreateAccount(self):
    self.ClearOutputs()
    self.Run(
        'iam service-accounts create {0} '
        '--display-name "Test Account"'.format(self.account_name))
    self.AssertErrEquals(
        'Created service account [{0}].\n'.format(self.account_name))
    self.AssertOutputEquals('')

  def DescribeAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('projectId: cloud-sdk-integration-testing')
    self.AssertOutputContains('displayName: Test Account')
    self.AssertOutputContains('email: {0}'.format(self.email))

  def UpdateAccount(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam service-accounts update {email} '
        '--display-name "Updated Account"')
    self.AssertErrEquals(
        'Updated service account [{0}].\n'.format(self.email))

    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('displayName: Updated Account')
    self.AssertOutputContains('email: {0}'.format(self.email))

  def ListAccount(self):
    self.ClearOutputs()
    self.Run('iam service-accounts list')
    # self.AssertOutputContains('email: {0}'.format(self.email))
    self.AssertOutputContains(self.email)

  def DeleteAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts delete {email}')
    self.AssertErrContains('deleted service account')
    self.AssertErrContains(self.email)
    # TODO(b/36049692): b/26496763. For some reason, deleting an account
    # multiple times in rapid succession causes a server-side error sometimes.
    # If we've made it to this point, the service account has already been
    # deleted, and cleanup isn't necessary.
    self.requires_cleanup = False


if __name__ == '__main__':
  e2e_test_base.main()
