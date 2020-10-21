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

from botocore import stub
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import s3_api
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import s3_resource_reference
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.storage import test_base
from tests.lib.surface.storage import test_resources

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
SCHEME = storage_url.ProviderPrefix.S3


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetBucketTest(test_base.StorageTestBase, parameterized.TestCase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

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
          'ACL': {'Owner': {}, 'Grants': []}}))
  def test_gets_bucket_with_different_fields_scopes(
      self, fields_scope, number_api_calls, expected_metadata):
    # Minimum amount of response data to pass Boto Stubber validation and
    # verify each API endpoint has returned a response.
    get_bucket_api_call_and_response = [
        ('get_bucket_location', {'LocationConstraint': ''}),
        ('get_bucket_cors', {'CORSRules': []}),
        ('get_bucket_lifecycle_configuration', {'Rules': []}),
        ('get_bucket_logging', {
            'LoggingEnabled': {
                'TargetBucket': '', 'TargetGrants': [], 'TargetPrefix': ''}}),
        ('get_bucket_request_payment', {'Payer': 'BucketOwner'}),
        ('get_bucket_versioning', {}),
        ('get_bucket_website', {}),
        ('get_bucket_acl', {'Owner': {}, 'Grants': []})
    ]

    # Don't loop over extra API functions to avoid the Stubber
    # complaining about expected uncalled functions.
    for method, response in get_bucket_api_call_and_response[:number_api_calls]:
      self.stubber.add_response(method=method,
                                expected_params={'Bucket': BUCKET_NAME},
                                service_response=response)

    expected = s3_resource_reference.S3BucketResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME), metadata=expected_metadata)
    with self.stubber:
      observed = self.s3_api.get_bucket(BUCKET_NAME, fields_scope)
      self.assertEqual(observed, expected)

  def test_gets_bucket_receives_all_api_errors(self):
    get_bucket_api_method_names_and_metadata_key = [
        ('get_bucket_location', 'GetBucketLocation', 'LocationConstraint'),
        ('get_bucket_cors', 'GetBucketCors', 'CORSRules'),
        ('get_bucket_lifecycle_configuration',
         'GetBucketLifecycleConfiguration', 'LifecycleConfiguration'),
        ('get_bucket_logging', 'GetBucketLogging', 'LoggingEnabled'),
        ('get_bucket_request_payment', 'GetBucketRequestPayment', 'Payer'),
        ('get_bucket_versioning', 'GetBucketVersioning', 'Versioning'),
        ('get_bucket_website', 'GetBucketWebsite', 'Website'),
        ('get_bucket_acl', 'GetBucketAcl', 'ACL'),
    ]
    expected_metadata = {'Name': BUCKET_NAME}
    for (method_name, error_string_of_method_name,
         metadata_key) in get_bucket_api_method_names_and_metadata_key:
      self.stubber.add_client_error(method=method_name)
      expected_metadata[metadata_key] = errors.S3ApiError(
          'An error occurred () when calling the {} operation: '
          .format(error_string_of_method_name))

    expected_resource = s3_resource_reference.S3BucketResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME), metadata=expected_metadata)
    with self.stubber:
      observed_resource = self.s3_api.get_bucket(
          BUCKET_NAME, fields_scope=cloud_api.FieldsScope.FULL)
      self.assertEqual(observed_resource, expected_resource)

  @parameterized.parameters([
      'get_bucket_location', 'get_bucket_cors',
      'get_bucket_lifecycle_configuration', 'get_bucket_logging',
      'get_bucket_request_payment', 'get_bucket_versioning',
      'get_bucket_website', 'get_bucket_acl'])
  def test_gets_bucket_with_individual_calls_failing(self, failing_method_name):
    # Method name, method name in error, metadata key, API response, and
    # flag describing if API response has key mirroring metadata key.
    get_bucket_api_call_data = [
        (
            'get_bucket_location', 'GetBucketLocation', 'LocationConstraint',
            {'LocationConstraint': ''}, True
        ),
        (
            'get_bucket_cors', 'GetBucketCors', 'CORSRules',
            {'CORSRules': []}, True
        ),
        (
            'get_bucket_lifecycle_configuration',
            'GetBucketLifecycleConfiguration', 'LifecycleConfiguration',
            {'Rules': []}, False
        ),
        (
            'get_bucket_logging', 'GetBucketLogging', 'LoggingEnabled',
            {'LoggingEnabled': {
                'TargetBucket': '', 'TargetGrants': [], 'TargetPrefix': ''}},
            True
        ),
        (
            'get_bucket_request_payment', 'GetBucketRequestPayment', 'Payer',
            {'Payer': 'BucketOwner'}, True
        ),
        (
            'get_bucket_versioning', 'GetBucketVersioning', 'Versioning', {},
            False
        ),
        (
            'get_bucket_website', 'GetBucketWebsite', 'Website', {}, False
        ),
        (
            'get_bucket_acl', 'GetBucketAcl', 'ACL',
            {'Owner': {}, 'Grants': []}, False
        ),
    ]
    expected_metadata = {'Name': BUCKET_NAME}
    for (method_name, error_string_of_method_name, metadata_key, response,
         result_has_key) in get_bucket_api_call_data:
      if failing_method_name == method_name:
        self.stubber.add_client_error(method=method_name)
        expected_metadata[metadata_key] = errors.S3ApiError(
            'An error occurred () when calling the {} operation: '
            .format(error_string_of_method_name))
      else:
        self.stubber.add_response(method=method_name,
                                  expected_params={'Bucket': BUCKET_NAME},
                                  service_response=response)
        expected_metadata[metadata_key] = (
            response[metadata_key] if result_has_key else response)

    expected_resource = s3_resource_reference.S3BucketResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME), metadata=expected_metadata)
    with self.stubber:
      observed_resource = self.s3_api.get_bucket(
          BUCKET_NAME, fields_scope=cloud_api.FieldsScope.FULL)
      self.assertEqual(observed_resource, expected_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ListBucketsTest(test_base.StorageTestBase, parameterized.TestCase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  # NO_ACL is treated the same as SHORT.
  @parameterized.parameters([
      cloud_api.FieldsScope.SHORT, cloud_api.FieldsScope.NO_ACL])
  def test_list_buckets_translates_response_to_resources(self, fields_scope):
    names = ['bucket1', 'bucket2']
    cloud_urls = [storage_url.CloudUrl(SCHEME, name) for name in names]
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
      expected.append(s3_resource_reference.S3BucketResource(
          url, metadata={'Bucket': {'Name': name, 'CreationDate': date},
                         'Owner': owner_data}))
    with self.stubber:
      observed = self.s3_api.list_buckets(fields_scope=fields_scope)
      self.assertCountEqual(observed, expected)

  def test_list_buckets_calls_get_bucket_with_full_fields_scope(self):
    owner_data = {
        'DisplayName': OWNER_NAME,
        'ID': OWNER_ID,
    }
    s3_response = {
        'Buckets': [
            {'Name': 'bucket1', 'CreationDate': datetime.datetime(1, 1, 1)},
            {'Name': 'bucket2', 'CreationDate': datetime.datetime(2, 1, 1)},
        ],
        'Owner': owner_data,
    }
    self.stubber.add_response(
        method='list_buckets', expected_params={}, service_response=s3_response)

    with mock.patch.object(self.s3_api, 'get_bucket') as mock_get_bucket:
      with self.stubber:
        list(self.s3_api.list_buckets(fields_scope=cloud_api.FieldsScope.FULL))

        mock_get_bucket.mock_calls = [
            mock.call('bucket1', cloud_api.FieldsScope.FULL),
            mock.call('bucket2', cloud_api.FieldsScope.FULL),
        ]


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ListObjectsTest(test_base.StorageTestBase, parameterized.TestCase):
  _OBJECT_RESPONSE_METADATA = {
      'Key': 'obj',
      'LastModified': datetime.datetime(1, 1, 1),
      'ETag': 'etag_1',
      'Size': 1,
      'StorageClass': 'class_1',
  }

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  @parameterized.named_parameters([{
      'testcase_name':
          '_with_multiple_objects_and_prefixes_present',
      'response': {
          'Name': BUCKET_NAME,
          'Contents': [
              {
                  'Key': 'obj1'
              },
              {
                  'Key': 'obj2'
              },
          ],
          'CommonPrefixes': [
              {
                  'Prefix': 'dir1/'
              },
              {
                  'Prefix': 'dir2/'
              },
          ],
      },
      'expected_resources': [
          s3_resource_reference.S3ObjectResource(
              storage_url.CloudUrl(SCHEME, BUCKET_NAME, 'obj1'),
              metadata={'Key': 'obj1'}),
          s3_resource_reference.S3ObjectResource(
              storage_url.CloudUrl(SCHEME, BUCKET_NAME, 'obj2'),
              metadata={'Key': 'obj2'}),
          test_resources.get_prefix_resource(SCHEME, BUCKET_NAME, 'dir1/'),
          test_resources.get_prefix_resource(SCHEME, BUCKET_NAME, 'dir2/'),
      ],
  }, {
      'testcase_name':
          '_with_missing_prefixes',
      'response': {
          'Name': BUCKET_NAME,
          'Contents': [{
              'Key': 'obj1'
          }],
      },
      'expected_resources': [
          s3_resource_reference.S3ObjectResource(
              storage_url.CloudUrl(SCHEME, BUCKET_NAME, 'obj1'),
              metadata={'Key': 'obj1'})
      ],
  }, {
      'testcase_name':
          '_with_missing_objects',
      'response': {
          'Name': BUCKET_NAME,
          'CommonPrefixes': [{
              'Prefix': 'dir1/'
          }],
      },
      'expected_resources': [
          test_resources.get_prefix_resource(SCHEME, BUCKET_NAME, 'dir1/'),
      ],
  }, {
      'testcase_name': '_with_both_objects_and_prefixes_missing',
      'response': {
          'Name': BUCKET_NAME
      },
      'expected_resources': [],
  }, {
      'testcase_name':
          '_with_correct_metadata_populated',
      'response': {
          'Name': BUCKET_NAME,
          'Contents': [_OBJECT_RESPONSE_METADATA],
      },
      'expected_resources': [
          s3_resource_reference.S3ObjectResource(
              storage_url.CloudUrl(SCHEME, BUCKET_NAME, 'obj'),
              etag='etag_1',
              metadata=_OBJECT_RESPONSE_METADATA)
      ],
  }])
  def test_list_objects_returns_correct_object_and_prefix_resources(
      self, response, expected_resources):
    self.stubber.add_response(
        'list_objects_v2',
        service_response=response,
        expected_params={
            'Bucket': BUCKET_NAME,
            'Prefix': '',
            'Delimiter': '',
        })

    with self.stubber:
      observed = self.s3_api.list_objects(BUCKET_NAME)
      self.assertCountEqual(observed, expected_resources)

  def test_list_objects_with_all_versions(self):
    object_metadata_with_version = {'Key': 'obj', 'VersionId': 'v1'}
    self.stubber.add_response(
        'list_object_versions',
        service_response={
            'Name': BUCKET_NAME,
            'Versions': [object_metadata_with_version],
        },
        expected_params={
            'Bucket': BUCKET_NAME,
            'Prefix': '',
            'Delimiter': '',
        })

    expected_resources = [
        s3_resource_reference.S3ObjectResource(
            storage_url.CloudUrl(SCHEME, BUCKET_NAME, 'obj', 'v1'),
            metadata=object_metadata_with_version)
    ]

    with self.stubber:
      observed = self.s3_api.list_objects(BUCKET_NAME, all_versions=True)
      self.assertCountEqual(observed, expected_resources)

  def test_list_objects_with_full_fields_scope(self):
    # Test with more than one object to ensure that get_object_metadata call
    # is being made for each object.
    objects = [{'Key': 'obj1'}, {'Key': 'obj2'}]
    self.stubber.add_response(
        'list_objects_v2',
        service_response={
            'Name': BUCKET_NAME,
            'Contents': objects,
        },
        expected_params={
            'Bucket': BUCKET_NAME,
            'Prefix': '',
            'Delimiter': '',
        })

    expected_resources = []
    for object_dict in objects:
      # For each object, we expect a call to the head_object and get_object_acl
      # API methods.
      self.stubber.add_response(
          'head_object',
          service_response={'ETag': 'e'},
          expected_params={
              'Bucket': BUCKET_NAME,
              'Key': object_dict['Key']
          })
      self.stubber.add_response(
          'get_object_acl',
          service_response={'Grants': []},
          expected_params={
              'Bucket': BUCKET_NAME,
              'Key': object_dict['Key']
          })

      expected_resources.append(
          s3_resource_reference.S3ObjectResource(
              storage_url.CloudUrl(SCHEME, BUCKET_NAME, object_dict['Key']),
              etag='e',
              metadata={
                  'ETag': 'e',
                  'ACL': {
                      'Grants': []
                  }
              }))

    with self.stubber:
      observed = self.s3_api.list_objects(
          BUCKET_NAME, fields_scope=cloud_api.FieldsScope.FULL)
      self.assertEqual(list(observed), expected_resources)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetObjectMetadataTest(test_base.StorageTestBase, parameterized.TestCase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_get_object_metadata_creates_object_resource(self):
    response = {'ETag': 'e', 'ContentLength': 5}
    self.stubber.add_response(
        'head_object',
        service_response=response,
        expected_params={
            'Bucket': BUCKET_NAME,
            'Key': OBJECT_NAME,
        })

    expected_cloud_url = storage_url.CloudUrl(
        SCHEME, bucket_name=BUCKET_NAME, object_name=OBJECT_NAME)
    expected_resource = s3_resource_reference.S3ObjectResource(
        expected_cloud_url, etag='e', size=5, metadata=response)
    with self.stubber:
      object_resource = self.s3_api.get_object_metadata(BUCKET_NAME,
                                                        OBJECT_NAME)
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
      object_resource = self.s3_api.get_object_metadata(
          BUCKET_NAME, OBJECT_NAME, generation=generation)

      expected_cloud_url = storage_url.CloudUrl(
          SCHEME,
          bucket_name=BUCKET_NAME,
          object_name=OBJECT_NAME,
          generation=generation)
      self.assertEqual(object_resource.storage_url, expected_cloud_url)

  def test_get_object_metadata_populates_acls_with_full_fieldscope(self):
    expected_request_params = {'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME}
    self.stubber.add_response(
        'head_object',
        service_response={},
        expected_params=expected_request_params)
    self.stubber.add_response(
        'get_object_acl',
        service_response={
            'Grants': [],
            'Owner': {
                'ID': '1'
            },
            'ResponseMetadata': {},
        },
        expected_params=expected_request_params)

    with self.stubber:
      object_resource = self.s3_api.get_object_metadata(
          BUCKET_NAME, OBJECT_NAME, fields_scope=cloud_api.FieldsScope.FULL)

      expected_resource = s3_resource_reference.S3ObjectResource(
          storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME),
          metadata={
              'ACL': {
                  'Grants': [],
                  'Owner': {
                      'ID': '1'
                  },
              },
          })
      self.assertEqual(object_resource, expected_resource)

  def test_get_object_metadata_populates_acls_with_error_message(self):
    self.stubber.add_response(
        'head_object',
        service_response={},
        expected_params={
            'Bucket': BUCKET_NAME,
            'Key': OBJECT_NAME
        })
    self.stubber.add_client_error('get_object_acl')

    with self.stubber:
      object_resource = self.s3_api.get_object_metadata(
          BUCKET_NAME, OBJECT_NAME, fields_scope=cloud_api.FieldsScope.FULL)

      expected_resource = s3_resource_reference.S3ObjectResource(
          storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME),
          metadata={
              'ACL':
                  errors.S3ApiError('An error occurred () when calling the'
                                    ' GetObjectAcl operation: ')
          })
      self.assertEqual(object_resource, expected_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CopyObjectTest(test_base.StorageTestBase, parameterized.TestCase):
  # TODO(b/168332070): Refactor all instances of messages.Object to Resource.

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_copies_objects(self):
    source_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o'))
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o2'))

    params = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'CopySource': {'Bucket': source_resource.storage_url.bucket_name,
                       'Key': source_resource.storage_url.object_name}}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._get_object_resource_from_s3_response(
        response, destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name)
    with self.stubber:
      observed_resource = self.s3_api.copy_object(source_resource,
                                                  destination_resource)
      self.assertEqual(observed_resource, expected_resource)

  def test_copy_handles_api_error(self):
    source_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o'))
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o2'))
    self.stubber.add_client_error(
        'copy_object', http_status_code=404)

    with self.stubber:
      with self.assertRaises(errors.S3ApiError):
        self.s3_api.copy_object(source_resource, destination_resource)

  def test_copy_handles_generation(self):
    source_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o#gen'))
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o2'))
    params = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'CopySource': {'Bucket': source_resource.storage_url.bucket_name,
                       'Key': source_resource.storage_url.object_name,
                       'VersionId': 'gen'}}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._get_object_resource_from_s3_response(
        response, destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name)
    with self.stubber:
      observed_resource = self.s3_api.copy_object(source_resource,
                                                  destination_resource)
      self.assertEqual(observed_resource, expected_resource)

  @parameterized.parameters(
      s3_api._GCS_TO_S3_PREDEFINED_ACL_TRANSLATION_DICT.items())
  def test_copy_handles_predefined_acl(self, arg_acl, translated_acl):
    source_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o'))
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o2'))

    params = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'CopySource': {'Bucket': source_resource.storage_url.bucket_name,
                       'Key': source_resource.storage_url.object_name},
        'ACL': translated_acl}
    response = {'CopyObjectResult': {'ETag': ETAG,
                                     'LastModified': LAST_MODIFIED}}
    self.stubber.add_response(
        'copy_object',
        service_response=response,
        expected_params=params)

    expected_resource = self.s3_api._get_object_resource_from_s3_response(
        response, destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name)
    with self.stubber:
      observed_resource = self.s3_api.copy_object(
          source_resource,
          destination_resource,
          request_config=cloud_api.RequestConfig(arg_acl))
      self.assertEqual(observed_resource, expected_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class DownloadObjectTest(test_base.StorageTestBase):

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
      result = self.s3_api.download_object(BUCKET_NAME, OBJECT_NAME,
                                           write_stream)
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
      result = self.s3_api.download_object(
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
      result = self.s3_api.download_object(BUCKET_NAME, OBJECT_NAME,
                                           write_stream)
      self.assertIsNone(result)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class UploadObjectTest(test_base.StorageTestBase, parameterized.TestCase):
  # TODO(b/168332070): Refactor all instances of messages.Object to Resource.

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  def test_uploads_with_unknown_resource(self):
    params = {'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME, 'Body': BINARY_DATA}
    response = {'ETag': ETAG}
    self.stubber.add_response(
        'put_object', service_response=response, expected_params=params)
    upload_resource = resource_reference.UnknownResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME))

    expected_resource = self.s3_api._get_object_resource_from_s3_response(
        response, BUCKET_NAME, OBJECT_NAME)
    with self.stubber:
      observed_resource = self.s3_api.upload_object(
          io.BytesIO(BINARY_DATA), upload_resource)
      self.assertEqual(observed_resource, expected_resource)

  @parameterized.parameters(
      s3_api._GCS_TO_S3_PREDEFINED_ACL_TRANSLATION_DICT.items())
  def test_upload_translates_predefined_acl(self, arg_acl, translated_acl):
    params = {'Bucket': BUCKET_NAME, 'Key': OBJECT_NAME, 'Body': BINARY_DATA,
              'ACL': translated_acl}
    response = {'ETag': ETAG}
    self.stubber.add_response(
        'put_object', service_response=response, expected_params=params)

    expected_resource = self.s3_api._get_object_resource_from_s3_response(
        response, BUCKET_NAME, OBJECT_NAME)
    upload_resource = resource_reference.UnknownResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME))

    with self.stubber:
      observed_resource = self.s3_api.upload_object(
          io.BytesIO(BINARY_DATA),
          upload_resource,
          request_config=cloud_api.RequestConfig(arg_acl))
      self.assertEqual(observed_resource, expected_resource)

  def test_upload_raises_error_for_unrecognized_predefined_acl(self):
    upload_resource = resource_reference.UnknownResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME))
    with self.assertRaisesRegex(
        ValueError, ('Could not translate predefined_acl_string fake_acl to'
                     ' AWS-accepted ACL.')):
      self.s3_api.upload_object(
          io.BytesIO(BINARY_DATA),
          upload_resource,
          request_config=cloud_api.RequestConfig('fake_acl'))

  def test_raises_api_error(self):
    self.stubber.add_client_error('put_object', http_status_code=404)

    upload_resource = resource_reference.UnknownResource(
        storage_url.CloudUrl(SCHEME, BUCKET_NAME, OBJECT_NAME))
    with self.stubber:
      with self.assertRaises(errors.S3ApiError):
        self.s3_api.upload_object(io.BytesIO(BINARY_DATA), upload_resource)


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
          function_name='list_buckets', api_method='list_buckets', args=()),
      MockCall(
          function_name='list_objects',
          api_method='list_objects_v2',
          args=(BUCKET_NAME,)),
      MockCall(
          function_name='download_object',
          api_method='get_object',
          args=(BUCKET_NAME, 'object_name', mock.Mock())),
      MockCall(
          function_name='get_object_metadata',
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
