# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Tools for making the most of GcsApi metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import encoding_helper

from googlecloudsdk.api_lib.storage import gcs_metadata_field_converters
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference

# Similar to CORS above, we need a sentinel value allowing us to specify
# when a default object ACL should be private (containing no entries).
# A defaultObjectAcl value of [] means don't modify the default object ACL.
# A value of [PRIVATE_DEFAULT_OBJ_ACL] means create an empty/private default
# object ACL.
PRIVATE_DEFAULT_OBJECT_ACL = apis.GetMessagesModule(
    'storage', 'v1').ObjectAccessControl(id='PRIVATE_DEFAULT_OBJ_ACL')


def copy_select_object_metadata(source_metadata, destination_metadata,
                                request_config):
  """Copies specific metadata from source_metadata to destination_metadata.

  The API manually generates metadata for destination objects most of the time,
  but here are some fields that may not be populated.

  Args:
    source_metadata (messages.Object): Metadata from source object.
    destination_metadata (messages.Object): Metadata for destination object.
    request_config (request_config_factory.RequestConfig): Holds context info
      about the copy operation.
  """
  destination_metadata.cacheControl = source_metadata.cacheControl
  destination_metadata.contentDisposition = source_metadata.contentDisposition
  destination_metadata.contentEncoding = source_metadata.contentEncoding
  destination_metadata.contentLanguage = source_metadata.contentLanguage
  destination_metadata.contentType = source_metadata.contentType
  destination_metadata.crc32c = source_metadata.crc32c
  destination_metadata.customTime = source_metadata.customTime
  destination_metadata.md5Hash = source_metadata.md5Hash
  destination_metadata.metadata = copy.deepcopy(source_metadata.metadata)

  if request_config.resource_args.preserve_acl:
    if not source_metadata.acl:
      raise ValueError('Preserve ACL flag present but found no source ACLs.')
    destination_metadata.acl = copy.deepcopy(source_metadata.acl)


def get_apitools_metadata_from_url(cloud_url):
  """Takes storage_url.CloudUrl and returns appropriate Apitools message."""
  messages = apis.GetMessagesModule('storage', 'v1')
  if cloud_url.is_bucket():
    return messages.Bucket(name=cloud_url.bucket_name)
  elif cloud_url.is_object():
    generation = int(cloud_url.generation) if cloud_url.generation else None
    return messages.Object(
        name=cloud_url.object_name,
        bucket=cloud_url.bucket_name,
        generation=generation)


def get_bucket_resource_from_metadata(metadata):
  """Helper method to generate a BucketResource instance from GCS metadata.

  Args:
    metadata (messages.Bucket): Extract resource properties from this.

  Returns:
    BucketResource with properties populated by metadata.
  """
  url = storage_url.CloudUrl(
      scheme=storage_url.ProviderPrefix.GCS, bucket_name=metadata.name)
  retention_period = getattr(metadata.retentionPolicy, 'retentionPeriod', None)
  uniform_bucket_level_access = getattr(
      getattr(metadata.iamConfiguration, 'uniformBucketLevelAccess', False),
      'enabled', False)
  return gcs_resource_reference.GcsBucketResource(
      url,
      etag=metadata.etag,
      location=metadata.location,
      metadata=metadata,
      retention_period=retention_period,
      default_storage_class=metadata.storageClass,
      uniform_bucket_level_access=uniform_bucket_level_access)


def get_metadata_from_bucket_resource(resource):
  """Helper method to generate Apitools metadata instance from BucketResource.

  Args:
    resource (BucketResource): Extract metadata properties from this.

  Returns:
    messages.Bucket with properties populated by resource.
  """
  messages = apis.GetMessagesModule('storage', 'v1')
  metadata = messages.Bucket(
      name=resource.name,
      etag=resource.etag,
      location=resource.location,
      storageClass=resource.default_storage_class)

  if resource.retention_period:
    metadata.retentionPolicy = messages.Bucket.RetentionPolicyValue(
        retentionPeriod=resource.retention_period)
  if resource.uniform_bucket_level_access:
    metadata.iamConfiguration = messages.Bucket.IamConfigurationValue(
        uniformBucketLevelAccess=messages.Bucket.IamConfigurationValue
        .UniformBucketLevelAccessValue(
            enabled=resource.uniform_bucket_level_access))

  return metadata


