# -*- coding: utf-8 -*- #
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
"""Tests for the Diagnose Utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.compute.diagnose import diagnose_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib.surface.compute import test_base


class DiagnoseUtilsTest(test_base.BaseTest):

  def SetUp(self):
    """Called by base class's SetUp() method, which does additional mocking."""
    self.SelectApi('v1')

    self._mock_compute_client = self._MockClient('compute', 'v1')
    self._mock_iam_client = self._MockClient('iam', 'v1')
    self._mock_storage_client = self._MockClient('storage', 'v1')

    self.diagnose_client = diagnose_utils.DiagnoseClient(
        compute_client=self._mock_compute_client,
        iam_client=self._mock_iam_client,
        storage_client=self._mock_storage_client)

  def _MockClient(self, client_name, version):
    """Mocks a specific client for the duration of a test.

    Cleans the mock up after the test is completed.

    Args:
      client_name: The name of the api to mock.
      version: The version string to reference for the mock.

    Returns:
      A mock class that can override functionality of the underlying api, and
      specify expected inputs.
    """
    client = mock.Client(
        client_class=core_apis.GetClientClass(client_name, version))
    client.Mock()
    self.addCleanup(client.Unmock)
    return client

  def testSignBlob(self):
    messages = self._mock_iam_client.MESSAGES_MODULE
    test_account = 'test-account@google.com'
    bytes_to_sign = b'Hello'
    signature = b'World'

    self._mock_iam_client.projects_serviceAccounts.SignBlob.Expect(
        request=messages.IamProjectsServiceAccountsSignBlobRequest(
            name='projects/-/serviceAccounts/{}'.format(test_account),
            signBlobRequest=messages.SignBlobRequest(
                bytesToSign=bytes_to_sign)),
        response=messages.SignBlobResponse(signature=signature))

    response = self.diagnose_client.SignBlob(test_account, bytes_to_sign)
    self.assertEquals(signature, response)

  def testListServiceAccounts(self):
    messages = self._mock_iam_client.MESSAGES_MODULE
    project = 'my-project'
    accounts = [messages.ServiceAccount(email='test-account@google.com')]

    self._mock_iam_client.projects_serviceAccounts.List.Expect(
        request=messages.IamProjectsServiceAccountsListRequest(
            name='projects/{}'.format(project)),
        response=messages.ListServiceAccountsResponse(accounts=accounts))

    response = self.diagnose_client.ListServiceAccounts(project)
    self.assertEquals(accounts, response)

  def testCreateServiceAccount(self):
    messages = self._mock_iam_client.MESSAGES_MODULE
    project = 'my-project'
    account_id = 'test-account'
    account_email = 'test-account@google.com'

    self._mock_iam_client.projects_serviceAccounts.Create.Expect(
        request=messages.IamProjectsServiceAccountsCreateRequest(
            name='projects/{}'.format(project),
            createServiceAccountRequest=messages.CreateServiceAccountRequest(
                accountId=account_id)),
        response=messages.ServiceAccount(email=account_email))

    response = self.diagnose_client.CreateServiceAccount(project, account_id)
    self.assertEquals(account_email, response)

  def testFindBucketWithNoResults(self):
    messages = self._mock_storage_client.MESSAGES_MODULE
    project = 'my-project'
    prefix = 'test'
    matching_buckets = []

    self._mock_storage_client.buckets.List.Expect(
        request=messages.StorageBucketsListRequest(
            prefix=prefix, project=project),
        response=messages.Buckets(items=matching_buckets))

    response = self.diagnose_client.FindBucket(project, prefix)
    self.assertEquals(None, response)

  def testFindBucketWithManyResults(self):
    messages = self._mock_storage_client.MESSAGES_MODULE
    project = 'my-project'
    prefix = 'test'
    matching_buckets = [
        messages.Bucket(name='bucket-1'),
        messages.Bucket(name='bucket-2'),
        messages.Bucket(name='bucket-3'),
        messages.Bucket(name='bucket-4')
    ]

    self._mock_storage_client.buckets.List.Expect(
        request=messages.StorageBucketsListRequest(
            prefix=prefix, project=project),
        response=messages.Buckets(items=matching_buckets))

    response = self.diagnose_client.FindBucket(project, prefix)
    self.assertEquals(matching_buckets[0], response)

  def testCreateBucketWithLifecycle(self):
    days = 100

    bucket = self.diagnose_client.CreateBucketWithLifecycle(days_to_live=days)

    bucket_rule = bucket.lifecycle.rule[0]
    self.assertEqual(days, bucket_rule.condition.age)
    self.assertEqual('Delete', bucket_rule.action.type)

  def testInsertBucket(self):
    messages = self._mock_storage_client.MESSAGES_MODULE
    project = 'my-project'
    bucket = messages.Bucket(name='test-bucket')

    self._mock_storage_client.buckets.Insert.Expect(
        request=messages.StorageBucketsInsertRequest(
            bucket=bucket, project=project),
        response=bucket)

    self.diagnose_client.InsertBucket(project, bucket)

  def testUpdateMetadata(self):
    messages = self._mock_compute_client.MESSAGES_MODULE
    project = 'my-project'
    zone = 'us-east'
    instance = 'my-instance'
    key = 'test-key'
    val = 'test-value'
    instance_ref = resources.REGISTRY.Create(
        'compute.instances', instance=instance, zone=zone, project=project)

    self._mock_compute_client.instances.Get.Expect(
        request=messages.ComputeInstancesGetRequest(
            project=project, zone=zone, instance=instance),
        response=messages.Instance(
            name=instance,
            metadata=messages.Metadata(items=[
                messages.Metadata.ItemsValueListEntry(
                    key='old-key', value='old')
            ])))

    self._mock_compute_client.instances.SetMetadata.Expect(
        request=messages.ComputeInstancesSetMetadataRequest(
            instance=instance,
            metadata=messages.Metadata(items=[
                messages.Metadata.ItemsValueListEntry(
                    key='old-key', value='old'),
                messages.Metadata.ItemsValueListEntry(
                    key='test-key', value='test-value')
            ]),
            project=project,
            zone=zone),
        response=messages.Operation())

    self.diagnose_client.UpdateMetadata(project, instance_ref, key, val)
