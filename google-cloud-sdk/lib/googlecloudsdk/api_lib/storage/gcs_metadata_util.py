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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference


def copy_select_object_metadata(source_metadata, destination_metadata):
  """Copies specific metadata from source_metadata to destination_metadata.

  The API manually generates metadata for destination objects most of the time,
  but here are some fields that may not be populated.

  Args:
    source_metadata (messages.Object): Metadata from source object.
    destination_metadata (messages.Object): Metadata for destination object.
  """
  destination_metadata.cacheControl = source_metadata.cacheControl
  destination_metadata.contentDisposition = source_metadata.contentDisposition
  destination_metadata.contentEncoding = source_metadata.contentEncoding
  destination_metadata.contentLanguage = source_metadata.contentLanguage
  destination_metadata.contentType = source_metadata.contentType
  destination_metadata.customTime = source_metadata.customTime
  destination_metadata.md5Hash = source_metadata.md5Hash
  destination_metadata.metadata = copy.deepcopy(source_metadata.metadata)


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
  return gcs_resource_reference.GcsBucketResource(
      url, etag=metadata.etag, metadata=metadata)


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
  return gcs_resource_reference.GcsObjectResource(
      url,
      creation_time=metadata.timeCreated,
      etag=metadata.etag,
      md5_hash=metadata.md5Hash,
      metadata=metadata,
      metageneration=metadata.metageneration,
      size=metadata.size)
