# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API interface for interacting with cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.command_lib.storage import storage_url


class Capability(enum.Enum):
  """Used to track API capabilities relevant to logic in tasks."""
  COMPOSE_OBJECTS = 'COMPOSE_OBJECTS'
  CLIENT_SIDE_HASH_VALIDATION = 'CLIENT_SIDE_HASH_VALIDATION'
  RESUMABLE_UPLOAD = 'RESUMABLE_UPLOAD'
  SLICED_DOWNLOAD = 'SLICED_DOWNLOAD'


class DownloadStrategy(enum.Enum):
  """Enum class for specifying download strategy."""
  ONE_SHOT = 'oneshot'
  RESUMABLE = 'resumable'


class UploadStrategy(enum.Enum):
  """Enum class for specifying upload strategy."""
  SIMPLE = 'simple'
  RESUMABLE = 'resumable'


class FieldsScope(enum.Enum):
  """Values used to determine fields and projection values for API calls."""
  FULL = 1
  NO_ACL = 2
  SHORT = 3


DEFAULT_PROVIDER = storage_url.ProviderPrefix.GCS
NUM_ITEMS_PER_LIST_PAGE = 1000


class CloudApi(object):
  """Abstract base class for interacting with cloud storage providers.

  Implementations of the Cloud API are not guaranteed to be thread-safe.
  Behavior when calling a Cloud API instance simultaneously across
  threads is undefined and doing so will likely cause errors. Therefore,
  a separate instance of the Cloud API should be instantiated per-thread.

  Attributes:
    capabilities (set[Capability]): If a Capability is present in this set, this
      API can be used to execute related logic in tasks.
  """
  capabilities = set()

  def create_bucket(self, bucket_resource, fields_scope=None):
    """Creates a new bucket with the specified metadata.

    Args:
      bucket_resource (resource_reference.BucketResource):
        Resource containing metadata for new bucket.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.

    Returns:
      resource_reference.BucketResource representing new bucket.
    """
    raise NotImplementedError('create_bucket must be overridden.')

  def delete_bucket(self, bucket_name, request_config):
    """Deletes a bucket.

    Args:
      bucket_name (str): Name of the bucket to delete.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('delete_bucket must be overridden.')

  def get_bucket(self, bucket_name, fields_scope=None):
    """Gets bucket metadata.

    Args:
      bucket_name (str): Name of the bucket.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Returns:
      resource_reference.BucketResource containing the bucket metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('get_bucket must be overridden.')

  def patch_bucket(self, bucket_resource, request_config, fields_scope=None):
    """Patches bucket metadata.

    Args:
      bucket_resource (BucketResource): Contans metadata to patch.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Returns:
      resource_reference.BucketResource containing the bucket metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
          this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('patch_bucket must be overridden.')

  def list_buckets(self, fields_scope=None):
    """Lists bucket metadata for the given project.

    Args:
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Yields:
      Iterator over resource_reference.BucketResource objects

    Raises:
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('list_buckets must be overridden.')

  def list_objects(self,
                   bucket_name,
                   prefix=None,
                   delimiter=None,
                   all_versions=None,
                   fields_scope=None):
    """Lists objects (with metadata) and prefixes in a bucket.

    Args:
      bucket_name (str): Bucket containing the objects.
      prefix (str): Prefix for directory-like behavior.
      delimiter (str): Delimiter for directory-like behavior.
      all_versions (boolean): If true, list all object versions.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Yields:
      Iterator over resource_reference.ObjectResource objects.

    Raises:
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('list_objects must be overridden.')

  def delete_object(self, object_url, request_config):
    """Deletes an object.

    Args:
      object_url (storage_url.CloudUrl): Url of object to delete.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
          this interface.
    """
    raise NotImplementedError('delete_object must be overridden.')

  def get_object_metadata(self,
                          bucket_name,
                          object_name,
                          generation=None,
                          fields_scope=None):
    """Gets object metadata.

    If decryption is supported by the implementing class, this function will
    read decryption keys from configuration and appropriately retry requests to
    encrypted objects with the correct key.

    Args:
      bucket_name (str): Bucket containing the object.
      object_name (str): Object name.
      generation (string): Generation of the object to retrieve.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Returns:
      resource_reference.ObjectResource with object metadata.

    Raises:
      CloudApiError: API returned an error.
      NotFoundError: Raised if object does not exist.
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('get_object_metadata must be overridden.')

  def patch_object_metadata(self,
                            bucket_name,
                            object_name,
                            object_resource,
                            request_config,
                            fields_scope=None,
                            generation=None):
    """Updates object metadata with patch semantics.

    Args:
      bucket_name (str): Bucket containing the object.
      object_name (str): Object name.
      object_resource (resource_reference.ObjectResource): Contains metadata
        that will be used to update cloud object. May have different name than
        object_name argument.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.
      generation (string): Generation (or version) of the object to update.

    Returns:
      resource_reference.ObjectResource with patched object metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
      ValueError: Invalid fields_scope.
    """
    raise NotImplementedError('patch_object_metadata must be overridden.')

  def copy_object(self,
                  source_resource,
                  destination_resource,
                  request_config,
                  progress_callback=None):
    """Copies an object within the cloud of one provider.

    Args:
      source_resource (resource_reference.ObjectResource): Resource for
        source object. Must have been confirmed to exist in the cloud.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Resource for destination object. Existence doesn't have to be confirmed.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      progress_callback (function): Optional callback function for progress
        notifications. Receives calls with arguments (bytes_transferred,
        total_size).

    Returns:
      resource_reference.ObjectResource with new object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('copy_object must be overridden')

  def download_object(self,
                      cloud_resource,
                      download_stream,
                      compressed_encoding=False,
                      decryption_wrapper=None,
                      digesters=None,
                      download_strategy=DownloadStrategy.ONE_SHOT,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """Gets object data.

    Args:
      cloud_resource (resource_reference.ObjectResource): Contains
        metadata and information about object being downloaded.
      download_stream (stream): Stream to send the object data to.
      compressed_encoding (bool): If true, object is stored with a compressed
        encoding.
      decryption_wrapper (CryptoKeyWrapper):
        utils.encryption_helper.CryptoKeyWrapper that can optionally be added
        to decrypt an encrypted object.
      digesters (dict): Dict of {string : digester}, where string is the name of
        a hash algorithm, and digester is a validation digester object that
        update(bytes) and digest() using that algorithm. Implementation can
        set the digester value to None to indicate supports bytes were not
        successfully digested on-the-fly.
      download_strategy (DownloadStrategy): Cloud API download strategy to use
        for download.
      progress_callback (function): Optional callback function for progress
        notifications. Receives calls with arguments (bytes_transferred,
        total_size).
      start_byte (int): Starting point for download (for resumable downloads and
        range requests). Can be set to negative to request a range of bytes
        (python equivalent of [:-3]).
      end_byte (int): Ending byte number, inclusive, for download (for range
        requests). If None, download the rest of the object.

    Returns:
      Content-encoding string if it was detected that the server sent an encoded
      object during transfer. Otherwise, None.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('download_object must be overridden.')

  def upload_object(self,
                    source_stream,
                    destination_resource,
                    request_config,
                    progress_callback=None,
                    serialization_data=None,
                    tracker_callback=None,
                    upload_strategy=UploadStrategy.SIMPLE):
    """Uploads object data and metadata.

    Args:
      source_stream (stream): Seekable stream of object data.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Contains the correct metadata to upload.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      progress_callback (function): Callback function for progress
        notifications. Receives calls with arguments (bytes_transferred,
        total_size).
      serialization_data (dict): API-specific data needed to resume an upload.
        Only used with UploadStrategy.RESUMABLE.
      tracker_callback (Callable[[dict], None]): Function that writes a tracker
        file with serialization data. Only used with UploadStrategy.RESUMABLE.
      upload_strategy (UploadStrategy): Strategy to use for this upload.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('upload_object must be overridden.')

  def compose_objects(self, source_resources, destination_resource,
                      request_config):
    """Concatenates a list of objects into a new object.

    Args:
      source_resources (list[ObjectResource|UnknownResource]): The objects
        to compose.
      destination_resource (resource_reference.UnknownResource): Metadata for
        the resulting composite object.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Returns:
      resource_reference.ObjectResource with composite object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('compose_object must be overridden.')
