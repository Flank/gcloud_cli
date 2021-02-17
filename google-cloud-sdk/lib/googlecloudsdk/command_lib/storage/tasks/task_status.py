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
"""Tools for monitoring and reporting task statuses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import multiprocessing
import threading
import time

from googlecloudsdk.command_lib.storage import thread_messages
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import scaled_integer


class OperationName(enum.Enum):
  DOWNLOADING = 'Downloading'
  UPLOADING = 'Uploading'
  HASHING = 'Hashing'


class ProgressType(enum.Enum):
  FILES_AND_BYTES = 'FILES AND BYTES'
  FILES = 'FILES'


class FilesAndBytesProgressCallback:
  """Tracks file count and bytes progress info for large file operations.

  Information is sent to the status_queue, which will print aggregate it
  for printing to the user. Useful for heavy operations like copy or hash.
  Arguments are the same as thread_messages.ProgressMessage.
  """

  def __init__(self,
               status_queue,
               size,
               source_url,
               destination_url=None,
               component_number=None,
               operation_name=None,
               process_id=None,
               thread_id=None):
    """Initializes callback, saving non-changing variables.

    Args:
      status_queue (multiprocessing.Queue): Where to submit progress messages.
        If we spawn new worker processes, they will lose their reference to the
        correct version of this queue if we don't package it here.
      size (int): Total size of file/component in bytes.
      source_url (StorageUrl): Represents source of data used by operation.
      destination_url (StorageUrl|None): Represents destination of data used by
        operation. None for unary operations like hashing.
      component_number (int|None): If a multipart operation, indicates the
        component number.
      operation_name (OperationName|None): Name of the operation running on
        target data.
      process_id (int|None): Identifies process that produced the instance of
        this message (overridable for testing).
      thread_id (int|None): Identifies thread that produced the instance of this
        message (overridable for testing).
    """
    self._status_queue = status_queue
    self._size = size
    self._source_url = source_url
    self._destination_url = destination_url
    self._component_number = component_number
    self._operation_name = operation_name
    self._process_id = process_id
    self._thread_id = thread_id

  def __call__(self, processed_bytes):
    """See __init__ docstring for processed_bytes arg."""
    # Time progress callback is triggered in seconds since epoch (float).
    current_time = time.time()
    self._status_queue.put(
        thread_messages.ProgressMessage(
            size=self._size,
            processed_bytes=processed_bytes,
            time=current_time,
            source_url=self._source_url,
            destination_url=self._destination_url,
            component_number=self._component_number,
            operation_name=self._operation_name,
            process_id=self._process_id,
            thread_id=self._thread_id))


class _StatusTracker:
  """Aggregates and prints information on task statuses.

  We use "start" and "stop" instead of "__enter__" and "__exit__" because
  this class should only be used by ProgressManager as a non-context-manager.
  """

  def __init__(self):
    self._completed_files = 0
    self._processed_bytes = 0
    self._tracked_file_progress = {}
    self._progress_tracker = None

  def _get_status_string(self):
    # TODO(b/180047352) Avoid having other output print on the same line.
    return '\rCopied files {} | {}'.format(
        self._completed_files,
        scaled_integer.FormatBinaryNumber(
            self._processed_bytes, decimal_places=1))

  def add_message(self, status_message):
    """Processes task status message for printing and aggregation.

    Args:
      status_message (thread_messages.ProgressMessage): Message to process.
    """
    known_progress = self._tracked_file_progress.get(
        status_message.source_url.url_string, 0)
    # status_message.processed_bytes includes bytes from past messages.
    self._processed_bytes += status_message.processed_bytes - known_progress
    if status_message.finished:
      self._completed_files += 1
      del self._tracked_file_progress[status_message.source_url.url_string]
    else:
      self._tracked_file_progress[status_message.source_url.url_string] = (
          status_message.processed_bytes)

  def start(self):
    self._progress_tracker = progress_tracker.ProgressTracker(
        message='Starting operation',
        detail_message_callback=self._get_status_string)
    self._progress_tracker.__enter__()
    return self

  def stop(self, exc_type, exc_val, exc_tb):
    if self._progress_tracker:
      return self._progress_tracker.__exit__(exc_type, exc_val, exc_tb)


def status_message_handler(task_status_queue,
                           status_printing_manager):
  """Thread method for submiting items from queue to manager for processing."""
  while True:
    status_message = task_status_queue.get()
    if status_message == '_SHUTDOWN':
      break
    status_printing_manager.add_message(status_message)


class ProgressManager:
  """Context manager for processing and displaying progress completing command.

  Attributes:
    task_status_queue (multiprocessing.Queue): Tasks can submit their progress
      messages here.
  """

  def __init__(self, progress_type):
    """Initializes context manager.

    Args:
      progress_type (ProgressType): Determines what type of progress indicator
        to display.
    """
    super(ProgressManager, self).__init__()

    self._progress_type = progress_type
    self._status_message_handler_thread = None
    self._status_tracker = None
    self.task_status_queue = multiprocessing.Queue()

  def __enter__(self):
    if self._progress_type is ProgressType.FILES_AND_BYTES:
      self._status_tracker = _StatusTracker()
      self._status_message_handler_thread = threading.Thread(
          target=status_message_handler,
          args=(self.task_status_queue, self._status_tracker))

      self._status_tracker.start()
      self._status_message_handler_thread.start()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if self._progress_type is ProgressType.FILES_AND_BYTES:
      self.task_status_queue.put('_SHUTDOWN')
      self._status_message_handler_thread.join()
      self._status_tracker.stop(exc_type, exc_val, exc_tb)
