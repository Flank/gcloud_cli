# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

import copy
import os

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import cloud_storage_util


class GetObjectTest(sdk_test_base.SdkBase):

  _BUCKET_NAME = 'mybucket'
  _OBJECT_NAME = 'myobject'
  _OBJECT = storage_util.ObjectReference.FromUrl(
      'gs://{bucket}/{object}'.format(
          bucket=_BUCKET_NAME, object=_OBJECT_NAME))

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

  def testGetObject(self):
    self.apitools_client.objects.Get.Expect(
        self.storage_msgs.StorageObjectsGetRequest(
            bucket=self._BUCKET_NAME, object=self._OBJECT_NAME),
        self.storage_msgs.Object(name=self._OBJECT_NAME))

    self.assertEqual(
        self.storage_client.GetObject(self._OBJECT),
        self.storage_msgs.Object(name=self._OBJECT_NAME))


class CopyFileTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

    self.object_name = 'foobar'
    self.target_path = 'mytargetpath'
    self.bucket_name = 'mybucket'
    self.bucket_reference = storage_util.BucketReference.FromUrl(
        'gs://{bucket}/'.format(bucket=self.bucket_name))
    self.target_ref = storage_util.ObjectReference.FromBucketRef(
        self.bucket_reference, self.target_path)
    self.local_path = self.Touch(
        self.temp_path, self.object_name, contents='somecontentshere')
    self.file_size = os.path.getsize(self.local_path)
    self.insert_request = self.storage_msgs.StorageObjectsInsertRequest(
        bucket=self.bucket_reference.bucket,
        name=self.target_path,
        object=self.storage_msgs.Object(size=self.file_size)
    )

  def testSuccess(self):
    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        self.storage_msgs.Object(size=self.file_size)
    )
    self.storage_client.CopyFileToGCS(self.local_path, self.target_ref)

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        exception=exception
    )

    with self.assertRaisesRegex(
        storage_api.UploadError,
        r'400 Could not upload file \[.*{object}\] to '
        r'\[{bucket}/{_target_path}\]: Invalid request.'.
        format(object=self.object_name, bucket=self.bucket_name,
               _target_path=self.target_path)):
      self.storage_client.CopyFileToGCS(self.local_path, self.target_ref)

  def testBucketNotFoundError(self):
    exception = http_error.MakeHttpError(code=404, message='Not found')

    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        exception=exception
    )

    with self.assertRaisesRegex(
        storage_api.BucketNotFoundError,
        r'Could not upload file: \[{bucket}\] bucket does not exist.'.
        format(bucket=self.bucket_name)):
      self.storage_client.CopyFileToGCS(self.local_path, self.target_ref)

  def testSizeMismatch(self):
    self.apitools_client.objects.Insert.Expect(
        self.insert_request,
        # Return an object with a different size.
        self.storage_msgs.Object(size=self.file_size - 1)
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileToGCS(self.local_path, self.target_ref)


class CopyFileFromGCSTest(sdk_test_base.WithFakeAuth):

  _BUCKET = storage_util.BucketReference.FromUrl('gs://mybucket/')

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = self.apitools_client.MESSAGES_MODULE

    self.object_name = 'foobar'
    self.target_path = 'mytargetpath'
    self.target_ref = storage_util.ObjectReference.FromBucketRef(
        CopyFileFromGCSTest._BUCKET, self.target_path)
    self.local_path = os.path.join(self.temp_path, self.object_name)
    self.get_request = self.storage_msgs.StorageObjectsGetRequest(
        bucket=self._BUCKET.bucket,
        object=self.target_path)

  def testSuccess(self):
    # TODO(b/33202933): There's a TODO in the apitools testing code to add
    # support for upload/download in mocked apitools clients; when that is
    # resolved, test a non-empty mocked file here.
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = self.storage_msgs.Object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        self.storage_msgs.Object(size=0))
    self.storage_client.CopyFileFromGCS(self.target_ref, self.local_path)

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Get.Expect(
        self.get_request,
        exception=exception
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileFromGCS(self.target_ref, self.local_path)

  def testSizeMismatch(self):
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = self.storage_msgs.Object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        # Return an object with a different size.
        self.storage_msgs.Object(size=-1))

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.CopyFileFromGCS(self.target_ref, self.local_path)


