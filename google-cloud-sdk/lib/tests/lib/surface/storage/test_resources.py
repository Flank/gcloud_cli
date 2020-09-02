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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url


def get_bucket_resource(scheme, name):
  messages = apis.GetMessagesModule('storage', 'v1')
  metadata = messages.Bucket(name=name)
  return resource_reference.BucketResource.from_gcs_metadata_object(
      scheme, metadata)


def get_object_resource(scheme, bucket, name):
  messages = apis.GetMessagesModule('storage', 'v1')
  metadata = messages.Object(bucket=bucket, name=name)
  return resource_reference.ObjectResource.from_gcs_metadata_object(
      scheme, metadata)


def get_prefix_resource(scheme, bucket, prefix):
  url = storage_url.CloudUrl(scheme, bucket_name=bucket, object_name=prefix)
  return resource_reference.PrefixResource(url, prefix)


def get_file_object_resource(path):
  url = storage_url.storage_url_from_string(path)
  return resource_reference.FileObjectResource(url)


def get_file_directory_resource(path):
  url = storage_url.storage_url_from_string(path)
  return resource_reference.FileDirectoryResource(url)


def get_unknown_resource(url_str):
  url = storage_url.storage_url_from_string(url_str)
  return resource_reference.UnknownResource(url)

