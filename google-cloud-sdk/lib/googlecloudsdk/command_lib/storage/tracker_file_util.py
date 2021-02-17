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
"""Utilities for tracker files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import hashlib
import json
import os
import re

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

# The maximum length of a file name can vary wildly between operating
# systems, so always ensure that tracker files are less than 100 characters.
_MAX_TRACKER_FILE_NAME_LENGTH = 100
_TRAILING_FILE_NAME_CHARACTERS_FOR_DISPLAY = 16
_RE_DELIMITER_PATTERN = r'[/\\]'


class TrackerFileType(enum.Enum):
  UPLOAD = 'upload'
  DOWNLOAD = 'download'
  DOWNLOAD_COMPONENT = 'download_component'
  PARALLEL_UPLOAD = 'parallel_upload'
  SLICED_DOWNLOAD = 'sliced_download'
  REWRITE = 'rewrite'


def _get_unwritable_tracker_file_error(error, tracker_file_path):
  """Edits error to use custom unwritable message.

  Args:
    error (Exception): Python error to modify message of.
    tracker_file_path (str): Tracker file path there were issues writing to.

  Returns:
    Exception argument with altered error message.
  """
  original_error_text = getattr(error, 'strerror')
  if not original_error_text:
    original_error_text = '[No strerror]'
  return type(error)(
      ('Could not write tracker file ({}): {}. This can happen if gcloud '
       'storage is configured to save tracker files to an unwritable directory.'
      ).format(tracker_file_path, original_error_text))


def _create_tracker_directory_if_needed():
  """Looks up or creates the gcloud storage tracker file directory.

  Resumable transfer tracker files will be kept here.

  Returns:
    The path string to the tracker directory.
  """
  tracker_directory = properties.VALUES.storage.tracker_files_directory.Get()
  # Thread-safe method to prevent parallel processing errors.
  files.MakeDir(tracker_directory)
  return tracker_directory


def _get_hashed_file_name(file_name):
  """Applies a hash function (SHA1) to shorten the passed file name.

  The spec for the hashed file name is as follows:
      TRACKER_<hash>_<trailing>
  'hash' is a SHA1 hash on the original file name, and 'trailing' is
  the last chars of the original file name. Max file name lengths
  vary by operating system, so the goal of this function is to ensure
  the hashed version takes fewer than _MAX_TRACKER_FILE_NAME_LENGTH characters.

  Args:
    file_name (str): File name to be hashed. May be unicode or bytes.

  Returns:
    String of shorter, hashed file_name.
  """
  name_hash_object = hashlib.sha1(file_name.encode('utf-8'))
  return 'TRACKER_{}.{}'.format(
      name_hash_object.hexdigest(),
      file_name[-1 * _TRAILING_FILE_NAME_CHARACTERS_FOR_DISPLAY:])


def _get_hashed_path(tracker_file_name, tracker_file_type,
                     resumable_tracker_directory):
  """Hashes and returns a tracker file path.

  Args:
    tracker_file_name (str): The tracker file name prior to it being hashed.
    tracker_file_type (TrackerFileType): The TrackerFileType of
      res_tracker_file_name.
    resumable_tracker_directory (str): Path to directory of tracker files.

  Returns:
    Final (hashed) tracker file path.

  Raises:
    Error: Hashed file path is too long.
  """
  hashed_tracker_file_name = _get_hashed_file_name(tracker_file_name)
  tracker_file_name_with_type = '{}_{}'.format(tracker_file_type.value.lower(),
                                               hashed_tracker_file_name)
  if len(tracker_file_name_with_type) > _MAX_TRACKER_FILE_NAME_LENGTH:
    raise errors.Error(
        'Tracker file name hash is over max character limit of {}: {}'.format(
            _MAX_TRACKER_FILE_NAME_LENGTH, tracker_file_name_with_type))

  tracker_file_path = (
      resumable_tracker_directory + os.sep + tracker_file_name_with_type)
  return tracker_file_path


def get_tracker_file_path(destination_url,
                          tracker_file_type,
                          source_url=None,
                          component_number=None):
  """Retrieves path string to tracker file.

  Args:
    destination_url (storage_url.StorageUrl): Describes the destination file.
    tracker_file_type (TrackerFileType): Type of tracker file to retrieve.
    source_url (storage_url.StorageUrl): Describes the source file.
    component_number (int): The number of the component is being tracked for a
      sliced download.

  Returns:
    String file path to tracker file.
  """
  if tracker_file_type == TrackerFileType.UPLOAD:
    # Encode the destination bucket and object name into the tracker file name.
    raw_result_tracker_file_name = 'resumable_upload__{}__{}__{}.url'.format(
        destination_url.bucket_name, destination_url.object_name,
        destination_url.scheme.value)
  elif tracker_file_type == TrackerFileType.DOWNLOAD:
    # Encode the fully-qualified destination file into the tracker file name.
    raw_result_tracker_file_name = 'resumable_download__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value)
  elif tracker_file_type == TrackerFileType.DOWNLOAD_COMPONENT:
    # Encode the fully-qualified destination file name and the component number
    # into the tracker file name.
    raw_result_tracker_file_name = 'resumable_download__{}__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value, component_number)
  elif tracker_file_type == TrackerFileType.PARALLEL_UPLOAD:
    # Encode the destination bucket and object names as well as the source file
    # into the tracker file name.
    raw_result_tracker_file_name = 'parallel_upload__{}__{}__{}__{}.url'.format(
        destination_url.bucket_name, destination_url.object_name, source_url,
        destination_url.scheme.value)
  elif tracker_file_type == TrackerFileType.SLICED_DOWNLOAD:
    # Encode the fully-qualified destination file into the tracker file name.
    raw_result_tracker_file_name = 'sliced_download__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value)
  elif tracker_file_type == TrackerFileType.REWRITE:
    raw_result_tracker_file_name = 'rewrite__{}__{}__{}__{}__{}.token'.format(
        source_url.bucket_name, source_url.object_name,
        destination_url.bucket_name, destination_url.object_name,
        destination_url.scheme.value)

  result_tracker_file_name = re.sub(_RE_DELIMITER_PATTERN, '_',
                                    raw_result_tracker_file_name)
  resumable_tracker_directory = _create_tracker_directory_if_needed()
  return _get_hashed_path(result_tracker_file_name, tracker_file_type,
                          resumable_tracker_directory)


def get_sliced_download_tracker_file_paths(destination_url):
  """Gets a list of tracker file paths for each slice of a sliced download.

  The returned list consists of the parent tracker file path in index 0
  followed by component tracker files.

  Args:
    destination_url: Destination URL for tracker file.

  Returns:
    List of string file paths to tracker files.
  """
  parallel_tracker_file_path = get_tracker_file_path(
      destination_url, TrackerFileType.SLICED_DOWNLOAD)
  tracker_file_paths = [parallel_tracker_file_path]
  number_components = 0

  tracker_file = None
  try:
    tracker_file = files.FileReader(parallel_tracker_file_path)
    number_components = json.load(tracker_file)['number_components']
  except files.MissingFileError:
    return tracker_file_paths
  finally:
    if tracker_file:
      tracker_file.close()

  for i in range(number_components):
    tracker_file_paths.append(
        get_tracker_file_path(
            destination_url,
            TrackerFileType.DOWNLOAD_COMPONENT,
            component_number=i))

  return tracker_file_paths


def delete_tracker_file(tracker_file_path):
  """Deletes tracker file if it exists."""
  if tracker_file_path and os.path.exists(tracker_file_path):
    os.remove(tracker_file_path)


def delete_download_tracker_files(destination_url):
  """Deletes all tracker files for an object download.

  Args:
    destination_url (storage_url.StorageUrl): Describes the destination file.
  """
  # Delete non-sliced download tracker file.
  delete_tracker_file(
      get_tracker_file_path(destination_url, TrackerFileType.DOWNLOAD))

  # Delete all sliced download tracker files.
  tracker_files = get_sliced_download_tracker_file_paths(destination_url)
  for tracker_file in tracker_files:
    delete_tracker_file(tracker_file)


def hash_gcs_rewrite_parameters_for_tracker_file(
    source_object_resource,
    destination_object_resource,
    destination_metadata=None,
    request_config=None,
    source_decyrption_key_sha256=None,
    destination_encryption_key_sha256=None):
  """Creates an MD5 hex digest of the parameters for GCS rewrite call.

  Resuming rewrites requires that the input parameters are identical, so the
  tracker file needs to represent the input parameters. This is done by hashing
  the API call parameters. For example, if a user performs a rewrite with a
  changed ACL, the hashes will not match, and we will restart the rewrite.

  Args:
    source_object_resource (ObjectResource): Must include
      bucket, name, etag, and metadata.
    destination_object_resource (ObjectResource|UnknownResource): Must include
      bucket, name, and metadata.
    destination_metadata (messages.Object|None): Separated from
      destination_object_resource since UnknownResource does not have metadata.
    request_config (gcs_api.GcsRequestConfig|None): Contains a variety of API
      arguments.
    source_decyrption_key_sha256 (str|None): Optional SHA256 hash string of
      decryption key for source object.
    destination_encryption_key_sha256 (str|None): Optional SHA256 hash string of
      encryption key for destination object.

  Returns:
    MD5 hex digest (string) of the input parameters.

  Raises:
    ValueError if argument is missing required property.
  """
  mandatory_parameters = (source_object_resource.storage_url.bucket_name,
                          source_object_resource.storage_url.object_name,
                          destination_object_resource.storage_url.bucket_name,
                          destination_object_resource.storage_url.object_name)
  if not all(mandatory_parameters):
    raise ValueError('Missing required parameter values.')

  optional_parameters = (
      destination_metadata,
      getattr(request_config, 'max_bytes_per_call', None),
      getattr(request_config, 'precondition_generation_match', None),
      getattr(request_config, 'precondition_metageneration_match', None),
      getattr(request_config, 'predefined_acl_string', None),
      source_decyrption_key_sha256,
      destination_encryption_key_sha256,
  )
  all_parameters = mandatory_parameters + optional_parameters
  parameters_bytes = ''.join([str(parameter) for parameter in all_parameters
                             ]).encode('UTF8')
  parameters_hash = util.get_md5_hash(parameters_bytes)
  return parameters_hash.hexdigest()


def _write_tracker_file(tracker_file_path, data):
  """Creates a tracker file, storing the input data."""
  try:
    file_descriptor = os.open(tracker_file_path,
                              os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(file_descriptor, 'w') as write_stream:
      write_stream.write(data)
  except OSError as e:
    raise _get_unwritable_tracker_file_error(e, tracker_file_path)


def write_json_to_tracker_file(tracker_file_path, data):
  """Creates a tracker file and writes JSON to it.

  Args:
    tracker_file_path (str): The path to the tracker file.
    data (object): JSON-serializable data to write to file.
  """
  json_string = json.dumps(data)
  _write_tracker_file(tracker_file_path, json_string)


def write_download_component_tracker_file(tracker_file_path,
                                          source_object_resource,
                                          download_start_byte):
  """Updates or creates a download component tracker file on disk.

  Args:
    tracker_file_path (str): The path to the tracker file.
    source_object_resource (resource_reference.ObjectResource): Needed for
      object etag and optionally generation.
    download_start_byte (int): Where to resume downloading from.
  """
  component_data = {
      'etag': source_object_resource.etag,
      'generation': source_object_resource.generation,
      'download_start_byte': download_start_byte,
  }

  write_json_to_tracker_file(tracker_file_path, component_data)


def write_rewrite_tracker_file(tracker_file_name, rewrite_parameters_hash,
                               rewrite_token):
  """Writes rewrite operation information to a tracker file.

  Args:
    tracker_file_name (str): The path to the tracker file.
    rewrite_parameters_hash (str): MD5 hex digest of rewrite call parameters.
    rewrite_token (str): Returned by API, so rewrites can resume where they left
      off.
  """
  _write_tracker_file(tracker_file_name,
                      '{}\n{}'.format(rewrite_parameters_hash, rewrite_token))


def read_or_create_download_tracker_file(source_object_resource,
                                         destination_url,
                                         slice_start_byte=0,
                                         existing_file_size=0,
                                         component_number=None,
                                         create=True):
  """Checks for a download tracker file and creates one if it does not exist.

  For normal downloads, if the tracker file exists, the existing_file_size
  in bytes is presumed to downloaded from the server. Therefore,
  existing_file_size becomes the download start point.

  For sliced downloads, the number of bytes previously retrieved from the server
  cannot be determined from existing_file_size. Therefore, it is retrieved
  from the tracker file.

  Args:
    source_object_resource (resource_reference.ObjectResource): Needed for
      object etag and generation.
    destination_url (storage_url.StorageUrl): Destination URL for tracker file.
    slice_start_byte (int): Start byte to use if we cannot find a
      matching tracker file for a download slice.
    existing_file_size (int): Amount of file on disk that already exists.
    component_number (int?): The download component number to find the start
      point for.
    create (bool): Creates tracker file if one could not be found.

  Returns:
    tracker_file_path (str?): The path to the tracker file, if one was used.
    download_start_byte (int): The first byte that still needs to be downloaded.

  Raises:
    ValueCannotBeDeterminedError: Source object resource does not have
      necessary metadata to decide on download start byte.
  """
  if not source_object_resource.etag:
    raise errors.ValueCannotBeDeterminedError(
        'Source object resource is missing etag.')

  tracker_file_path = None
  if (not source_object_resource.size or
      (source_object_resource.size <
       properties.VALUES.storage.resumable_threshold.GetInt())):
    # There is no tracker file for small downloads, so start from scratch.
    return tracker_file_path, slice_start_byte

  if component_number is None:
    tracker_file_type = TrackerFileType.DOWNLOAD
    download_name_for_logger = destination_url.object_name
  else:
    tracker_file_type = TrackerFileType.DOWNLOAD_COMPONENT
    download_name_for_logger = '{} component {}'.format(
        destination_url.object_name, component_number)

  tracker_file_path = get_tracker_file_path(
      destination_url, tracker_file_type, component_number=component_number)
  tracker_file = None
  # Check to see if we already have a matching tracker file.
  try:
    tracker_file = files.FileReader(tracker_file_path)
    if tracker_file_type is TrackerFileType.DOWNLOAD:
      etag_value = tracker_file.readline().rstrip('\n')
      if etag_value == source_object_resource.etag:
        log.debug('Found tracker file starting at byte {} for {}.'.format(
            existing_file_size, download_name_for_logger))
        return tracker_file_path, existing_file_size
    elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
      component_data = json.loads(tracker_file.read())
      if (component_data['etag'] == source_object_resource.etag and
          component_data['generation'] == source_object_resource.generation):
        start_byte = int(component_data['download_start_byte'])
        log.debug('Found tracker file starting at byte {} for {}.'.format(
            start_byte, download_name_for_logger))
        return tracker_file_path, start_byte

  except files.MissingFileError:
    # Cannot read from file.
    pass

  finally:
    if tracker_file:
      tracker_file.close()

  if create:
    log.debug(
        'No matching tracker file for {}.'.format(download_name_for_logger))
    if tracker_file_type is TrackerFileType.DOWNLOAD:
      _write_tracker_file(tracker_file_path, source_object_resource.etag + '\n')
    elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
      write_download_component_tracker_file(tracker_file_path,
                                            source_object_resource,
                                            slice_start_byte)

  # No matching tracker file, so starting point is slice_start_byte.
  return tracker_file_path, slice_start_byte


def read_rewrite_tracker_file(tracker_file_path, rewrite_parameters_hash):
  """Attempts to read a rewrite tracker file.

  Args:
    tracker_file_path (str): The path to the tracker file.
    rewrite_parameters_hash (str): MD5 hex digest of rewrite call parameters
      constructed by hash_gcs_rewrite_parameters_for_tracker_file.

  Returns:
    String token for resuming rewrites if a matching tracker file exists.
  """
  with files.FileReader(tracker_file_path) as tracker_file:
    existing_hash, rewrite_token = [
        line.rstrip('\n') for line in tracker_file.readlines()
    ]
    if existing_hash == rewrite_parameters_hash:
      return rewrite_token


def get_download_start_byte(source_object_resource, destination_url,
                            slice_start_byte, existing_file_size,
                            component_number):
  """Returns the download starting point for a component.

  Args:
    source_object_resource (resource_reference.ObjectResource): Needed for
      object etag and generation.
    destination_url (storage_url.StorageUrl): Destination URL for tracker file.
    slice_start_byte (int): The start byte of the byte range for this download.
    existing_file_size (int): Amount of file on disk that already exists.
    component_number (int): The download component number to find the start
      point for.

  Returns:
    download_start_byte (int): The first byte that still needs to be downloaded.
  """
  _, download_start_byte = read_or_create_download_tracker_file(
      source_object_resource,
      destination_url,
      slice_start_byte,
      existing_file_size,
      component_number,
      create=False)
  return download_start_byte