class ReadObjectTest(sdk_test_base.WithFakeAuth):

  _BUCKET_NAME = 'bucket'
  _OBJECT_NAME = 'object'
  _OBJECT = storage_util.ObjectReference.FromUrl(
      'gs://{bucket}/{object}'.format(bucket=_BUCKET_NAME, object=_OBJECT_NAME))

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)
    self.storage_msgs = self.apitools_client.MESSAGES_MODULE

    self.get_request = self.storage_msgs.StorageObjectsGetRequest(
        bucket=self._BUCKET_NAME,
        object=self._OBJECT_NAME)

  def testSuccess(self):
    # TODO(b/33202933): There's a TODO in the apitools testing code to add
    # support for upload/download in mocked apitools clients; when that is
    # resolved, test a non-empty mocked file here.
    # Use object() instead of None because when the mock is given None, it uses
    # a real client
    response = self.storage_msgs.Object()
    self.apitools_client.objects.Get.Expect(
        self.get_request,
        response)
    self.assertEqual(self.storage_client.ReadObject(self._OBJECT).read(), b'')

  def testApiError(self):
    exception = http_error.MakeHttpError()

    self.apitools_client.objects.Get.Expect(
        self.get_request,
        exception=exception
    )

    with self.assertRaises(exceptions.BadFileException):
      self.storage_client.ReadObject(self._OBJECT)


class ListBucketTest(cloud_storage_util.WithGCSCalls, sdk_test_base.SdkBase):

  _BUCKET_NAME = 'testbucket'

  _SHA1_SUMS = {
      'content': '040f06fd774092478d450774f5ba30c5da78acc8',
      'content2': '6dc99d4757bcb35eaaf4cd3cb7907189fab8d254',
      'content3': '32c5ff3108bcea43b1c4826d66f43a3ae570e663'
  }

  def SetUp(self):
    self.bucket = storage_util.BucketReference.FromUrl(
        'gs://{0}/'.format(self._BUCKET_NAME))

  def testListBucket(self):
    self.ExpectList([('a', 'content'), ('b', 'content'), ('c', 'content2')])
    storage_client = storage_api.StorageClient()

    names = set(o.name for o in storage_client.ListBucket(self.bucket))
    self.assertEqual(
        names,
        set([self._SHA1_SUMS['content'], self._SHA1_SUMS['content2']]))

  def testListBucketMultiplePages(self):
    self.ExpectListMulti([
        [('a', 'content'), ('b', 'content')],
        [('c', 'content2'), ('d', 'content3')]])
    storage_client = storage_api.StorageClient()
    names = set(o.name for o in storage_client.ListBucket(self.bucket))
    self.assertEqual(
        names,
        set([self._SHA1_SUMS['content'], self._SHA1_SUMS['content2'],
             self._SHA1_SUMS['content3']]))

  def testApiError(self):
    exception = http_error.MakeHttpError()
    self.ExpectListException(exception)
    storage_client = storage_api.StorageClient()

    with self.assertRaisesRegex(
        storage_api.ListBucketError,
        r'400 Could not list bucket \[{bucket}\]: Invalid request.'.
        format(bucket=self._BUCKET_NAME)):
      list(storage_client.ListBucket(self.bucket))

  def testBucketNotFoundError(self):
    exception = http_error.MakeHttpError(code=404)
    self.ExpectListException(exception)
    storage_client = storage_api.StorageClient()

    with self.assertRaisesRegex(
        storage_api.BucketNotFoundError,
        r'Could not list bucket: \[{bucket}\] bucket does not exist.'.
        format(bucket=self._BUCKET_NAME)):
      list(storage_client.ListBucket(self.bucket))


class DeleteBucketTest(test_case.TestCase):

  _BUCKET_NAME = 'testbucket'

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

    self.storage_client = storage_api.StorageClient(self.apitools_client)

  def testDeleteBucket(self):
    bucket = storage_util.BucketReference.FromUrl(
        'gs://{bucket}/'.format(bucket=self._BUCKET_NAME))
    self.apitools_client.buckets.Delete.Expect(
        self.apitools_client.MESSAGES_MODULE.StorageBucketsDeleteRequest(
            bucket=self._BUCKET_NAME),
        self.apitools_client.MESSAGES_MODULE.StorageBucketsDeleteResponse()
    )

    self.storage_client.DeleteBucket(bucket)


class GetBucketLocationForFileTest(e2e_base.WithMockHttp):

  _BUCKET_NAME = 'testbucket'
  _FILE_NAME = 'testfile'
  _BUCKET_LOCATION = 'EUROPE-NORTH-1'
  _FILE_PATH = 'gs://{bucket}/{file}'.format(
      bucket=_BUCKET_NAME, file=_FILE_NAME)

  def SetUp(self):
    self.mocked_storage_v1 = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

  def testGetBucketLocationForFileSuccess(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        response=self.storage_v1_messages.Bucket(
            name=self._BUCKET_NAME,
            location=self._BUCKET_LOCATION,
        ),
    )

    client = storage_api.StorageClient()
    location = client.GetBucketLocationForFile(self._FILE_PATH)
    self.assertEqual(location, self._BUCKET_LOCATION)

  def testGetBucketLocationForNonExistentFile(self):
    exception = http_error.MakeHttpError(code=404)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=exception,
    )
    with self.assertRaisesRegex(
        storage_api.BucketNotFoundError,
        r'Could not get location for file: '
        r'\[{bucket}\] bucket does not exist.'.
        format(bucket=self._BUCKET_NAME)):
      client = storage_api.StorageClient()
      client.GetBucketLocationForFile(self._FILE_PATH)


