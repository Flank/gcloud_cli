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
"""S3 API-specific resource subclasses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util


INCOMPLETE_OBJECT_METADATA_WARNING = (
    'Use "-j", the JSON flag, to view additional S3 metadata.')


def _json_dump_recursion_helper(metadata):
  """See _get_json_dump docstring."""
  if isinstance(metadata, list):
    return [_json_dump_recursion_helper(item) for item in metadata]

  if not isinstance(metadata, dict):
    return resource_util.convert_to_json_parsable_type(metadata)

  # Sort by key to make sure dictionary always prints in correct order.
  formatted_dict = collections.OrderedDict(sorted(metadata.items()))
  for key, value in formatted_dict.items():
    if isinstance(value, dict):
      # Recursively handle dictionaries.
      formatted_dict[key] = _json_dump_recursion_helper(value)
    elif isinstance(value, list):
      # Recursively handled lists, which may contain more dicts, like ACLs.
      formatted_list = [_json_dump_recursion_helper(item) for item in value]
      if formatted_list:
        # Ignore empty lists.
        formatted_dict[key] = formatted_list
    elif value or resource_util.should_preserve_falsy_metadata_value(value):
      formatted_dict[key] = resource_util.convert_to_json_parsable_type(value)

  return formatted_dict


def _get_json_dump(resource):
  """Formats S3 resource metadata as JSON.

  Args:
    resource (S3BucketResource|S3ObjectResource): Resource object.

  Returns:
    Formatted JSON string.
  """
  return resource_util.configured_json_dumps(
      collections.OrderedDict([
          ('url', resource.storage_url.url_string),
          ('type', resource.TYPE_STRING),
          ('metadata', _json_dump_recursion_helper(resource.metadata)),
      ]))


def _get_error_or_exists_string(value):
  """Returns error if value is error or existence string."""
  if isinstance(value, errors.S3ApiError):
    return value
  else:
    return resource_util.get_exists_string(value)


def _get_error_string_or_value(value):
  """Returns the error string if value is error or the value itself."""
  if isinstance(value, errors.S3ApiError):
    return str(value)
  if isinstance(value, dict) and 'ResponseMetadata' in value:
    value.pop('ResponseMetadata')
  return value


class S3BucketResource(resource_reference.BucketResource):
  """API-specific subclass for handling metadata."""

  def get_displayable_bucket_data(self):
    # Handle versioning.
    versioning = self.metadata.get('Versioning', {})
    if isinstance(versioning, errors.S3ApiError):
      versioning_enabled = str(versioning)
    else:
      versioning_status = versioning.get('Status')
      if versioning_status == 'Enabled':
        versioning_enabled = True
      elif versioning_status == 'Suspended':
        versioning_enabled = False
      else:
        versioning_enabled = None

    # Handle requester pays.
    payer = self.metadata.get('Payer')
    if isinstance(payer, errors.S3ApiError):
      requester_pays = str(payer)
    elif payer == 'Requester':
      requester_pays = True
    elif payer == 'BucketOwner':
      requester_pays = False
    else:
      requester_pays = None

    return resource_reference.DisplayableBucketData(
        name=self.name,
        url_string=self.storage_url.url_string,
        acl=_get_error_string_or_value(self.metadata.get('ACL')),
        cors_config=_get_error_string_or_value(self.metadata.get('CORSRules')),
        encryption_config=_get_error_string_or_value(
            self.metadata.get('ServerSideEncryptionConfiguration')),
        location=_get_error_string_or_value(
            self.metadata.get('LocationConstraint')),
        logging_config=_get_error_string_or_value(
            self.metadata.get('LoggingEnabled')),
        lifecycle_config=_get_error_string_or_value(
            self.metadata.get('LifecycleConfiguration')),
        requester_pays=requester_pays,
        versioning_enabled=versioning_enabled,
        website_config=_get_error_string_or_value(self.metadata.get('Website')))

  def get_json_dump(self):
    return _get_json_dump(self)


class S3ObjectResource(resource_reference.ObjectResource):
  """API-specific subclass for handling metadata."""

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
    super(S3ObjectResource, self).__init__(
        storage_url_object,
        content_type=content_type,
        creation_time=creation_time,
        etag=etag,
        crc32c_hash=None,
        md5_hash=md5_hash,
        metadata=metadata,
        metageneration=metageneration,
        size=size)

  def get_displayable_object_data(self):
    return resource_reference.DisplayableObjectData(
        name=self.name,
        bucket=self.bucket,
        url_string=self.storage_url.url_string,
        acl=_get_error_string_or_value(self.metadata.get('ACL')),
        cache_control=self.metadata.get('CacheControl'),
        component_count=self.metadata.get('PartsCount'),
        content_disposition=self.metadata.get('ContentDisposition'),
        content_encoding=self.metadata.get('ContentEncoding'),
        content_language=self.metadata.get('ContentLanguage'),
        content_length=self.size,
        content_type=self.metadata.get('ContentType'),
        # Setting crc32c_hash as DO_NOT_DISPLAY so that it can
        # be ignored as expected by ls -L formatters. Setting it None will
        # make the list/describe commands to ignore it, but ls -L might still
        # display it if encryption_algorithm is present.
        crc32c_hash=resource_reference.DO_NOT_DISPLAY,
        encryption_algorithm=self.metadata.get('SSECustomerAlgorithm'),
        etag=self.etag,
        generation=self.generation,
        md5_hash=self.md5_hash,
        storage_class=self.metadata.get('StorageClass'),
        update_time=self.metadata.get('LastModified'),
        incomplete_warning=INCOMPLETE_OBJECT_METADATA_WARNING)

  def get_json_dump(self):
    return _get_json_dump(self)
