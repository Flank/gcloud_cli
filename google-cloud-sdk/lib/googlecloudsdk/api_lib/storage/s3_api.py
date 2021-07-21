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
"""Implementation of CloudApi for s3 using boto3."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import threading

import boto3
import botocore
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import s3_metadata_util
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import s3_resource_reference
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import scaled_integer


# S3 does not allow upload of size > 5 GiB for put_object.
MAX_PUT_OBJECT_SIZE = 5 * (1024**3)  # 5 GiB
BOTO3_CLIENT_LOCK = threading.Lock()


def _raise_if_not_found_error(error, resource_name):
  if error.response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 404:
    # TODO(b/193464904): Remove the hardcoded error message here after
    # refactoring the errors module.
    raise errors.NotFoundError('{} not found: 404.'.format(resource_name))


def _catch_client_error_raise_s3_api_error(format_str=None):
  """Decorator that catches botocore ClientErrors and raises S3ApiErrors.

  Args:
    format_str (str): A googlecloudsdk.api_lib.storage.errors.S3ErrorPayload
      format string. Note that any properties that are accessed here are on the
      S3ErrorPayload object, not the object returned from botocore.

  Returns:
    A decorator that catches botocore.exceptions.ClientError and returns an
      S3ApiError with a formatted error message.
  """

  return errors.catch_error_raise_cloud_api_error(
      [(botocore.exceptions.ClientError, errors.S3ApiError)],
      format_str=format_str)


# pylint:disable=abstract-method
class S3Api(cloud_api.CloudApi):
  """S3 Api client."""

  capabilities = {
      # Boto3 implements its own unskippable validation.
      cloud_api.Capability.CLIENT_SIDE_HASH_VALIDATION,
  }

  def __init__(self):
    # Using a lock since the boto3.client creation is not thread-safe.
    with BOTO3_CLIENT_LOCK:
      self.client = boto3.client(storage_url.ProviderPrefix.S3.value)

  @_catch_client_error_raise_s3_api_error()
  def create_bucket(self, bucket_resource, fields_scope=None):
    """See super class."""
    del fields_scope  # Unused in S3 client.

    if bucket_resource.retention_period:
      raise ValueError(
          'S3 API does not accept retention_period argument for create_bucket.')
    if bucket_resource.storage_class:
      raise ValueError(
          'S3 API does not accept storage_class argument for create_bucket.')
    if bucket_resource.uniform_bucket_level_access:
      raise ValueError(
          'S3 API does not accept uniform_bucket_level_access argument for create_bucket.'
      )

    if bucket_resource.location:
      # Create client with appropriate endpoint for creating regional bucket.
      client = boto3.client(
          storage_url.ProviderPrefix.S3.value,
          region_name=bucket_resource.location)
      create_bucket_configuration = {
          'LocationConstraint': bucket_resource.location
      }
    else:
      client = self.client
      # Must match client's default regional endpoint.
      create_bucket_configuration = {
          'LocationConstraint': boto3.session.Session().region_name
      }

    metadata = client.create_bucket(
        Bucket=bucket_resource.storage_url.bucket_name,
        CreateBucketConfiguration=create_bucket_configuration)
    backend_location = metadata.get('Location')
    return s3_resource_reference.S3BucketResource(
        bucket_resource.storage_url,
        location=backend_location,
        metadata=metadata)

  @_catch_client_error_raise_s3_api_error()
  def delete_bucket(self, bucket_name, request_config):
    """See super class."""
    del request_config  # Unused.
    return self.client.delete_bucket(Bucket=bucket_name)

  def get_bucket(self, bucket_name, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    metadata = {'Name': bucket_name}
    # TODO (b/168716392): As new commands are implemented, they may want
    # specific error handling for different methods.
    try:
      # Low-bandwidth way to determine if bucket exists for FieldsScope.SHORT.
      metadata.update(self.client.get_bucket_location(
          Bucket=bucket_name))
    except botocore.exceptions.ClientError as error:
      _raise_if_not_found_error(error, bucket_name)

      metadata['LocationConstraint'] = errors.S3ApiError(error)

    if fields_scope is not cloud_api.FieldsScope.SHORT:
      # Data for FieldsScope.NO_ACL.
      for key, api_call, result_has_key in [
          ('CORSRules', self.client.get_bucket_cors, True),
          ('ServerSideEncryptionConfiguration',
           self.client.get_bucket_encryption, True),
          ('LifecycleConfiguration',
           self.client.get_bucket_lifecycle_configuration, False),
          ('LoggingEnabled', self.client.get_bucket_logging, True),
          ('Payer', self.client.get_bucket_request_payment, True),
          ('Versioning', self.client.get_bucket_versioning, False),
          ('Website', self.client.get_bucket_website, False),
      ]:
        try:
          api_result = api_call(Bucket=bucket_name)
          # Some results are wrapped in dictionaries with keys matching "key".
          metadata[key] = api_result.get(key) if result_has_key else api_result
        except botocore.exceptions.ClientError as error:
          metadata[key] = errors.S3ApiError(error)

      # User requested ACL's with FieldsScope.FULL.
      if fields_scope is cloud_api.FieldsScope.FULL:
        try:
          metadata['ACL'] = self.client.get_bucket_acl(Bucket=bucket_name)
        except botocore.exceptions.ClientError as error:
          metadata['ACL'] = errors.S3ApiError(error)

    return s3_resource_reference.S3BucketResource(
        storage_url.CloudUrl(storage_url.ProviderPrefix.S3, bucket_name),
        metadata=metadata)

  def patch_bucket(self,
                   bucket_resource,
                   request_config,
                   fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    del fields_scope, request_config  # Unused.

    if ('FullACLConfiguration' in bucket_resource.metadata or
        'ACL' in bucket_resource.metadata):
      try:
        if 'FullACLConfiguration' in bucket_resource.metadata:
          # Can contain canned ACL and other settings.
          # Takes priority over 'ACL' metadata key.
          kwargs = bucket_resource.metadata['FullACLConfiguration']
        else:
          # Data returned by get_bucket_acl.
          kwargs = {'AccessControlPolicy': bucket_resource.metadata['ACL']}
        kwargs['Bucket'] = bucket_resource.name
        self.client.put_bucket_acl(**kwargs)
      except botocore.exceptions.ClientError as error:
        _raise_if_not_found_error(error, bucket_resource.name)
        # Don't return any ACL information in case the failure affected both
        # metadata keys.
        bucket_resource.metadata.pop('FullACLConfiguration', None)
        bucket_resource.metadata.pop('ACL', None)
        log.error(errors.S3ApiError(error))

    patchable_metadata = {  # Key -> (client function, function kwargs).
        'CORSRules': (
            self.client.put_bucket_cors,
            {'CORSConfiguration': {
                'CORSRules': bucket_resource.metadata.get('CORSRules'),
            }}),
        'ServerSideEncryptionConfiguration': (
            self.client.put_bucket_encryption,
            {'ServerSideEncryptionConfiguration': bucket_resource.metadata.get(
                'ServerSideEncryptionConfiguration'),
            }),
        'LifecycleConfiguration': (
            self.client.put_bucket_lifecycle_configuration,
            {'LifecycleConfiguration': bucket_resource.metadata.get(
                'LifecycleConfiguration'),
            }),
        'LoggingEnabled': (
            self.client.put_bucket_logging,
            {'BucketLoggingStatus': {
                'LoggingEnabled': bucket_resource.metadata.get(
                    'LoggingEnabled'),
            }}),
        'Payer': (
            self.client.put_bucket_request_payment,
            {'RequestPaymentConfiguration': {
                'Payer': bucket_resource.metadata.get('Payer'),
            }}),
        'Versioning': (
            self.client.put_bucket_versioning,
            {'VersioningConfiguration': bucket_resource.metadata.get(
                'Versioning'),
            }),
        'Website': (
            self.client.put_bucket_website,
            {'WebsiteConfiguration': bucket_resource.metadata.get('Website')}),
    }
    for metadata_key, (patch_function,
                       patch_kwargs) in patchable_metadata.items():
      if metadata_key not in bucket_resource.metadata:
        continue

      patch_kwargs['Bucket'] = bucket_resource.name
      try:
        patch_function(**patch_kwargs)
      except botocore.exceptions.ClientError as error:
        _raise_if_not_found_error(error, bucket_resource.name)
        log.error(errors.S3ApiError(error))
        del bucket_resource.metadata[metadata_key]

    return bucket_resource

  def list_buckets(self, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    try:
      response = self.client.list_buckets()
      for bucket in response['Buckets']:
        if fields_scope == cloud_api.FieldsScope.FULL:
          yield self.get_bucket(bucket['Name'], fields_scope)
        else:
          yield s3_resource_reference.S3BucketResource(
              storage_url.CloudUrl(
                  storage_url.ProviderPrefix.S3, bucket['Name']),
              metadata={'Bucket': bucket, 'Owner': response['Owner']})
    except botocore.exceptions.ClientError as error:
      core_exceptions.reraise(errors.S3ApiError(error))

  def list_objects(self,
                   bucket_name,
                   prefix=None,
                   delimiter=None,
                   all_versions=False,
                   fields_scope=None):
    """See super class."""
    if all_versions:
      api_method_name = 'list_object_versions'
      objects_key = 'Versions'
    else:
      api_method_name = 'list_objects_v2'
      objects_key = 'Contents'
    try:
      paginator = self.client.get_paginator(api_method_name)
      page_iterator = paginator.paginate(
          Bucket=bucket_name,
          Prefix=prefix if prefix is not None else '',
          Delimiter=delimiter if delimiter is not None else '')
      for page in page_iterator:
        for object_dict in page.get(objects_key, []):
          if fields_scope is cloud_api.FieldsScope.FULL:
            # The metadata present in the list_objects_v2 response or the
            # list_object_versions response is not enough
            # for a FULL scope. Hence, calling the GetObjectMetadata method
            # to get the additonal metadata and ACLs information.
            yield self.get_object_metadata(
                bucket_name=bucket_name,
                object_name=object_dict['Key'],
                generation=object_dict.get('VersionId'),
                fields_scope=fields_scope)
          else:
            yield s3_metadata_util.get_object_resource_from_s3_response(
                object_dict, bucket_name)
        for prefix_dict in page.get('CommonPrefixes', []):
          yield s3_metadata_util.get_prefix_resource_from_s3_response(
              prefix_dict, bucket_name)
    except botocore.exceptions.ClientError as error:
      core_exceptions.reraise(errors.S3ApiError(error))

  @_catch_client_error_raise_s3_api_error()
  def copy_object(self,
                  source_resource,
                  destination_resource,
                  request_config,
                  progress_callback=None):
    """See super class."""
    del progress_callback

    source_kwargs = {'Bucket': source_resource.storage_url.bucket_name,
                     'Key': source_resource.storage_url.object_name}
    if source_resource.storage_url.generation:
      source_kwargs['VersionId'] = source_resource.storage_url.generation

    kwargs = {'Bucket': destination_resource.storage_url.bucket_name,
              'Key': destination_resource.storage_url.object_name,
              'CopySource': source_kwargs}
    kwargs.update(
        s3_metadata_util.get_metadata_dict_from_request_config(request_config))

    response = self.client.copy_object(**kwargs)
    return s3_metadata_util.get_object_resource_from_s3_response(
        response, kwargs['Bucket'], kwargs['Key'])

    # TODO(b/161900052): Implement resumable copies.

  def _get_content_encoding(self, resource):
    """Returns the ContentEncoding for the resource.

    Returns the ContentEncoding if it is already present in the resource object.
    If it is not present, it makes an API call to fetch the object's metadata.
    This might happen if the resource was not created using the head_object
    call, for example, in case of S3Api.list_objects call which is used by the
    WildCardIterator if a wildcard is present.

    Args:
      resource (resource_reference.ObjectResource): Resource representing an
        existing object.

    Returns:
      A string representing the ContentEncoding for the S3 Object.
    """
    if resource.metadata:
      content_encoding = resource.metadata.get('ContentEncoding')
    else:
      content_encoding = None

    if content_encoding is not None:
      return content_encoding

    complete_resource = self.get_object_metadata(resource.bucket, resource.name,
                                                 resource.generation)
    return complete_resource.metadata.get('ContentEncoding')

  @_catch_client_error_raise_s3_api_error()
  def download_object(self,
                      cloud_resource,
                      download_stream,
                      compressed_encoding=False,
                      decryption_wrapper=None,
                      digesters=None,
                      download_strategy=cloud_api.DownloadStrategy.ONE_SHOT,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """See super class."""
    extra_args = {}
    if cloud_resource.generation:
      extra_args['VersionId'] = cloud_resource.generation

    if download_strategy == cloud_api.DownloadStrategy.RESUMABLE:
      response = self.client.get_object(
          Bucket=cloud_resource.bucket,
          Key=cloud_resource.name,
          Range='bytes={}-'.format(start_byte),
      )
      processed_bytes = start_byte
      for chunk in response['Body'].iter_chunks(
          scaled_integer.ParseInteger(
              properties.VALUES.storage.download_chunk_size.Get())):
        download_stream.write(chunk)
        processed_bytes += len(chunk)
        if progress_callback:
          progress_callback(processed_bytes)
    else:
      # TODO(b/172480278) Conditionally call get_object for smaller object.
      self.client.download_fileobj(
          cloud_resource.bucket,
          cloud_resource.name,
          download_stream,
          Callback=progress_callback,
          ExtraArgs=extra_args)

    # Download callback doesn't give us streaming data, so we have to
    # read whole downloaded file to update digests.
    if digesters:
      with files.BinaryFileReader(
          download_stream.name) as completed_download_stream:
        completed_download_stream.seek(0)
        for hash_algorithm in digesters:
          digesters[hash_algorithm] = hash_util.get_hash_from_file_stream(
              completed_download_stream, hash_algorithm)

    return self._get_content_encoding(cloud_resource)

    # TODO(b/161437901): Handle resumed download.
    # TODO(b/161460749): Handle download retries.

  @_catch_client_error_raise_s3_api_error()
  def delete_object(self, object_url, request_config):
    """See super class."""
    del request_config  # Unused.

    delete_object_kwargs = {
        'Bucket': object_url.bucket_name,
        'Key': object_url.object_name,
    }
    if object_url.generation:
      delete_object_kwargs['VersionId'] = object_url.generation
    return self.client.delete_object(**delete_object_kwargs)

  @_catch_client_error_raise_s3_api_error()
  def get_object_metadata(self,
                          bucket_name,
                          object_name,
                          generation=None,
                          fields_scope=None):
    """See super class."""
    request = {'Bucket': bucket_name, 'Key': object_name}

    # The VersionId keyword argument to head_object is not nullable if it is
    # present, so only include it in the function call if it has a value.
    if generation is not None:
      request['VersionId'] = generation

    try:
      object_dict = self.client.head_object(**request)
    except botocore.exceptions.ClientError as e:
      _raise_if_not_found_error(
          e,
          storage_url.CloudUrl(storage_url.ProviderPrefix.S3, bucket_name,
                               object_name, generation).url_string)
      raise e

    # User requested ACL's with FieldsScope.FULL.
    if fields_scope is cloud_api.FieldsScope.FULL:
      try:
        acl_response = self.client.get_object_acl(**request)
        acl_response.pop('ResponseMetadata', None)
        object_dict['ACL'] = acl_response
      except botocore.exceptions.ClientError as error:
        object_dict['ACL'] = errors.S3ApiError(error)

    return s3_metadata_util.get_object_resource_from_s3_response(
        object_dict, bucket_name, object_name)

  def _upload_using_managed_transfer_utility(self, source_stream,
                                             destination_resource, extra_args):
    """Uploads the data using boto3's managed transfer utility.

    Calls the upload_fileobj method which performs multi-threaded multipart
    upload automatically. Performs slightly better than put_object API method.
    However, upload_fileobj cannot perform data intergrity checks and we have
    to use put_object method in such cases.

    Args:
      source_stream (a file-like object): A file-like object to upload. At a
        minimum, it must implement the read method, and must return bytes.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Represents the metadata for the destination object.
      extra_args (dict): Extra arguments that may be passed to the client
        operation.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.
    """
    bucket_name = destination_resource.storage_url.bucket_name
    object_name = destination_resource.storage_url.object_name
    self.client.upload_fileobj(
        Fileobj=source_stream,
        Bucket=bucket_name,
        Key=object_name,
        ExtraArgs=extra_args)
    return self.get_object_metadata(bucket_name, object_name)

  def _upload_using_put_object(self, source_stream, destination_resource,
                               extra_args):
    """Uploads the source stream using the put_object API method.

    Args:
      source_stream (a seekable file-like object): The stream of bytes to be
        uploaded.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Represents the metadata for the destination object.
      extra_args (dict): Extra arguments that may be passed to the client
        operation.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.
    """
    kwargs = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'Body': source_stream,
    }
    kwargs.update(extra_args)
    response = self.client.put_object(**kwargs)
    return s3_metadata_util.get_object_resource_from_s3_response(
        response, destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name)

  @_catch_client_error_raise_s3_api_error()
  def upload_object(self,
                    source_stream,
                    destination_resource,
                    request_config,
                    progress_callback=None,
                    serialization_data=None,
                    tracker_callback=None,
                    upload_strategy=cloud_api.UploadStrategy.SIMPLE):
    """See super class."""
    del progress_callback, serialization_data, tracker_callback

    if upload_strategy != cloud_api.UploadStrategy.SIMPLE:
      raise command_errors.Error(
          'Invalid upload strategy: {}.'.format(upload_strategy.value))

    # All fields common to both put_object and upload_fileobj are added
    # to the extra_args dict.
    extra_args = s3_metadata_util.get_metadata_dict_from_request_config(
        request_config)

    if request_config.md5_hash:
      # The upload_fileobj method can perform multipart uploads, so it cannot
      # validate with user-provided MD5 hashes. Hence we use the put_object API
      # method if MD5 validation is requested.
      if request_config.size > MAX_PUT_OBJECT_SIZE:
        raise errors.S3ApiError(
            'Cannot upload to destination: {url} because MD5 validation can'
            ' only be performed for file size <= {maxsize} Bytes. Current file'
            ' size is {filesize} Bytes. You can remove the MD5 validation'
            ' requirement to complete the upload'.format(
                url=destination_resource.storage_url.url_string,
                maxsize=MAX_PUT_OBJECT_SIZE,
                filesize=request_config.size))

      return self._upload_using_put_object(source_stream, destination_resource,
                                           extra_args)
    else:
      # We default to calling the upload_fileobj method provided by boto3 which
      # is a managed-transfer utility that can perform mulitpart uploads
      # automatically. It can be used for non-seekable source_streams as well.
      return self._upload_using_managed_transfer_utility(
          source_stream, destination_resource, extra_args)
