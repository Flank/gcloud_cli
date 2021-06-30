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

import collections
import json

from googlecloudsdk.command_lib.storage import errors


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
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
  """
  TYPE_STRING = 'resource'

  def __init__(self, storage_url_object):
    """Initialize the Resource object.

    Args:
      storage_url_object (StorageUrl): A StorageUrl object representing the
          resource.
    """
    self.storage_url = storage_url_object

  def __repr__(self):
    return self.storage_url.url_string

  def __eq__(self, other):
    return (
        isinstance(other, self.__class__) and
        self.storage_url == other.storage_url
    )

  def is_container(self):
    raise NotImplementedError('is_container must be overridden.')


class CloudResource(Resource):
  """For Resource classes with CloudUrl's.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
        hosts the bucket.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
  """
  TYPE_STRING = 'cloud_resource'

  @property
  def scheme(self):
    # TODO(b/168690302): Stop using string scheme in storage_url.py.
    return self.storage_url.scheme

  def get_json_dump(self):
    raise NotImplementedError('get_json_dump must be overridden.')


class BucketResource(CloudResource):
  """Class representing a bucket.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the bucket.
    name (str): Name of bucket.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
      hosts the bucket.
    etag (str|None): HTTP version identifier.
    location (str|None): Represents region bucket was created in.
    metadata (object|dict|None): Cloud-provider specific data type for holding
      bucket metadata.
    retention_period (int|None): Default time to hold items in bucket before
      before deleting in seconds.
    storage_class (str|None): Default storage class for objects in bucket.
    uniform_bucket_level_access (bool): True if all objects in the bucket share
      ACLs rather than the default, fine-grain ACL control.
  """
  TYPE_STRING = 'cloud_bucket'

  def __init__(self,
               storage_url_object,
               etag=None,
               location=None,
               metadata=None,
               retention_period=None,
               storage_class=None,
               uniform_bucket_level_access=False):
    """Initializes resource. Args are a subset of attributes."""
    super(BucketResource, self).__init__(storage_url_object)
    self.etag = etag
    self.location = location
    self.metadata = metadata
    self.retention_period = retention_period
    self.storage_class = storage_class
    self.uniform_bucket_level_access = uniform_bucket_level_access

  @property
  def name(self):
    return self.storage_url.bucket_name

  def __eq__(self, other):
    return (super(BucketResource, self).__eq__(other) and
            self.etag == other.etag and self.location == other.location and
            self.metadata == other.metadata and
            self.retention_period == other.retention_period and
            self.storage_class == other.storage_class and
            self.uniform_bucket_level_access
            == other.uniform_bucket_level_access)

  def is_container(self):
    return True

  def get_json_dump(self):
    super(BucketResource).get_json_dump()


class ObjectResource(CloudResource):
  """Class representing a cloud object confirmed to exist.

  Attributes:
    TYPE_STRING (str): String representing the resource's type.
    storage_url (StorageUrl): A StorageUrl object representing the object.
    content_type (str|None): A MIME type describing the object's content.
    creation_time (datetime|None): Time the object was created.
    etag (str|None): HTTP version identifier.
    crc32c_hash (str|None): Base64-encoded digest of crc32c hash.
    md5_hash (str|None): Base64-encoded digest of md5 hash.
    metageneration (int|None): Generation object's metadata.
    metadata (object|dict|None): Cloud-specific metadata type.
    size (int|None): Size of object in bytes.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
        hosts the object.
    bucket (str): Bucket that contains the object.
    name (str): Name of object.
    generation (str|None): Generation (or "version") of the underlying object.
  """
  TYPE_STRING = 'cloud_object'

  def __init__(self,
               storage_url_object,
               content_type=None,
               creation_time=None,
               etag=None,
               crc32c_hash=None,
               md5_hash=None,
               metadata=None,
               metageneration=None,
               size=None):
    """Initializes resource. Args are a subset of attributes."""
    super(ObjectResource, self).__init__(storage_url_object)
    self.content_type = content_type
    self.creation_time = creation_time
    self.etag = etag
    self.crc32c_hash = crc32c_hash
    self.md5_hash = md5_hash
    self.metageneration = metageneration
    self.metadata = metadata
    self.size = size

  @property
  def bucket(self):
    return self.storage_url.bucket_name

  @property
  def name(self):
    return self.storage_url.object_name

  @property
  def generation(self):
    return self.storage_url.generation

  def __eq__(self, other):
    return (super(ObjectResource, self).__eq__(other) and
            self.content_type == other.content_type and
            self.etag == other.etag and self.generation == other.generation and
            self.crc32c_hash == other.crc32c_hash and
            self.md5_hash == other.md5_hash and self.metadata == other.metadata)

  def is_container(self):
    return False

  def get_json_dump(self):
    super(ObjectResource).get_json_dump()


class PrefixResource(Resource):
  """Class representing a  cloud object.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the prefix.
    prefix (str): A string representing the prefix.
  """
  TYPE_STRING = 'prefix'

  def __init__(self, storage_url_object, prefix):
    """Initialize the PrefixResource object.

    Args:
      storage_url_object (StorageUrl): A StorageUrl object representing the
          prefix.
      prefix (str): A string representing the prefix.
    """
    super(PrefixResource, self).__init__(storage_url_object)
    self.prefix = prefix

  def is_container(self):
    return True

  def get_json_dump(self):
    return json.dumps(collections.OrderedDict([
        ('url', self.storage_url.versionless_url_string),
        ('type', self.TYPE_STRING),
    ]), indent=2)


class FileObjectResource(Resource):
  """Wrapper for a filesystem file.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
    md5_hash (bytes): Base64-encoded digest of md5 hash.
  """
  TYPE_STRING = 'file_object'

  def __init__(self, storage_url_object, md5_hash=None):
    """Initializes resource. Args are a subset of attributes."""
    super(FileObjectResource, self).__init__(storage_url_object)
    self.md5_hash = md5_hash

  def is_container(self):
    return False


class FileDirectoryResource(Resource):
  """Wrapper for a File system directory."""
  TYPE_STRING = 'file_directory'

  def is_container(self):
    return True


class UnknownResource(Resource):
  """Represents a resource that may or may not exist."""
  TYPE_STRING = 'unknown'

  def is_container(self):
    raise errors.ValueCannotBeDeterminedError(
        'Unknown whether or not UnknownResource is a container.')