def get_object_resource_from_metadata(metadata):
  """Helper method to generate a ObjectResource instance from GCS metadata.

  Args:
    metadata (messages.Object): Extract resource properties from this.

  Returns:
    ObjectResource with properties populated by metadata.
  """
  if metadata.generation is not None:
    # Generation may be 0 integer, which is valid although falsy.
    generation = str(metadata.generation)
  else:
    generation = None
  url = storage_url.CloudUrl(
      scheme=storage_url.ProviderPrefix.GCS,
      bucket_name=metadata.bucket,
      object_name=metadata.name,
      generation=generation)

  if metadata.customerEncryption:
    key_hash = metadata.customerEncryption.keySha256
  else:
    key_hash = None

  return gcs_resource_reference.GcsObjectResource(
      url,
      content_type=metadata.contentType,
      creation_time=metadata.timeCreated,
      decryption_key_hash=key_hash,
      etag=metadata.etag,
      crc32c_hash=metadata.crc32c,
      md5_hash=metadata.md5Hash,
      metadata=metadata,
      metageneration=metadata.metageneration,
      size=metadata.size)


def update_bucket_metadata_from_request_config(bucket_metadata, request_config):
  """Sets Apitools Bucket fields based on values in request_config."""
  resource_args = getattr(request_config, 'resource_args', None)
  if not resource_args:
    return

  if resource_args.cors_file_path is not None:
    bucket_metadata.cors = gcs_metadata_field_converters.process_cors(
        resource_args.cors_file_path)
  if resource_args.default_encryption_key is not None:
    bucket_metadata.encryption = (
        gcs_metadata_field_converters.process_default_encryption_key(
            resource_args.default_encryption_key))
  if resource_args.default_event_based_hold is not None:
    bucket_metadata.defaultEventBasedHold = (
        resource_args.default_event_based_hold)
  if resource_args.default_storage_class is not None:
    bucket_metadata.storageClass = (
        gcs_metadata_field_converters.process_default_storage_class(
            resource_args.default_storage_class))
  if resource_args.labels_file_path is not None:
    bucket_metadata.labels = gcs_metadata_field_converters.process_labels(
        resource_args.labels_file_path)
  if resource_args.lifecycle_file_path is not None:
    bucket_metadata.lifecycle = (
        gcs_metadata_field_converters.process_lifecycle(
            resource_args.lifecycle_file_path))
  if resource_args.location is not None:
    bucket_metadata.location = resource_args.location
  if (resource_args.log_bucket is not None or
      resource_args.log_object_prefix is not None):
    bucket_metadata.logging = gcs_metadata_field_converters.process_log_config(
        resource_args.log_bucket, resource_args.log_object_prefix)
  if resource_args.requester_pays is not None:
    bucket_metadata.billing = (
        gcs_metadata_field_converters.process_requester_pays(
            bucket_metadata.billing, resource_args.requester_pays))
  if resource_args.retention_period is not None:
    bucket_metadata.retentionPolicy = (
        gcs_metadata_field_converters.process_retention_period(
            resource_args.retention_period))
  if resource_args.uniform_bucket_level_access is not None:
    bucket_metadata.iamConfiguration = (
        gcs_metadata_field_converters.process_uniform_bucket_level_access(
            bucket_metadata.iamConfiguration,
            resource_args.uniform_bucket_level_access))
  if resource_args.versioning is not None:
    bucket_metadata.versioning = (
        gcs_metadata_field_converters.process_versioning(
            resource_args.versioning))
  if (resource_args.web_error_page is not None or
      resource_args.web_main_page_suffix is not None):
    bucket_metadata.website = gcs_metadata_field_converters.process_website(
        resource_args.web_error_page, resource_args.web_main_page_suffix)


