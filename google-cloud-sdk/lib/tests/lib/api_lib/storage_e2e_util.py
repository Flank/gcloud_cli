# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Support for e2e tests that use the Cloud Storage API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core.util import retry


# creates/deletes are eventually consistent; this should be long enough
_NUM_RETRIES = 3
_WAIT_MS = 1000


@retry.RetryOnException(max_retrials=_NUM_RETRIES,
                        exponential_sleep_multiplier=1.5, sleep_ms=_WAIT_MS)
def _CleanUpBucket(storage_client, bucket_ref):
  """Removes a bucket and its contents."""
  # The bucket must be empty before we can delete it
  delete_tasks = []
  for obj in storage_client.ListBucket(bucket_ref):
    delete_tasks.append(storage_parallel.ObjectDeleteTask(
        storage_util.ObjectReference.FromMessage(obj)))
  storage_parallel.DeleteObjects(delete_tasks)
  storage_client.DeleteBucket(bucket_ref)


@contextlib.contextmanager
def CloudStorageBucket(storage_client, name, project):
  """Creates a Cloud Storage bucket and deletes it on exit.

  Args:
    storage_client: googlecloudsdk.api_lib.storage_api.StorageClient
    name: str, the name of the bucket to create
    project: str, the name of the project in which to create the bucket

  Yields:
    storage_util.BucketReference for the created bucket.
  """
  storage_client.CreateBucketIfNotExists(name, project=project)
  bucket_ref = storage_util.BucketReference.FromUrl(name)
  try:
    yield bucket_ref
  finally:
    _CleanUpBucket(storage_client, bucket_ref)


@contextlib.contextmanager
def GcsFile(storage_client, local_path, target_obj_ref):
  """Copies a file to Cloud Storage and deletes it on exit.

  This isn't as reliable as it could be, since there's no retry on the object
  deletion; it should only be used when there's a fallback method of deletion
  (e.g. the above CloudStorageBucket context manager).

  Args:
    storage_client: googlecloudsdk.api_lib.storage_api.StorageClient
    local_path: str, the path to the file on disk to be uploaded
    target_obj_ref: storage_util.ObjectReference, the path of the file on GCS.

  Yields:
    storage_util.ObjectReference for the created object.
  """
  storage_client.CopyFileToGCS(local_path, target_obj_ref)
  try:
    yield target_obj_ref
  finally:
    storage_client.DeleteObject(target_obj_ref)
