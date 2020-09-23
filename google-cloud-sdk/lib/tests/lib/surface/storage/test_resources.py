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
"""Contains builder methods for classes used in tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url


def get_bucket_resource(scheme, name):
  url = storage_url.CloudUrl(scheme=scheme, bucket_name=name)
  return resource_reference.BucketResource(url)


def get_object_resource(scheme, bucket, name, generation=None):
  url = storage_url.CloudUrl(scheme, bucket, name, generation)
  return resource_reference.ObjectResource(url)


def get_prefix_resource(scheme, bucket, prefix):
  url = storage_url.CloudUrl(scheme, bucket_name=bucket, object_name=prefix)
  return resource_reference.PrefixResource(url, prefix)


def get_file_object_resource(path):
  url = storage_url.storage_url_from_string(path)
  return resource_reference.FileObjectResource(url)


def get_file_directory_resource(path):
  url = storage_url.storage_url_from_string(path)
  return resource_reference.FileDirectoryResource(url)


def get_unknown_resource(url_string):
  url = storage_url.storage_url_from_string(url_string)
  return resource_reference.UnknownResource(url)


def from_url_string(url_string):
  """Convert test resource URL to resource object. Do not use in production.

  Do not use in production because terminating with a delimiter is not always
  an accurate indicator of if a URL is a prefix. For example, a query for
  "gs://bucket/dir" may have just forgotten the trailing "/".

  Furthermore, different operating systems may have different ways to signal
  filesystem paths point to directories.

  Args:
    url_string (str): Path to resource. Ex: "gs://bucket/hi" or "/bin/cat.png".

  Returns:
    resource.Resource subclass appropriate for URL.
  """
  parsed_url = storage_url.storage_url_from_string(url_string)

  if isinstance(parsed_url, storage_url.FileUrl):
    # See docstring.
    if url_string.endswith(parsed_url.delimiter):
      return get_file_directory_resource(url_string)
    return get_file_object_resource(url_string)
  # CloudUrl because it's not a FileUrl.
  if parsed_url.is_bucket():
    return get_bucket_resource(parsed_url.scheme, parsed_url.bucket_name)
  if parsed_url.is_object() and not url_string.endswith(
      storage_url.CloudUrl.CLOUD_URL_DELIM):
    return get_object_resource(parsed_url.scheme, parsed_url.bucket_name,
                               parsed_url.object_name)
  # See docstring.
  if parsed_url.is_object() and url_string.endswith(
      storage_url.CloudUrl.CLOUD_URL_DELIM):
    return get_prefix_resource(parsed_url.scheme, parsed_url.bucket_name,
                               parsed_url.object_name)
  return get_unknown_resource(url_string)
