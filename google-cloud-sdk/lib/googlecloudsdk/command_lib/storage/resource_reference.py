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
"""Classes for cloud/file references yielded by storage iterators."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage.storage_url import CloudUrl


class Resource(object):
  """Base class for a reference to one fully expanded iterator result.

  This allows polymorphic iteration over wildcard-iterated URLs.  The
  reference contains a fully expanded URL string containing no wildcards and
  referring to exactly one entity (if a wildcard is contained, it is assumed
  this is part of the raw string and should never be treated as a wildcard).

  Each reference represents a Bucket, Object, or Prefix.  For filesystem URLs,
  Objects represent files and Prefixes represent directories.

  The metadata_object member contains the underlying object as it was retrieved.
  It is populated by the calling iterator, which may only request certain
  fields to reduce the number of server requests.

  For filesystem and prefix URLs, metadata_object is not populated.

  Attributes:
    storage_url (StorageUrl): A StorageUrl object representing the resource
  """

  def __init__(self, storage_url):
    """Initialize the Resource object.

    Args:
      storage_url (StorageUrl): A StorageUrl object representing the resource.
    """
    self.storage_url = storage_url

  def __str__(self):
    return self.storage_url.url_string

  def __eq__(self, other):
    return (
        isinstance(other, self.__class__) and
        self.storage_url == other.storage_url
    )


class BucketResource(Resource):
  """Class representing a bucket.

  Attributes:
    storage_url (StorageUrl): A StorageUrl object representing the bucket
    metadata_object (apitools.messages.Bucket): Bucket instance.
    additional_metadata (dict): Key-value pairs representing additional
      metadata. This is needed for S3, where we want to preserve S3 metadata,
      which cannot be added to apitools.messages.Bucket
  """

  def __init__(self, storage_url, metadata_object, additional_metadata=None):
    super(BucketResource, self).__init__(storage_url)
    self.metadata_object = metadata_object
    self.additional_metadata = additional_metadata

  @classmethod
  def from_gcs_metadata_object(cls, provider, metadata_object):
    """Helper method to generate the instance from metadata_object."""
    return cls(CloudUrl(scheme=provider, bucket_name=metadata_object.name),
               metadata_object)

  def __eq__(self, other):
    return (
        super().__eq__(other) and
        self.metadata_object == other.metadata_object and
        self.additional_metadata == other.additional_metadata
    )


class ObjectResource(Resource):
  """Class representing a  cloud object.

  Attributes:
    storage_url (StorageUrl): A StorageUrl object representing the object
    metadata_object (apitools.messages.Object):
    additional_metadata (dict): key-value pairs od additional_metadata.
      This is needed for S3, where we want to preserve S3 metadata which
      cannot be added to apitools.messages.Bucket
  """

  def __init__(self, storage_url, metadata_object, additional_metadata=None):
    super(ObjectResource, self).__init__(storage_url)
    self.metadata_object = metadata_object
    self.additional_metadata = additional_metadata

  @classmethod
  def from_gcs_metadata_object(cls, provider, metadata_object):
    """Helper method to generate the instance from metadata_object."""
    storage_url = CloudUrl(
        scheme=provider,
        bucket_name=metadata_object.bucket,
        object_name=metadata_object.name,
        generation=metadata_object.generation)
    return cls(storage_url, metadata_object)

  def __eq__(self, other):
    return (
        super().__eq__(other) and
        self.metadata_object == other.metadata_object and
        self.additional_metadata == other.additional_metadata
    )


class PrefixResource(Resource):
  """Class representing a  cloud object.

  Attributes:
    storage_url (StorageUrl): A StorageUrl object representing the prefix
    prefix (str): A string representing the prefix.
  """

  def __init__(self, storage_url, prefix):
    """Initialize the PrefixResource object.

    Args:
      storage_url (StorageUrl): A StorageUrl object representing the prefix
      prefix (str): A string representing the prefix.
    """
    super(PrefixResource, self).__init__(storage_url)
    self.prefix = prefix


class FileObjectResource(Resource):
  """Wrapper for a filesystem file."""


class FileDirectoryResource(Resource):
  """Wrapper for a File system directory."""