def get_cleared_bucket_fields(request_config):
  """Gets a list of fields to be included in requests despite null values."""
  cleared_fields = []
  resource_args = getattr(request_config, 'resource_args', None)
  if not resource_args:
    return cleared_fields

  if resource_args.cors_file_path == user_request_args_factory.CLEAR:
    cleared_fields.append('cors')

  if resource_args.default_encryption_key == user_request_args_factory.CLEAR:
    cleared_fields.append('encryption')

  if resource_args.default_storage_class == user_request_args_factory.CLEAR:
    cleared_fields.append('storageClass')

  if resource_args.labels_file_path == user_request_args_factory.CLEAR:
    cleared_fields.append('labels')

  if resource_args.lifecycle_file_path == user_request_args_factory.CLEAR:
    cleared_fields.append('lifecycle')

  if (resource_args.log_bucket == resource_args.log_object_prefix ==
      user_request_args_factory.CLEAR):
    cleared_fields.append('logging')
  elif resource_args.log_bucket == user_request_args_factory.CLEAR:
    cleared_fields.append('logging.logBucket')
  elif resource_args.log_object_prefix == user_request_args_factory.CLEAR:
    cleared_fields.append('logging.logObjectPrefix')

  if resource_args.retention_period == user_request_args_factory.CLEAR:
    cleared_fields.append('retentionPolicy')

  if (resource_args.web_error_page
      == resource_args.web_main_page_suffix == user_request_args_factory.CLEAR):
    cleared_fields.append('website')
  elif resource_args.web_error_page == user_request_args_factory.CLEAR:
    cleared_fields.append('website.notFoundPage')
  elif resource_args.web_main_page_suffix == user_request_args_factory.CLEAR:
    cleared_fields.append('website.mainPageSuffix')

  return cleared_fields


def _process_value_or_clear_flag(metadata, key, value):
  """Sets appropriate metadata based on value."""
  if value == user_request_args_factory.CLEAR:
    setattr(metadata, key, None)
  elif value is not None:
    setattr(metadata, key, value)


def update_object_metadata_from_request_config(object_metadata,
                                               request_config,
                                               file_path=None):
  """Sets Apitools Object fields based on values in request_config.

  User custom metadata takes precedence over preserved POSIX data.
  Gzip metadata changes take precedence over user custom metadata.

  Args:
    object_metadata (storage_v1_messages.Object): Existing object metadata.
    request_config (request_config): May contain data to add to object_metadata.
    file_path (str|None): If present, used for parsing POSIX data from a file on
      the system for the --preserve-posix flag. This flag's presence is
      indicated by the system_posix_data field on request_config.
  """
  resource_args = request_config.resource_args
  if (resource_args and
      resource_args.custom_metadata is user_request_args_factory.CLEAR):
    object_metadata.metadata = None
  else:
    should_parse_file_posix = request_config.system_posix_data and file_path
    should_add_custom_metadata = (
        resource_args and resource_args.custom_metadata is not None)
    if should_parse_file_posix or should_add_custom_metadata:
      messages = apis.GetMessagesModule('storage', 'v1')
      if not object_metadata.metadata:
        object_metadata.metadata = messages.Object.MetadataValue()

      custom_metadata_dict = encoding_helper.MessageToDict(
          object_metadata.metadata)

      if should_parse_file_posix:
        posix_attributes = posix_util.get_posix_attributes_from_file(file_path)
        posix_util.update_custom_metadata_dict_with_posix_attributes(
            custom_metadata_dict, posix_attributes)

      if should_add_custom_metadata:
        custom_metadata_dict.update(resource_args.custom_metadata)

      object_metadata.metadata = encoding_helper.DictToMessage(
          custom_metadata_dict, messages.Object.MetadataValue)

  should_gzip_locally = gzip_util.should_gzip_locally(
      request_config.gzip_settings, file_path)
  if should_gzip_locally:
    content_encoding = 'gzip'
  else:
    content_encoding = getattr(resource_args, 'content_encoding', None)
  _process_value_or_clear_flag(object_metadata, 'contentEncoding',
                               content_encoding)
  if should_gzip_locally:
    cache_control = 'no-transform'
  else:
    cache_control = getattr(resource_args, 'cache_control', None)
  _process_value_or_clear_flag(object_metadata, 'cacheControl', cache_control)

  if not resource_args:
    return

  _process_value_or_clear_flag(object_metadata, 'contentDisposition',
                               resource_args.content_disposition)
  _process_value_or_clear_flag(object_metadata, 'contentLanguage',
                               resource_args.content_language)
  _process_value_or_clear_flag(object_metadata, 'customTime',
                               resource_args.custom_time)
  _process_value_or_clear_flag(object_metadata, 'contentType',
                               resource_args.content_type)
  _process_value_or_clear_flag(object_metadata, 'md5Hash',
                               resource_args.md5_hash)
  _process_value_or_clear_flag(object_metadata, 'storageClass',
                               resource_args.storage_class)

  if (resource_args.encryption_key and
      resource_args.encryption_key.type == encryption_util.KeyType.CMEK):
    object_metadata.kmsKeyName = resource_args.encryption_key.key
