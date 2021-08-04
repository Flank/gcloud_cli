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

"""Task for file downloads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os
import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks.cp import copy_component_util
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import finalize_sliced_download_task
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import scaled_integer


TEMPORARY_FILE_SUFFIX = '_.gstmp'


def _get_hash_check_warning_base():
  # Create the text in a function so that we can test it easily.
  google_crc32c_install_steps = hash_util.get_google_crc32c_install_command()
  return textwrap.dedent(
      """\
      This download {{}} since the google-crc32c
      binary is not installed, and Python hash computation will likely
      throttle performance. You can change this by installing the binary
      {crc32c_steps}or
      modifying the "storage/check_hashes" config setting.""".format(
          crc32c_steps='by running "{}" '.format(google_crc32c_install_steps)
          if google_crc32c_install_steps else ''))


_HASH_CHECK_WARNING_BASE = _get_hash_check_warning_base()
_NO_HASH_CHECK_WARNING = _HASH_CHECK_WARNING_BASE.format(
    'will not be validated')
_SLOW_HASH_CHECK_WARNING = _HASH_CHECK_WARNING_BASE.format('may be slow')
_NO_HASH_CHECK_ERROR = _HASH_CHECK_WARNING_BASE.format('was skipped')


def _log_or_raise_crc32c_issues(resource):
  """Informs user about non-standard hashing behavior.

  Args:
    resource (resource_reference.ObjectResource): For checking if object has
      known hash to validate against.

  Raises:
    errors.Error: gcloud storage set to fail if performance-optimized digesters
      could not be created.
  """
  if crc32c.IS_FAST_GOOGLE_CRC32C_AVAILABLE or not resource.crc32c_hash:
    # If crc32c is available, hashing behavior will be standard.
    # If resource.crc32c not available, no hash will be verified.
    return

  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes == properties.CheckHashes.ALWAYS.value:
    log.warning(_SLOW_HASH_CHECK_WARNING)
  elif check_hashes == properties.CheckHashes.IF_FAST_ELSE_SKIP.value:
    log.warning(_NO_HASH_CHECK_WARNING)
  elif check_hashes == properties.CheckHashes.IF_FAST_ELSE_FAIL.value:
    raise errors.Error(_NO_HASH_CHECK_ERROR)


def _should_perform_sliced_download(resource):
  """Returns True if conditions are right for a sliced download."""
  if (not resource.crc32c_hash and properties.VALUES.storage.check_hashes.Get()
      != properties.CheckHashes.NEVER.value):
    # Do not perform sliced download if hash validation is not possible.
    return False

  threshold = scaled_integer.ParseInteger(
      properties.VALUES.storage.sliced_object_download_threshold.Get())
  component_size = scaled_integer.ParseInteger(
      properties.VALUES.storage.sliced_object_download_component_size.Get())
  # TODO(b/183017513): Only perform sliced downloads with parallelism.
  api_capabilities = api_factory.get_capabilities(resource.storage_url.scheme)
  return (resource.size and threshold != 0 and resource.size > threshold and
          component_size and
          cloud_api.Capability.SLICED_DOWNLOAD in api_capabilities and
          task_executor.should_use_parallelism())


class FileDownloadTask(task.Task):
  """Represents a command operation triggering a file download."""

  def __init__(self, source_resource, destination_resource):
    """Initializes task.

    Args:
      source_resource (ObjectResource): Must contain
        the full path of object to download, including bucket. Directories
        will not be accepted. Does not need to contain metadata.
      destination_resource (FileObjectResource|UnknownResource): Must contain
        local filesystem path to upload object. Does not need to contain
        metadata.
    """
    super(FileDownloadTask, self).__init__()
    self._source_resource = source_resource
    self._destination_resource = destination_resource
    self._temporary_destination_resource = (
        self._get_temporary_destination_resource())

    if (self._source_resource.size and
        self._source_resource.size >= scaled_integer.ParseInteger(
            properties.VALUES.storage.resumable_threshold.Get())):
      self._strategy = cloud_api.DownloadStrategy.RESUMABLE
    else:
      self._strategy = cloud_api.DownloadStrategy.ONE_SHOT

    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string)

  def _get_temporary_destination_resource(self):
    temporary_resource = copy.deepcopy(self._destination_resource)
    temporary_resource.storage_url.object_name += TEMPORARY_FILE_SUFFIX
    return temporary_resource

  def _get_sliced_download_tasks(self):
    """Creates all tasks necessary for a sliced download."""
    _log_or_raise_crc32c_issues(self._source_resource)

    component_offsets_and_lengths = copy_component_util.get_component_offsets_and_lengths(
        self._source_resource.size,
        properties.VALUES.storage.sliced_object_download_component_size.Get(),
        properties.VALUES.storage.sliced_object_download_max_components.GetInt(
        ))

    download_component_task_list = []
    for i, (offset, length) in enumerate(component_offsets_and_lengths):
      download_component_task_list.append(
          file_part_download_task.FilePartDownloadTask(
              self._source_resource,
              self._temporary_destination_resource,
              offset=offset,
              length=length,
              component_number=i,
              total_components=len(component_offsets_and_lengths),
              strategy=self._strategy))

    finalize_sliced_download_task_list = [
        finalize_sliced_download_task.FinalizeSlicedDownloadTask(
            self._source_resource, self._temporary_destination_resource,
            self._destination_resource)
    ]

    return (download_component_task_list, finalize_sliced_download_task_list)

  def _restart_download(self):
    log.status.Print('Temporary download file corrupt.'
                     ' Restarting download {}'.format(self._source_resource))
    temporary_download_url = self._temporary_destination_resource.storage_url
    os.remove(temporary_download_url.object_name)
    tracker_file_util.delete_download_tracker_files(temporary_download_url)

  def execute(self, task_status_queue=None):
    """Creates appropriate download tasks."""

    # We need to call os.remove here for two reasons:
    # 1. It saves on disk space during a transfer.
    # 2. Os.rename fails if a file exists at the destination. Avoiding this by
    # removing files after a download makes us susceptible to a race condition
    # between two running instances of gcloud storage. See the following PR for
    # more information: https://github.com/GoogleCloudPlatform/gsutil/pull/1202.
    if self._destination_resource.storage_url.exists():
      os.remove(self._destination_resource.storage_url.object_name)
    temporary_download_file_exists = (
        self._temporary_destination_resource.storage_url.exists())
    if temporary_download_file_exists and os.path.getsize(
        self._temporary_destination_resource.storage_url.object_name
    ) > self._source_resource.size:
      self._restart_download()

    if _should_perform_sliced_download(self._source_resource):
      download_component_task_list, finalize_sliced_download_task_list = (
          self._get_sliced_download_tasks())

      _, found_tracker_file = (
          tracker_file_util.read_or_create_download_tracker_file(
              self._source_resource,
              self._temporary_destination_resource.storage_url,
              total_components=len(download_component_task_list),
          ))
      if found_tracker_file:
        log.debug('Resuming sliced download with {} components.'.format(
            len(download_component_task_list)))
      else:
        if temporary_download_file_exists:
          # Component count may have changed, invalidating earlier download.
          self._restart_download()
        log.debug('Launching sliced download with {} components.'.format(
            len(download_component_task_list)))

      copy_component_util.create_file_if_needed(
          self._source_resource, self._temporary_destination_resource)

      return task.Output(
          additional_task_iterators=[
              download_component_task_list,
              finalize_sliced_download_task_list,
          ],
          messages=None)

    file_part_download_task.FilePartDownloadTask(
        self._source_resource,
        self._temporary_destination_resource,
        offset=0,
        length=self._source_resource.size,
        strategy=self._strategy).execute(task_status_queue=task_status_queue)

    temporary_url = self._temporary_destination_resource.storage_url
    if os.path.exists(temporary_url.object_name):
      os.rename(temporary_url.object_name,
                self._destination_resource.storage_url.object_name)

    # For sliced download, cleanup is done in the finalized sliced download task
    # We perform cleanup here for all other types in case some corrupt files
    # were left behind.
    tracker_file_util.delete_download_tracker_files(temporary_url)
