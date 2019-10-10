# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.iam import e2e_test_base


# This test requires the 'Google Identity and Access Management' API to be
# enabled on the current project.
class AccountsTestGA(e2e_test_base.ServiceAccountBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testAccounts(self):
    self.CreateAccount()
    self.DescribeAccount()
    self.UpdateAccount()
    self.ListAccount()
    self.GetIamPolicy()
    self.DeleteAccount()

  def ClearOutputs(self):
    self.ClearOutput()
    self.ClearErr()

  def CreateAccount(self):
    self.ClearOutputs()
    self.Run('iam service-accounts create {0} '
             '--display-name "Test display name" '.format(self.account_name))
    self.AssertErrEquals('Created service account [{0}].\n'.format(
        self.account_name))
    self.AssertOutputEquals('')

  def DescribeAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('projectId: cloud-sdk-integration-testing')
    self.AssertOutputContains('displayName: Test display name')
    self.AssertOutputContains('email: {0}'.format(self.email))

  def UpdateAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts update {email} '
                   '--display-name "Updated display name"')
    self.AssertErrEquals('Updated serviceAccount [{0}].\n'.format(self.email))

    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('displayName: Updated display name')
    self.AssertOutputContains('email: {0}'.format(self.email))

  def ListAccount(self):
    time.sleep(5)  # Wait for sync to Cloud Gaia

    @sdk_test_base.Retry(why='Waiting for list result to reconcile',
                         max_retrials=10, sleep_ms=4000)
    def ListCheck():
      self.ClearOutputs()
      self.Run('iam service-accounts list')
      self.AssertOutputContains(self.email)

    ListCheck()

  def GetIamPolicy(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts get-iam-policy {email}')
    self.AssertOutputContains('etag: ACAB')

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


class AccountsTestBeta(AccountsTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

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
        '--display-name "Test display name" --description "Test description" '
        .format(self.account_name))
    self.AssertErrEquals('Created service account [{0}].\n'.format(
        self.account_name))
    self.AssertOutputEquals('')

  def DescribeAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('projectId: cloud-sdk-integration-testing')
    self.AssertOutputContains('displayName: Test display name')
    self.AssertOutputContains('description: Test description')
    self.AssertOutputContains('email: {0}'.format(self.email))

  def UpdateAccount(self):
    self.ClearOutputs()
    self.RunFormat('iam service-accounts update {email} '
                   '--display-name "Updated display name" '
                   '--description "Updated description"')
    self.AssertErrEquals('Updated serviceAccount [{0}].\n'.format(self.email))

    self.ClearOutputs()
    self.RunFormat('iam service-accounts describe {email}')
    self.AssertOutputContains('displayName: Updated display name')
    self.AssertOutputContains('description: Updated description')
    self.AssertOutputContains('email: {0}'.format(self.email))


class AccountsTestAlpha(AccountsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  e2e_test_base.main()