class GetBucketTest(e2e_base.WithMockHttp):

  _BUCKET_NAME = 'testbucket'

  def SetUp(self):
    self.mocked_storage_v1 = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule('storage', 'v1')

  def testReturnsExistingBucket(self):
    """Gets a bucket that exists."""
    existing_bucket = self.storage_v1_messages.Bucket(id=self._BUCKET_NAME)
    self.mocked_storage_v1.buckets.Get.Expect(
        request=self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        response=existing_bucket)
    client = storage_api.StorageClient()
    bucket = client.GetBucket(self._BUCKET_NAME)
    self.assertEqual(bucket, existing_bucket)

  def testAcceptsFullProjection(self):
    """Gets a bucket with 'full' projection mode."""
    existing_bucket = self.storage_v1_messages.Bucket(id=self._BUCKET_NAME)
    self.mocked_storage_v1.buckets.Get.Expect(
        request=self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME,
            projection=self.storage_v1_messages.StorageBucketsGetRequest
            .ProjectionValueValuesEnum.full),
        response=existing_bucket)
    client = storage_api.StorageClient()
    bucket = client.GetBucket(
        self._BUCKET_NAME, self.storage_v1_messages.StorageBucketsGetRequest
        .ProjectionValueValuesEnum.full)
    self.assertEqual(bucket, existing_bucket)

  def testErrorForNonexistentBucket(self):
    """Raises an error for a nonexistent bucket."""
    self.mocked_storage_v1.buckets.Get.Expect(
        request=self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    client = storage_api.StorageClient()

    with self.assertRaises(storage_api.BucketNotFoundError):
      client.GetBucket(self._BUCKET_NAME)


class CreateBucketIfNotExistsTest(e2e_base.WithMockHttp):

  _BUCKET_NAME = 'testbucket'
  _PROJECT_ID = 'project-id'
  _BUCKET_LOCATION = 'eu'

  def SetUp(self):
    self.mocked_storage_v1 = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

  def testAlreadyExists(self):
    """Bucket already exists."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        response=self.storage_v1_messages.Bucket(id=self._BUCKET_NAME))
    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID)

  def testCreateBucket(self):
    """Bucket doesn't exist and must be created."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
            ),
            project=self._PROJECT_ID,
        ),
        response=self.storage_v1_messages.Bucket(id=self._BUCKET_NAME))
    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID)

  def testCreateBucketLocation(self):
    """Bucket doesn't exist and must be created (in specified location)."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
                location=self._BUCKET_LOCATION,
            ),
            project=self._PROJECT_ID,
        ),
        response=self.storage_v1_messages.Bucket(id=self._BUCKET_NAME))
    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID,
                                   location=self._BUCKET_LOCATION)

  def testCreateBucketRace(self):
    """Bucket doesn't exist, but creating it results in conflict due to race."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
            ),
            project=self._PROJECT_ID,
        ),
        exception=http_error.MakeHttpError(code=409))
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        response=self.storage_v1_messages.Bucket(id=self._BUCKET_NAME))
    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID)

  def testCreateBucketRaceNotOwned(self):
    """Bucket is created by another process, but is not accessible."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
            ),
            project=self._PROJECT_ID,
        ),
        exception=http_error.MakeHttpError(code=409))
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=403,
                                           message='Permission denied'))
    client = storage_api.StorageClient()
    with self.assertRaisesRegex(api_exceptions.HttpError, 'Permission denied'):
      client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID)

  def testCreateBucketInvalidLocation(self):
    """Bucket doesn't exist and must be created (in bad location)."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
                location='bad',
            ),
            project=self._PROJECT_ID,
        ),
        exception=http_error.MakeHttpError(code=400, message='Invalid value'))
    client = storage_api.StorageClient()
    with self.assertRaisesRegex(api_exceptions.HttpError, 'Invalid value'):
      client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID,
                                     location='bad')

  def testCreateBucketDenied(self):
    """Bucket doesn't exist and we don't have permission to create it."""
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=self._BUCKET_NAME),
        exception=http_error.MakeHttpError(code=404))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=self._BUCKET_NAME,
            ),
            project=self._PROJECT_ID,
        ),
        exception=http_error.MakeHttpError(
            code=403, message='Permission denied'))
    client = storage_api.StorageClient()
    with self.assertRaisesRegex(api_exceptions.HttpError, 'Permission denied'):
      client.CreateBucketIfNotExists(self._BUCKET_NAME, self._PROJECT_ID)


