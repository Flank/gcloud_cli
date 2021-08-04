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

"""Task for file uploads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import functools
import os
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage import upload_stream
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_task
from googlecloudsdk.command_lib.storage.tasks.cp import upload_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import hashing
from googlecloudsdk.core.util import retry


UploadedComponent = collections.namedtuple(
    'UploadedComponent',
    ['component_number', 'object_resource']
)


class FilePartUploadTask(file_part_task.FilePartTask):
  """Uploads a range of bytes from a file."""

  def __init__(self,
               source_resource,
               destination_resource,
               offset,
               length,
               component_number=None,
               total_components=None,
               user_request_args=None):
    """Initializes task.

    Args:
      source_resource (resource_reference.FileObjectResource): Must contain
        local filesystem path to upload object. Does not need to contain
        metadata.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Must contain the full object path. Directories will not be accepted.
        Existing objects at the this location will be overwritten.
      offset (int): The index of the first byte in the upload range.
      length (int): The number of bytes in the upload range.
      component_number (int|None): If a multipart operation, indicates the
        component number.
      total_components (int|None): If a multipart operation, indicates the total
        number of components.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    super(FilePartUploadTask,
          self).__init__(source_resource, destination_resource, offset, length,
                         component_number, total_components)
    self._user_request_args = user_request_args

  def _get_upload_stream(self, digesters, task_status_queue):
    if task_status_queue:
      progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
          status_queue=task_status_queue,
          offset=self._offset,
          length=self._length,
          source_url=self._source_resource.storage_url,
          destination_url=self._destination_resource.storage_url,
          component_number=self._component_number,
          total_components=self._total_components,
          operation_name=task_status.OperationName.UPLOADING,
          process_id=os.getpid(),
          thread_id=threading.get_ident(),
      )
    else:
      progress_callback = None

    source_stream = files.BinaryFileReader(
        self._source_resource.storage_url.object_name)
    return upload_stream.UploadStream(
        source_stream, self._offset, self._length, digesters=digesters,
        progress_callback=progress_callback)

  def _get_output(self, destination_resource):
    if self._component_number is not None:
      return task.Output(
          additional_task_iterators=None,
          messages=[
              task.Message(
                  topic=task.Topic.UPLOADED_COMPONENT,
                  payload=UploadedComponent(
                      component_number=self._component_number,
                      object_resource=destination_resource)),
          ])

  def _get_digesters(self):
    provider = self._destination_resource.storage_url.scheme
    check_hashes = properties.CheckHashes(
        properties.VALUES.storage.check_hashes.Get())

    if (self._source_resource.md5_hash or
        # Boto3 implements its own unskippable validation.
        provider == storage_url.ProviderPrefix.S3 or
        check_hashes == properties.CheckHashes.NEVER):
      return {}
    return {hash_util.HashAlgorithm.MD5: hashing.get_md5()}

  def _existing_destination_is_valid(self, destination_resource):
    """Returns True if a completed temporary component can be reused."""
    digesters = self._get_digesters()
    with self._get_upload_stream(digesters, task_status_queue=None) as stream:
      stream.seek(0, whence=os.SEEK_END)  # Populates digesters.

    try:
      upload_util.validate_uploaded_object(
          digesters, destination_resource, task_status_queue=None)
      return True
    except command_errors.HashMismatchError:
      return False

  def execute(self, task_status_queue=None):
    """Performs upload."""
    digesters = self._get_digesters()
    destination_url = self._destination_resource.storage_url
    provider = destination_url.scheme
    api = api_factory.get_api(provider)
    request_config = request_config_factory.get_request_config(
        destination_url,
        content_type=upload_util.get_content_type(self._source_resource),
        md5_hash=self._source_resource.md5_hash,
        size=self._length,
        user_request_args=self._user_request_args)

    with self._get_upload_stream(digesters, task_status_queue) as source_stream:
      upload_strategy = upload_util.get_upload_strategy(api, self._length)
      if upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
        tracker_file_path = tracker_file_util.get_tracker_file_path(
            self._destination_resource.storage_url,
            tracker_file_util.TrackerFileType.UPLOAD,
            component_number=self._component_number)

        # TODO(b/160998052): Validate and use keys from tracker files.
        encryption_key_sha256 = None

        complete = False
        tracker_callback = functools.partial(
            tracker_file_util.write_resumable_upload_tracker_file,
            tracker_file_path, complete, encryption_key_sha256)

        tracker_data = tracker_file_util.read_resumable_upload_tracker_file(
            tracker_file_path)
        if tracker_data is None:
          serialization_data = None
        else:
          # TODO(b/190093425): Print a better message for component uploads once
          # the final destination resource is available in ComponentUploadTask.
          log.status.Print('Resuming upload for ' + destination_url.object_name)

          serialization_data = tracker_data.serialization_data

        if tracker_data and tracker_data.complete:
          try:
            destination_resource = api.get_object_metadata(
                destination_url.bucket_name, destination_url.object_name)
          except api_errors.CloudApiError:
            # Any problem fetching existing object metadata can be ignored,
            # since we'll just reupload the object.
            pass
          else:
            if self._existing_destination_is_valid(destination_resource):
              return self._get_output(destination_resource)

        attempt_upload = functools.partial(
            api.upload_object,
            source_stream,
            self._destination_resource,
            request_config,
            serialization_data=serialization_data,
            tracker_callback=tracker_callback,
            upload_strategy=upload_strategy)

        def _handle_resumable_upload_error(exc_type, exc_value, exc_traceback,
                                           state):
          """Returns true if resumable upload should retry on error argument."""
          del exc_traceback  # Unused.
          if not (exc_type is api_errors.NotFoundError or
                  getattr(exc_value, 'status_code', None) == 410):

            if exc_type is api_errors.ResumableUploadAbortError:
              tracker_file_util.delete_tracker_file(tracker_file_path)

            # Otherwise the error is probably a persistent network issue
            # that is already retried by API clients, so we'll keep the tracker
            # file to allow the user to retry the upload in a separate run.

            return False

          tracker_file_util.delete_tracker_file(tracker_file_path)

          if state.retrial == 0:
            # Ping bucket to see if it exists.
            try:
              api.get_bucket(self._destination_resource.storage_url.bucket_name)
            except api_errors.CloudApiError as e:
              # The user may not have permission to view the bucket metadata,
              # so the ping may still be valid for access denied errors.
              status = getattr(e, 'status_code', None)
              if status not in (401, 403):
                raise

          return True

        # Convert seconds to miliseconds by multiplying by 1000.
        destination_resource = retry.Retryer(
            max_retrials=properties.VALUES.storage.max_retries.GetInt(),
            max_wait_ms=properties.VALUES.storage.max_retry_delay.GetInt() *
            1000,
            exponential_sleep_multiplier=(
                properties.VALUES.storage.exponential_sleep_multiplier.GetInt()
            )).RetryOnException(
                attempt_upload,
                sleep_ms=properties.VALUES.storage.base_retry_delay.GetInt() *
                1000,
                should_retry_if=_handle_resumable_upload_error)

        tracker_data = tracker_file_util.read_resumable_upload_tracker_file(
            tracker_file_path)
        if tracker_data is not None:
          if self._component_number is not None:
            tracker_file_util.write_resumable_upload_tracker_file(
                tracker_file_path,
                complete=True,
                encryption_key_sha256=tracker_data.encryption_key_sha256,
                serialization_data=tracker_data.serialization_data)
          else:
            tracker_file_util.delete_tracker_file(tracker_file_path)
      else:
        destination_resource = api.upload_object(
            source_stream,
            self._destination_resource,
            request_config,
            upload_strategy=upload_strategy)

      upload_util.validate_uploaded_object(digesters, destination_resource,
                                           task_status_queue)

    return self._get_output(destination_resource)
