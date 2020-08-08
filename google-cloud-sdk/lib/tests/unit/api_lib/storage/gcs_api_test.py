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
"""Tests for googlecloudsdk.api_lib.storage.storage_api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import gcs_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util

import mock


TEST_ACCOUNT = 'fake-account'
TEST_BUCKET = 'fake-bucket'
TEST_OBJECT = 'fake-object'
TEST_PROJECT = 'fake-project'


class GetBucketTest(cloud_storage_util.WithGCSCalls, parameterized.TestCase,
                    sdk_test_base.SdkBase):

  _BUCKET_NAMES = ['Bucket1', 'Bucket2', 'Bucket3']

  def SetUp(self):
    properties.VALUES.core.account.Set(TEST_ACCOUNT)
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageBucketsGetRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.gcs_client = gcs_api.GcsApi()

  def test_get_bucket(self):
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(
            bucket=TEST_BUCKET, projection=self.default_projection),
        response=self.messages.Bucket())

    self.gcs_client.GetBucket(TEST_BUCKET)

  def test_get_bucket_invalid_fields_scope(self):
    with self.assertRaises(ValueError):
      self.gcs_client.GetBucket(TEST_BUCKET, fields_scope='football field')

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 'noAcl', 'name,size'),
      (cloud_api.FieldsScope.NO_ACL, 'noAcl', None),
      (cloud_api.FieldsScope.FULL, 'full', None))
  def test_get_bucket_valid_fields_scope(self, fields_scope, projection,
                                         fields):

    request = self.messages.StorageBucketsGetRequest(
        bucket=TEST_BUCKET,
        projection=getattr(self.messages.StorageBucketsGetRequest
                           .ProjectionValueValuesEnum, projection))
    global_params = self.messages.StandardQueryParameters()
    global_params.fields = fields

    with mock.patch.object(self.apitools_client.buckets, 'Get') as mock_get:
      self.gcs_client.GetBucket(TEST_BUCKET, fields_scope=fields_scope)

      # Checks for correct projection value inside request.
      # Checks for correct fields value inside global_params.
      mock_get.assert_called_once_with(request, global_params=global_params)


class ListBucketsTest(cloud_storage_util.WithGCSCalls, parameterized.TestCase,
                      sdk_test_base.SdkBase):

  _BUCKET_NAMES = ['Bucket1', 'Bucket2', 'Bucket3']

  def SetUp(self):
    properties.VALUES.core.account.Set(TEST_ACCOUNT)
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageBucketsListRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.gcs_client = gcs_api.GcsApi()

  def test_list_buckets(self):
    buckets = self.messages.Buckets(items=[self.messages.Bucket(name=name)
                                           for name in self._BUCKET_NAMES])
    self.apitools_client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(
            project=TEST_PROJECT, projection=self.default_projection),
        response=buckets
    )

    names = [b.name for b in self.gcs_client.ListBuckets()]
    self.assertCountEqual(names, self._BUCKET_NAMES)

  def test_list_buckets_invalid_fields_scope(self):
    with self.assertRaises(ValueError):
      list(self.gcs_client.ListBuckets(fields_scope='football field'))

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 'noAcl', 'name,size'),
      (cloud_api.FieldsScope.NO_ACL, 'noAcl', None),
      (cloud_api.FieldsScope.FULL, 'full', None))
  def test_list_buckets_valid_fields_scope(self, fields_scope, projection,
                                           fields):

    request = self.messages.StorageBucketsListRequest(
        project=TEST_PROJECT,
        projection=getattr(self.messages.StorageBucketsListRequest
                           .ProjectionValueValuesEnum, projection))
    global_params = self.messages.StandardQueryParameters()
    global_params.fields = fields

    with mock.patch.object(list_pager, 'YieldFromList') as mock_yield_from_list:
      list(self.gcs_client.ListBuckets(fields_scope))

      # Checks for correct projection value inside request.
      # Checks for correct fields value inside global_params.
      mock_yield_from_list.assert_called_once_with(
          self.apitools_client.buckets,
          request,
          batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
          global_params=global_params)


class ListObjectsTest(cloud_storage_util.WithGCSCalls, parameterized.TestCase,
                      sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.account.Set(TEST_ACCOUNT)
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageObjectsListRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.gcs_client = gcs_api.GcsApi()

  def test_list_objects(self):
    file_list = ['content', 'content', 'content2']
    objects = self.messages.Objects(
        items=[self.messages.Object(name=c) for c in file_list])

    self.apitools_client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(
            bucket=TEST_BUCKET,
            projection=self.default_projection),
        response=objects
    )

    names = [o.name for o in self.gcs_client.ListObjects(TEST_BUCKET)]
    self.assertCountEqual(names, file_list)

  def test_list_objects_invalid_fields_scope(self):
    with self.assertRaises(ValueError):
      list(self.gcs_client.ListObjects(TEST_BUCKET,
                                       fields_scope='football field'))

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 'noAcl', 'name,size'),
      (cloud_api.FieldsScope.NO_ACL, 'noAcl', None),
      (cloud_api.FieldsScope.FULL, 'full', None))
  def test_list_objects_valid_fields_scope(self, fields_scope, projection,
                                           fields):
    request = self.messages.StorageObjectsListRequest(
        bucket=TEST_BUCKET,
        projection=getattr(self.messages.StorageObjectsListRequest
                           .ProjectionValueValuesEnum, projection))

    with mock.patch.object(list_pager, 'YieldFromList') as mock_yield_from_list:
      list(self.gcs_client.ListObjects(TEST_BUCKET,
                                       fields_scope=fields_scope))

      global_params = self.messages.StandardQueryParameters()
      global_params.fields = fields
      # Checks for correct projection value inside request.
      # Checks for correct fields value inside global_params.
      mock_yield_from_list.assert_called_once_with(
          self.apitools_client.objects,
          request,
          batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
          global_params=global_params)


class GetObjectMetadataTest(cloud_storage_util.WithGCSCalls,
                            parameterized.TestCase, sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.account.Set(TEST_ACCOUNT)
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageObjectsGetRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.gcs_client = gcs_api.GcsApi()

  def test_get_object_metadata(self):
    request = self.messages.StorageObjectsGetRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        projection=self.default_projection)
    self.apitools_client.objects.Get.Expect(request,
                                            response=self.messages.Object())

    self.gcs_client.GetObjectMetadata(TEST_BUCKET, TEST_OBJECT)

  def test_get_object_metadata_generation(self):
    request = self.messages.StorageObjectsGetRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        generation=1,
        projection=self.default_projection)
    self.apitools_client.objects.Get.Expect(request,
                                            response=self.messages.Object())

    self.gcs_client.GetObjectMetadata(TEST_BUCKET,
                                      TEST_OBJECT,
                                      generation=1)

  def test_get_object_metadata_invalid_fields_scope(self):
    with self.assertRaises(ValueError):
      self.gcs_client.GetObjectMetadata(TEST_BUCKET, TEST_OBJECT,
                                        fields_scope='football field')

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 'noAcl', 'name,size'),
      (cloud_api.FieldsScope.NO_ACL, 'noAcl', None),
      (cloud_api.FieldsScope.FULL, 'full', None))
  def test_get_object_metadata_valid_fields_scope(self, fields_scope,
                                                  projection, fields):
    request = self.messages.StorageObjectsGetRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        projection=getattr(self.messages.StorageObjectsGetRequest
                           .ProjectionValueValuesEnum, projection))

    with mock.patch.object(self.apitools_client.objects, 'Get') as mock_get:
      self.gcs_client.GetObjectMetadata(TEST_BUCKET, TEST_OBJECT,
                                        fields_scope=fields_scope)

      global_params = self.messages.StandardQueryParameters()
      global_params.fields = fields
      # Checks for correct projection value inside request.
      # Checks for correct fields value inside global_params.
      mock_get.assert_called_once_with(request, global_params=global_params)


class PatchObjectMetadataTest(cloud_storage_util.WithGCSCalls,
                              parameterized.TestCase, sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.account.Set(TEST_ACCOUNT)
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.patched_object = self.messages.Object()
    self.default_projection = (self.messages.StorageObjectsPatchRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.gcs_client = gcs_api.GcsApi()

  def test_patch_object_metadata(self):
    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        projection=self.default_projection)
    self.apitools_client.objects.Patch.Expect(request,
                                              response=self.patched_object)

    self.gcs_client.PatchObjectMetadata(
        TEST_BUCKET,
        TEST_OBJECT,
        self.patched_object)

  def test_patch_object_metadata_generation(self):
    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        generation=1,
        projection=self.default_projection)
    self.apitools_client.objects.Patch.Expect(request,
                                              response=self.patched_object)

    self.gcs_client.PatchObjectMetadata(TEST_BUCKET,
                                        TEST_OBJECT,
                                        self.patched_object,
                                        generation=1)

  def test_patch_object_metadata_precondition_generation_match(self):
    precondition_generation_match = 1
    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        ifGenerationMatch=precondition_generation_match,
        projection=self.default_projection)
    self.apitools_client.objects.Patch.Expect(request,
                                              response=self.patched_object)

    self.gcs_client.PatchObjectMetadata(
        TEST_BUCKET,
        TEST_OBJECT,
        self.patched_object,
        request_config=gcs_api.GcsRequestConfig(
            precondition_generation_match=precondition_generation_match))

  def test_patch_object_metadata_precondition_metageneration_match(self):
    precondition_metageneration_match = 1
    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        ifMetagenerationMatch=precondition_metageneration_match,
        projection=self.default_projection)
    self.apitools_client.objects.Patch.Expect(request,
                                              response=self.patched_object)

    self.gcs_client.PatchObjectMetadata(
        TEST_BUCKET,
        TEST_OBJECT,
        self.patched_object,
        request_config=gcs_api.GcsRequestConfig(
            precondition_metageneration_match=precondition_metageneration_match)
        )

  def test_patch_object_metadata_predefined_acl_string(self):
    predefined_acl_string = 'authenticatedRead'
    predefined_acl = getattr(
        self.messages.StorageObjectsPatchRequest.PredefinedAclValueValuesEnum,
        predefined_acl_string)

    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        predefinedAcl=predefined_acl,
        projection=self.default_projection)
    self.apitools_client.objects.Patch.Expect(request,
                                              response=self.messages.Object())

    request_config = gcs_api.GcsRequestConfig(
        predefined_acl_string=predefined_acl_string)
    self.gcs_client.PatchObjectMetadata(
        TEST_BUCKET,
        TEST_OBJECT,
        self.patched_object,
        request_config=request_config)

  def test_patch_object_metadata_invalid_fields_scope(self):
    with self.assertRaises(ValueError):
      self.gcs_client.PatchObjectMetadata(TEST_BUCKET, TEST_OBJECT,
                                          self.patched_object,
                                          fields_scope='football field')

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 'noAcl', 'name,size'),
      (cloud_api.FieldsScope.NO_ACL, 'noAcl', None),
      (cloud_api.FieldsScope.FULL, 'full', None))
  def test_patch_object_metadata_valid_fields_scope(self, fields_scope,
                                                    projection, fields):
    request = self.messages.StorageObjectsPatchRequest(
        bucket=TEST_BUCKET,
        object=TEST_OBJECT,
        objectResource=self.patched_object,
        projection=getattr(self.messages.StorageObjectsPatchRequest
                           .ProjectionValueValuesEnum, projection))

    with mock.patch.object(self.apitools_client.objects, 'Patch') as mock_patch:
      self.gcs_client.PatchObjectMetadata(TEST_BUCKET, TEST_OBJECT,
                                          self.patched_object,
                                          fields_scope=fields_scope)

      global_params = self.messages.StandardQueryParameters()
      global_params.fields = fields
      # Checks for correct projection value inside request.
      # Checks for correct fields value inside global_params.
      mock_patch.assert_called_once_with(request, global_params=global_params)


if __name__ == '__main__':
  test_case.main()
