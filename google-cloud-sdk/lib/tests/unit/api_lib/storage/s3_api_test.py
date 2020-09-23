# Lint as: python3
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
"""Tests for googlecloudsdk.api_lib.storage.s3_api.S3Api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import datetime
import io
import itertools

import boto3
import botocore
from botocore import stub
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import s3_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.storage import test_base

import mock


BINARY_DATA = b'hey, data is great'
BUCKET_NAME = 'bucket_name'
CONTENT_ENCODING = 'x'
DATE = datetime.datetime(1, 1, 1)
ETAG = 'e'
LAST_MODIFIED = datetime.datetime.strptime('06/12/1999 13:42:10',
                                           '%m/%d/%Y %H:%M:%S')
OBJECT_NAME = 'object_name'
OWNER_ID = 'owner_id'
OWNER_NAME = 'owner_name'
SCHEME = 's3'

GET_BUCKET_API_FUNCTION_NAMES = [
    'get_bucket_location',
    'get_bucket_cors',
    'get_bucket_logging',
    'get_bucket_request_payment',
    'get_bucket_lifecycle_configuration',
    'get_bucket_versioning',
    'get_bucket_website',
    'get_bucket_acl',
]


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetBucketTest(test_base.StorageTestBase, parameterized.TestCase):

  @parameterized.parameters(
      (cloud_api.FieldsScope.SHORT, 1, {'Name': BUCKET_NAME,
                                        'LocationConstraint': ''}),
      (cloud_api.FieldsScope.NO_ACL, 7, {
          'Name': BUCKET_NAME,
          'LocationConstraint': '',
          'CORSRules': [],
          'LifecycleConfiguration': {'Rules': []},
          'LoggingEnabled': {
              'TargetBucket': '', 'TargetGrants': [], 'TargetPrefix': ''},
          'Payer': 'BucketOwner',
          'Versioning': {},
          'Website': {}}),
      (cloud_api.FieldsScope.FULL, 8, {
          'Name': BUCKET_NAME,
          'LocationConstraint': '',
          'CORSRules': [],
          'LifecycleConfiguration': {'Rules': []},
          'LoggingEnabled': {
              'TargetBucket': '', 'TargetGrants': [], 'TargetPrefix': ''},
          'Payer': 'BucketOwner',
          'Versioning': {},
          'Website': {},
          'Owner': {},
          'Grants': []}))
  def test_gets_bucket_with_different_fields_scopes(
      self, fields_scope, number_api_calls, expected_metadata):
    api = s3_api.S3Api()
    stubber = stub.Stubber(api.client)

    # Minimum amount of response data to pass Boto Stubber validation and
    # verify each API endpoint has returned a response.
    get_bucket_api_call_and_response = [
        ('get_bucket_location', {'LocationConstraint': ''}),
        ('get_bucket_cors', {'CORSRules': []}),
        ('get_bucket_logging', {
            'LoggingEnabled': {
                'TargetBucket': '', 'TargetGrants': [], 'TargetPrefix': ''}}),
        ('get_bucket_request_payment', {'Payer': 'BucketOwner'}),
        ('get_bucket_lifecycle_configuration', {'Rules': []}),
        ('get_bucket_versioning', {}),
        ('get_bucket_website', {}),
        ('get_bucket_acl', {'Owner': {}, 'Grants': []})
    ]

    # Don't loop over extra API functions to avoid the Stubber
    # complaining about expected uncalled functions.
    for method, response in get_bucket_api_call_and_response[:number_api_calls]:
      stubber.add_response(method=method,
                           expected_params={'Bucket': BUCKET_NAME},
                           service_response=response)

    expected = resource_reference.BucketResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME), metadata=expected_metadata)
    with stubber:
      observed = api.GetBucket(BUCKET_NAME, fields_scope)
      self.assertEqual(observed, expected)

  @parameterized.parameters(GET_BUCKET_API_FUNCTION_NAMES)
  @mock.patch.object(boto3, 'client')
  def test_gets_bucket_with_individual_api_function_errors(
      self, error_method, mock_get_client):
    mock_client = mock.Mock()
    for method in GET_BUCKET_API_FUNCTION_NAMES:
      # Have non-error API functions return empty dictionaries that dict.update
      # will be called on.
      setattr(mock_client, method, mock.MagicMock(return_value={}))

    # Have specific API function return an error.
    mock_get_client.return_value = mock_client
    setattr(getattr(mock_client, error_method), 'side_effect',
            botocore.exceptions.ClientError({}, error_method))

    # Don't initialize API client until after mocking done above.
    patched_s3_api = s3_api.S3Api()
    with self.assertRaises(errors.S3ApiError):
      patched_s3_api.GetBucket(
          BUCKET_NAME, fields_scope=cloud_api.FieldsScope.FULL)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ListBucketsTest(test_base.StorageTestBase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_list_buckets_translates_response_to_resources(self):
    names = ['bucket1', 'bucket2']
    cloud_urls = [storage_url.storage_url_from_string('s3://' + name)
                  for name in names]
    dates = [datetime.datetime(1, 1, 1), datetime.datetime(2, 1, 1)]
    owner_data = {
        'DisplayName': OWNER_NAME,
        'ID': OWNER_ID,
    }
    s3_response = {
        'Buckets': [
            {'Name': name, 'CreationDate': date}
            for name, date in zip(names, dates)
        ],
        'Owner': owner_data,
    }
    self.stubber.add_response(
        method='list_buckets', expected_params={}, service_response=s3_response)

    expected = []
    for name, url, date in zip(names, cloud_urls, dates):
      expected.append(resource_reference.BucketResource(
          url, metadata={'Bucket': {'Name': name, 'CreationDate': date},
                         'Owner': owner_data}))
    with self.stubber:
      observed = self.s3_api.ListBuckets()
      self.assertCountEqual(observed, expected)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ListObjectsTest(test_base.StorageTestBase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_list_objects_creates_object_resources(self):
    s3_objects = []
    for i in range(2):
      s3_objects.append({
          'Key': 'object_name_%d' % i,
          'LastModified': datetime.datetime(i + 1, 1, 1),
          'ETag': 'etag_%d' % i,
          'Size': i,
          'StorageClass': 'class_%d' % i
      })
    response = {'Contents': s3_objects, 'Name': BUCKET_NAME}
    self.stubber.add_response(
        'list_objects_v2',
        service_response=response,
        expected_params={'Bucket': BUCKET_NAME})

    expected = []
    for o in s3_objects:
      url = storage_url.CloudUrl(
          cloud_api.ProviderPrefix.S3.value, BUCKET_NAME, o['Key'])
      resource = resource_reference.ObjectResource(
          url, etag=o['ETag'], metadata=o)
      expected.append(resource)
    with self.stubber:
      observed = self.s3_api.ListObjects(BUCKET_NAME)
      self.assertCountEqual(observed, expected)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetObjectMetadataTest(test_base.StorageTestBase, parameterized.TestCase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_get_object_metadata_creates_object_resource(self):
    response = {'ETag': 'e'}
    self.stubber.add_response(
        'head_object',
        service_response=response,
        expected_params={
            'Bucket': BUCKET_NAME,
            'Key': OBJECT_NAME,
        })

    expected_cloud_url = storage_url.CloudUrl(
        SCHEME, bucket_name=BUCKET_NAME, object_name=OBJECT_NAME)
    expected_resource = resource_reference.ObjectResource(
        expected_cloud_url, etag='e', metadata=response)
    with self.stubber:
      object_resource = self.s3_api.GetObjectMetadata(BUCKET_NAME, OBJECT_NAME)
      self.assertEqual(object_resource, expected_resource)

  def test_get_object_metadata_populates_cloud_url_with_generation(self):
    generation = 'generation'
    self.stubber.add_response(
        'head_object',
        service_response={'ETag': 'e', 'VersionId': generation},
        expected_params={
            'Bucket': BUCKET_NAME,
            'Key': OBJECT_NAME,
            'VersionId': generation,
        })

    with self.stubber:
      object_resource = self.s3_api.GetObjectMetadata(
          BUCKET_NAME, OBJECT_NAME, generation=generation)

      expected_cloud_url = storage_url.CloudUrl(
          SCHEME,
          bucket_name=BUCKET_NAME,
          object_name=OBJECT_NAME,
          generation=generation)
      self.assertEqual(object_resource.storage_url, expected_cloud_url)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CopyObjectTest(test_base.StorageTestBase, parameterized.TestCase):
  # TODO(b/167691513): Refactor all instances of from_gcs_metadata_object.
  # TODO(b/168332070): Refactor all instances of messages.Object to Resource.

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)
    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.source_object = self.messages.Object(name='o', bucket='b')
    self.destination_object = self.messages.Object(name='o2', bucket='b')

  def test_copies_objects(self):
    params = {
        'Bucket': self.destination_object.bucket,
        'Key': self.destination_object.name,
        'CopySource': {'Bucket': self.source_object.bucket,
                       'Key': self.source_object.name}}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._GetObjectResourceFromS3Response(
        response, self.destination_object.bucket, self.destination_object.name)
    with self.stubber:
      observed_resource = self.s3_api.CopyObject(
          self.source_object, self.destination_object)
      self.assertEqual(observed_resource, expected_resource)

  def test_raises_error_for_missing_source_metadata(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(None, self.destination_object)

  def test_raises_error_for_missing_source_metadata_name(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(self.messages.Object(bucket='b'),
                             self.destination_object)

  def test_raises_error_for_missing_source_metadata_bucket(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(self.messages.Object(name='o'),
                             self.destination_object)

  def test_raises_error_for_missing_destination_metadata(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(self.source_object, None)

  def test_raises_error_for_missing_destination_metadata_name(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(self.source_object,
                             self.messages.Object(bucket='b'))

  def test_raises_error_for_missing_destination_metadata_bucket(self):
    with self.assertRaises(ValueError):
      self.s3_api.CopyObject(self.source_object, self.messages.Object(name='o'))

  def test_copy_handles_generation(self):
    generation_arg = 'genZebra'
    params = {
        'Bucket': self.destination_object.bucket,
        'Key': self.destination_object.name,
        'CopySource': {'Bucket': self.source_object.bucket,
                       'Key': self.source_object.name,
                       'VersionId': generation_arg}}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._GetObjectResourceFromS3Response(
        response, self.destination_object.bucket, self.destination_object.name)
    with self.stubber:
      observed_resource = self.s3_api.CopyObject(
          self.source_object, self.destination_object,
          source_object_generation=generation_arg)
      self.assertEqual(observed_resource, expected_resource)

  @parameterized.parameters(
      s3_api._GCS_TO_S3_PREDEFINED_ACL_TRANSLATION_DICT.items())
  def test_copy_handles_predefined_acl(self, arg_acl, translated_acl):
    params = {
        'Bucket': self.destination_object.bucket,
        'Key': self.destination_object.name,
        'CopySource': {'Bucket': self.source_object.bucket,
                       'Key': self.source_object.name},
        'ACL': translated_acl}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._GetObjectResourceFromS3Response(
        response, self.destination_object.bucket, self.destination_object.name)
    with self.stubber:
      observed_resource = self.s3_api.CopyObject(
          self.source_object, self.destination_object,
          request_config=cloud_api.RequestConfig(arg_acl))
      self.assertEqual(observed_resource, expected_resource)

  def test_copy_handles_api_error(self):
    self.stubber.add_client_error(
        'copy_object', http_status_code=404)

    with self.stubber:
      with self.assertRaises(errors.S3ApiError):
        self.s3_api.CopyObject(self.source_object, self.destination_object)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class DownloadObjectTest(test_base.StorageTestBase):
  # TODO(b/167691513): Refactor all instances of from_gcs_metadata_object.

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_download_object_writes_to_file(self):
    response = {'Body': io.BytesIO(BINARY_DATA),
                'ContentEncoding': CONTENT_ENCODING}
    self.stubber.add_response(
        'get_object',
        service_response=response,
        expected_params={'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME})

    write_stream = io.BytesIO()
    with self.stubber:
      result = self.s3_api.DownloadObject(
          BUCKET_NAME, OBJECT_NAME, write_stream)
      self.assertEqual(result, CONTENT_ENCODING)

    self.assertEqual(write_stream.getvalue(), BINARY_DATA)

  def test_download_object_handles_generation(self):
    generation = 'cool_id'
    response = {'Body': io.BytesIO(BINARY_DATA),
                'ContentEncoding': CONTENT_ENCODING}
    self.stubber.add_response(
        'get_object',
        service_response=response,
        expected_params={'Bucket': BUCKET_NAME,
                         'Key': OBJECT_NAME,
                         'VersionId': generation})

    write_stream = io.BytesIO()
    with self.stubber:
      result = self.s3_api.DownloadObject(
          BUCKET_NAME, OBJECT_NAME, write_stream, generation=generation)
      self.assertEqual(result, CONTENT_ENCODING)

    self.assertEqual(write_stream.getvalue(), BINARY_DATA)

  def test_download_object_handles_missing_content_encoding(self):
    response = {'Body': io.BytesIO(BINARY_DATA)}
    self.stubber.add_response(
        'get_object',
        service_response=response,
        expected_params={
            'Bucket': BUCKET_NAME,
            'Key': OBJECT_NAME,
        })

    write_stream = io.BytesIO()
    with self.stubber:
      result = self.s3_api.DownloadObject(BUCKET_NAME, OBJECT_NAME,
                                          write_stream)
      self.assertIsNone(result)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class UploadObjectTest(test_base.StorageTestBase, parameterized.TestCase):
  # TODO(b/167691513): Refactor all instances of from_gcs_metadata_object.
  # TODO(b/168332070): Refactor all instances of messages.Object to Resource.

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)
    self.messages = apis.GetMessagesModule('storage', 'v1')

  def test_uploads(self):
    params = {'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME, 'Body': BINARY_DATA}
    response = {'ETag': ETAG}
    self.stubber.add_response(
        'put_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._GetObjectResourceFromS3Response(
        response, BUCKET_NAME, OBJECT_NAME)
    upload_object = self.messages.Object(name=OBJECT_NAME, bucket=BUCKET_NAME)

    with self.stubber:
      result_resource = self.s3_api.UploadObject(
          io.BytesIO(BINARY_DATA), upload_object)
      self.assertEqual(result_resource.metadata, expected_resource.metadata)

  @parameterized.parameters(
      s3_api._GCS_TO_S3_PREDEFINED_ACL_TRANSLATION_DICT.items())
  def test_upload_translates_predefined_acl(self, arg_acl, translated_acl):
    params = {'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME, 'Body': BINARY_DATA,
              'ACL': translated_acl}
    response = {'ETag': ETAG}
    self.stubber.add_response(
        'put_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._GetObjectResourceFromS3Response(
        response, BUCKET_NAME, OBJECT_NAME)
    upload_object = self.messages.Object(name=OBJECT_NAME, bucket=BUCKET_NAME)

    with self.stubber:
      result_resource = self.s3_api.UploadObject(
          io.BytesIO(BINARY_DATA), upload_object,
          request_config=cloud_api.RequestConfig(arg_acl))
      self.assertEqual(result_resource, expected_resource)

  def test_upload_raises_error_for_unrecognized_predefined_acl(self):
    upload_object = self.messages.Object(name=OBJECT_NAME, bucket=BUCKET_NAME)
    with self.assertRaisesRegex(
        ValueError, ('Could not translate predefined_acl_string fake_acl to'
                     ' AWS-accepted ACL.')):
      self.s3_api.UploadObject(
          io.BytesIO(BINARY_DATA), upload_object,
          request_config=cloud_api.RequestConfig('fake_acl'))

  def test_raises_error_for_missing_metadata(self):
    with self.assertRaisesRegex(ValueError,
                                'No object metadata supplied for object.'):
      self.s3_api.UploadObject(io.BytesIO(BINARY_DATA), None)

  def test_raises_error_for_missing_metadata_name(self):
    with self.assertRaisesRegex(
        ValueError, 'Object metadata supplied for object had no object name.'):
      self.s3_api.UploadObject(io.BytesIO(BINARY_DATA), self.messages.Object())

  def test_raises_error_for_missing_metadata_bucket(self):
    with self.assertRaisesRegex(
        ValueError, 'Object metadata supplied for object had no bucket name.'):
      self.s3_api.UploadObject(io.BytesIO(BINARY_DATA),
                               self.messages.Object(name='o'))

  def test_raises_api_error(self):
    self.stubber.add_client_error(
        'put_object', http_status_code=404)

    upload_object = self.messages.Object(name=OBJECT_NAME, bucket=BUCKET_NAME)
    with self.stubber:
      with self.assertRaises(errors.S3ApiError):
        self.s3_api.UploadObject(io.BytesIO(BINARY_DATA),
                                 upload_object)


MockCall = collections.namedtuple(
    'MockCall',
    ['function_name', 'api_method', 'args']
)

MockError = collections.namedtuple(
    'MockError',
    ['http_status_code', 'error_class']
)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ErrorTranslationTest(test_base.StorageTestBase, parameterized.TestCase):

  mock_calls = [
      MockCall(
          function_name='ListBuckets',
          api_method='list_buckets',
          args=()),
      MockCall(
          function_name='ListObjects',
          api_method='list_objects_v2',
          args=(BUCKET_NAME,)),
      MockCall(
          function_name='DownloadObject',
          api_method='get_object',
          args=(BUCKET_NAME, 'object_name', mock.Mock())),
      MockCall(
          function_name='GetObjectMetadata',
          api_method='head_object',
          args=(BUCKET_NAME, OBJECT_NAME)),
  ]

  mock_errors = [
      MockError(
          http_status_code=404,
          error_class=errors.S3ApiError),
  ]

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  @parameterized.parameters(itertools.product(mock_calls, mock_errors))
  def test_error_translation(self, mock_call, mock_error):
    self.stubber.add_client_error(
        mock_call.api_method, http_status_code=mock_error.http_status_code)

    with self.stubber:
      with self.assertRaises(mock_error.error_class):
        cloud_api_function = getattr(self.s3_api, mock_call.function_name)
        next(cloud_api_function(*mock_call.args))


if __name__ == '__main__':
  test_case.main()
