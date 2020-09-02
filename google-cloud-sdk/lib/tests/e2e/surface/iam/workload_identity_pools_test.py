# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Integration tests for managing IAM workload identity pools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import time

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.iam import e2e_test_base


# This test requires the 'Google Identity and Access Management' API to be
# enabled on the current project.
class WorkloadIdentityPoolsTestBeta(e2e_test_base.WorkloadIdentityPoolBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testWorkloadIdentityPools(self):
    # Prepare resources at start to reduce needed sleep time
    self.CreateWorkloadIdentityPool()
    self.CreateAwsWorkloadIdentityPoolProvider()
    self.CreateOidcWorkloadIdentityPoolProvider()
    time.sleep(5)  # Wait for sync to regional storage

    # Get/List tests
    self.DescribeWorkloadIdentityPool()
    self.ListWorkloadIdentityPools()
    self.DescribeWorkloadIdentityPoolProvider()
    self.ListWorkloadIdentityPoolProviders()

    # Update tests (group to reduce needed sleep time)
    self.UpdateWorkloadIdentityPool()
    self.UpdateAwsWorkloadIdentityPoolProvider()
    self.UpdateOidcWorkloadIdentityPoolProvider()
    time.sleep(5)  # Wait for sync to regional storage
    self.CheckUpdateWorkloadIdentityPool()
    self.CheckUpdateAwsWorkloadIdentityPoolProvider()
    self.CheckUpdateOidcWorkloadIdentityPoolProvider()

    # Delete/undelete tests
    self.DeleteWorkloadIdentityPool()
    self.UndeleteWorkloadIdentityPool()
    self.CheckUndeleteWorkloadIdentityPoolOperation()
    self.DeleteWorkloadIdentityPoolProvider()
    self.UndeleteWorkloadIdentityPoolProvider()
    self.CheckUndeleteWorkloadIdentityPoolProviderOperation()

  def ClearOutputs(self):
    self.ClearOutput()
    self.ClearErr()

  def CreateWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools create {pool} --location {location} '
        '--display-name "Test display name"')
    self.AssertErrEquals('Created WorkloadIdentityPool [{0}].\n'.format(
        self.workload_identity_pool_id))
    self.AssertOutputEquals('')

  def DescribeWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools describe {pool} --location {location}')
    self.AssertOutputContains('displayName: Test display name')
    self.AssertOutputContains('name: {0}'.format(
        self.workload_identity_pool_name))
    self.AssertOutputContains('state: ACTIVE')

  def ListWorkloadIdentityPools(self):
    self.ClearOutputs()
    self.RunFormat('iam workload-identity-pools list --location {location}')
    self.AssertOutputContains('name: {0}'.format(
        self.workload_identity_pool_name))

  def UpdateWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools update {pool} --location {location} '
        '--display-name "Updated display name"')
    self.AssertErrEquals('Updated WorkloadIdentityPool [{0}].\n'.format(
        self.workload_identity_pool_id))

  def CheckUpdateWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools describe {pool} --location {location}')
    self.AssertOutputContains('displayName: Updated display name')
    self.AssertOutputContains('name: {0}'.format(
        self.workload_identity_pool_name))
    self.AssertOutputContains('state: ACTIVE')

  def DeleteWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools delete {pool} --location {location} -q')
    self.AssertErrContains('Deleted WorkloadIdentityPool')
    self.AssertErrContains(self.workload_identity_pool_id)

  def UndeleteWorkloadIdentityPool(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools undelete {pool} --location {location}')
    self.AssertOutputContains('name: {0}'.format(
        self.workload_identity_pool_name))

  def CheckUndeleteWorkloadIdentityPoolOperation(self):
    operation_name_match = re.search(r'name: (.+)', self.GetOutput())
    if not operation_name_match:
      self.fail('Couldn\'t find an operation name')
    operation_name = operation_name_match.group(1)
    self.RunFormat('iam workload-identity-pools operations describe {0}',
                   operation_name)
    self.AssertOutputContains('name: {0}'.format(operation_name))

  def CreateAwsWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers create-aws {0} --workload-identity-pool {pool} --location {location} '
        '--account-id "123456789012"', self.aws_provider_id)
    self.AssertErrEquals('Created WorkloadIdentityPoolProvider [{0}].\n'.format(
        self.aws_provider_id))
    self.AssertOutputEquals('')

  def UpdateAwsWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers update-aws {0} --workload-identity-pool {pool} --location {location} '
        '--account-id "123456789000"', self.aws_provider_id)
    self.AssertErrEquals('Updated WorkloadIdentityPoolProvider [{0}].\n'.format(
        self.aws_provider_id))

  def CheckUpdateAwsWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers describe {0} --workload-identity-pool {pool} --location {location}',
        self.aws_provider_id)
    self.AssertOutputContains('aws:')
    self.AssertOutputContains('  accountId: \'123456789000\'')
    self.AssertOutputContains('name: {0}'.format(self.aws_provider_name))
    self.AssertOutputContains('state: ACTIVE')

  def CreateOidcWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers create-oidc {0} --workload-identity-pool {pool} --location {location} '
        '--issuer-uri "https://www.test.com" --attribute-mapping "google.subject=1"',
        self.oidc_provider_id)
    self.AssertErrEquals('Created WorkloadIdentityPoolProvider [{0}].\n'.format(
        self.oidc_provider_id))
    self.AssertOutputEquals('')

  def UpdateOidcWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers update-oidc {0} --workload-identity-pool {pool} --location {location} '
        '--issuer-uri "https://www.another-test.com"', self.oidc_provider_id)
    self.AssertErrEquals('Updated WorkloadIdentityPoolProvider [{0}].\n'.format(
        self.oidc_provider_id))

  def CheckUpdateOidcWorkloadIdentityPoolProvider(self):
    time.sleep(5)  # Wait for sync to regional storage
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers describe {0} --workload-identity-pool {pool} --location {location}',
        self.oidc_provider_id)
    self.AssertOutputContains('attributeMapping:')
    self.AssertOutputContains('  google.subject: \'1\'')
    self.AssertOutputContains('name: {0}'.format(self.oidc_provider_name))
    self.AssertOutputContains('oidc:')
    self.AssertOutputContains('  issuerUri: https://www.another-test.com')
    self.AssertOutputContains('state: ACTIVE')

  def DescribeWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers describe {0} --workload-identity-pool {pool} --location {location}',
        self.aws_provider_id)
    self.AssertOutputContains('aws:')
    self.AssertOutputContains('  accountId: \'123456789012\'')
    self.AssertOutputContains('name: {0}'.format(self.aws_provider_name))
    self.AssertOutputContains('state: ACTIVE')

  def ListWorkloadIdentityPoolProviders(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers list --workload-identity-pool {pool} --location {location}'
    )
    self.AssertOutputContains('name: {0}'.format(self.aws_provider_name))
    self.AssertOutputContains('name: {0}'.format(self.oidc_provider_name))

  def DeleteWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers delete {0} --workload-identity-pool {pool} --location {location}  -q',
        self.aws_provider_id)
    self.AssertErrContains('Deleted WorkloadIdentityPoolProvider')
    self.AssertErrContains(self.aws_provider_id)

  def UndeleteWorkloadIdentityPoolProvider(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam workload-identity-pools providers undelete {0} --workload-identity-pool {pool} --location {location}',
        self.aws_provider_id)
    self.AssertOutputContains('name: {0}'.format(self.aws_provider_name))

  def CheckUndeleteWorkloadIdentityPoolProviderOperation(self):
    operation_name_match = re.search(r'name: (.+)', self.GetOutput())
    if not operation_name_match:
      self.fail('Couldn\'t find an operation name')
    operation_name = operation_name_match.group(1)
    self.RunFormat(
        'iam workload-identity-pools providers operations describe {0}',
        operation_name)
    self.AssertOutputContains('name: {0}'.format(operation_name))