class BucketIamPolicyTest(e2e_base.WithMockHttp):

  _BUCKET_NAME = 'testbucket'
  _PROJECT_ID = 'project-id'

  def SetUp(self):
    self.mocked_storage_v1 = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule('storage', 'v1')

    self.bucket_reference = storage_util.BucketReference(self._BUCKET_NAME)

  def testGetIamPolicy(self):
    expected_policy = self.storage_v1_messages.Policy(
        kind='storage#policy',
        resourceId='projects/_/buckets/{}'.format(self._BUCKET_NAME),
        version=1,
        etag=b'CAE3',
        bindings=[
            self.storage_v1_messages.Policy.BindingsValueListEntry(
                role='roles/storage.legacyBucketOwner',
                members=[
                    'projectEditor:{}'.format(self._PROJECT_ID),
                    'projectOwner:{}'.format(self._PROJECT_ID),
                ]),
        ])
    self.mocked_storage_v1.buckets.GetIamPolicy.Expect(
        request=self.storage_v1_messages.StorageBucketsGetIamPolicyRequest(
            bucket=self._BUCKET_NAME, optionsRequestedPolicyVersion=3),
        response=expected_policy)

    client = storage_api.StorageClient()
    actual_policy = client.GetIamPolicy(self.bucket_reference)
    self.assertEqual(actual_policy, expected_policy)

  def testSetIamPolicy(self):
    new_policy = self.storage_v1_messages.Policy(
        kind='storage#policy',
        resourceId='projects/_/buckets/{}'.format(self._BUCKET_NAME),
        version=3,
        bindings=[
            self.storage_v1_messages.Policy.BindingsValueListEntry(
                role='roles/storage.objectAdmin',
                members=[
                    'user:test-user@gmail.com',
                ]),
        ])
    expected_policy = copy.deepcopy(new_policy)
    expected_policy.etag = b'CAE4'
    self.mocked_storage_v1.buckets.SetIamPolicy.Expect(
        request=self.storage_v1_messages.StorageBucketsSetIamPolicyRequest(
            bucket=self._BUCKET_NAME, policy=new_policy),
        response=expected_policy)

    client = storage_api.StorageClient()
    actual_policy = client.SetIamPolicy(self.bucket_reference, new_policy)
    self.assertEqual(actual_policy, expected_policy)

  def testAddIamPolicyBinding(self):
    old_policy = self.storage_v1_messages.Policy(
        kind='storage#policy',
        resourceId='projects/_/buckets/{}'.format(self._BUCKET_NAME),
        version=1,
        etag=b'CAE3',
        bindings=[
            self.storage_v1_messages.Policy.BindingsValueListEntry(
                role='roles/storage.legacyBucketOwner',
                members=[
                    'projectEditor:{}'.format(self._PROJECT_ID),
                    'projectOwner:{}'.format(self._PROJECT_ID),
                ]),
        ])

    # IAM utils always sets the policy version to the latest available.
    new_policy = copy.deepcopy(old_policy)
    new_policy.version = 3
    new_policy.bindings.append(
        self.storage_v1_messages.Policy.BindingsValueListEntry(
            role='roles/storage.objectAdmin',
            members=['user:test-user@gmail.com']))

    # ETAG should be updated after SetIamPolicy.
    expected_policy = copy.deepcopy(new_policy)
    expected_policy.etag = b'CAE4'
    self.mocked_storage_v1.buckets.GetIamPolicy.Expect(
        request=self.storage_v1_messages.StorageBucketsGetIamPolicyRequest(
            bucket=self._BUCKET_NAME, optionsRequestedPolicyVersion=3),
        response=old_policy)
    self.mocked_storage_v1.buckets.SetIamPolicy.Expect(
        self.storage_v1_messages.StorageBucketsSetIamPolicyRequest(
            bucket=self._BUCKET_NAME, policy=new_policy),
        response=expected_policy)

    client = storage_api.StorageClient()
    actual_policy = client.AddIamPolicyBinding(self.bucket_reference,
                                               'user:test-user@gmail.com',
                                               'roles/storage.objectAdmin')
    self.assertEqual(actual_policy, expected_policy)


if __name__ == '__main__':
  test_case.main()
