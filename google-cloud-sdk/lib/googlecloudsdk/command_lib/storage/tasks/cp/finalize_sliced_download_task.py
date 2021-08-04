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
"""Task for performing final steps of sliced download.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class FinalizeSlicedDownloadTask(task.Task):
  """Performs final steps of sliced download."""

  def __init__(self, source_resource, temporary_destination_resource,
               final_destination_resource):
    """Initializes task.

    Args:
      source_resource (resource_reference.ObjectResource): Should contain
        object's metadata for checking content encoding.
      temporary_destination_resource (resource_reference.FileObjectResource):
        Must contain a local path to the temporary file written to during
        transfers.
      final_destination_resource (resource_reference.FileObjectResource): Must
        contain local filesystem path to the final download destination.
    """
    super(FinalizeSlicedDownloadTask, self).__init__()
    self._source_resource = source_resource
    self._temporary_destination_resource = temporary_destination_resource
    self._final_destination_resource = final_destination_resource

  def execute(self, task_status_queue=None):
    """Validates and clean ups after sliced download."""
    for message in self.received_messages:
      if message.topic is task.Topic.ERROR:
        log.error(message.payload)
        return

    temporary_object_path = (
        self._temporary_destination_resource.storage_url.object_name)
    final_destination_object_path = (
        self._final_destination_resource.storage_url.object_name)
    if (properties.VALUES.storage.check_hashes.Get() !=
        properties.CheckHashes.NEVER.value and
        self._source_resource.crc32c_hash):

      component_payloads = [
          message.payload
          for message in self.received_messages
          if message.topic == task.Topic.CRC32C
      ]
      if component_payloads:
        # Returns list of payload values sorted by component number.
        sorted_component_payloads = sorted(
            component_payloads, key=lambda d: d['component_number'])

        downloaded_file_checksum = sorted_component_payloads[0][
            'crc32c_checksum']
        for i in range(1, len(sorted_component_payloads)):
          payload = sorted_component_payloads[i]
          downloaded_file_checksum = crc32c.concat_checksums(
              downloaded_file_checksum,
              payload['crc32c_checksum'],
              b_byte_count=payload['length'])

        downloaded_file_hash_object = crc32c.get_crc32c_from_checksum(
            downloaded_file_checksum)
        downloaded_file_hash_digest = crc32c.get_hash(
            downloaded_file_hash_object)

        download_util.validate_download_hash_and_delete_corrupt_files(
            temporary_object_path, self._source_resource.crc32c_hash,
            downloaded_file_hash_digest)

    if download_util.decompress_gzip_if_necessary(
        self._source_resource, temporary_object_path,
        final_destination_object_path):
      os.remove(temporary_object_path)

    if os.path.exists(temporary_object_path):
      os.rename(temporary_object_path, final_destination_object_path)

    tracker_file_util.delete_download_tracker_files(
        self._temporary_destination_resource.storage_url)
