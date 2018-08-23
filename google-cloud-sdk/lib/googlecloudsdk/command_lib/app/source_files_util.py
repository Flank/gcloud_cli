# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Utility methods for iterating over source files for deployment.

Based on the runtime and environment, this can entail generating a new
.gcloudignore, using an existing .gcloudignore, or using existing skip_files.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import runtime_registry
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import exceptions as core_exceptions


_NODE_GCLOUDIGNORE = '\n'.join([
    gcloudignore.DEFAULT_IGNORE_FILE,
    '# Node.js dependencies:',
    'node_modules/'
])


_PHP_GCLOUDIGNORE = '\n'.join([
    gcloudignore.DEFAULT_IGNORE_FILE,
    '# PHP Composer dependencies:',
    'vendor/'
])

_PYTHON_GCLOUDIGNORE = '\n'.join([
    gcloudignore.DEFAULT_IGNORE_FILE,
    '# Python pycache:',
    '__pycache__/'
])


_GCLOUDIGNORE_REGISTRY = {
    runtime_registry.RegistryEntry(
        env.NODE_TI_RUNTIME_EXPR, {env.STANDARD}): _NODE_GCLOUDIGNORE,
    runtime_registry.RegistryEntry(
        env.PHP_TI_RUNTIME_EXPR, {env.STANDARD}): _PHP_GCLOUDIGNORE,
    runtime_registry.RegistryEntry(
        env.PYTHON_TI_RUNTIME_EXPR, {env.STANDARD}): _PYTHON_GCLOUDIGNORE,
}


class SkipFilesError(core_exceptions.Error):

  def __init__(self, error_message):
    super(SkipFilesError, self).__init__(error_message)


def _GetGcloudignoreRegistry():
  return runtime_registry.Registry(_GCLOUDIGNORE_REGISTRY, default=False)


def GetSourceFileIterator(source_dir, skip_files_regex, has_explicit_skip_files,
                          runtime, environment):
  """Returns an iterator for accessing all source files to be uploaded.

  This method uses several implementations based on the provided runtime and
  env. The rules are as follows, in decreasing priority:
  1) For some runtimes/envs (i.e. those defined in _GCLOUDIGNORE_REGISTRY), we
     completely ignore skip_files and generate a runtime-specific .gcloudignore
     if one is not present, or use the existing .gcloudignore.
  2) For all other runtimes/envs, we:
    2a) Check for an existing .gcloudignore and use that if one exists. We also
        raise an error if the user has both a .gcloudignore file and explicit
        skip_files defined.
    2b) If there is no .gcloudignore, we use the provided skip_files.

  Args:
    source_dir: str, path to source directory
    skip_files_regex: str, skip_files to use if necessary - see above rules for
      when this could happen. This can be either the user's explicit skip_files
      as defined in their app.yaml or the default skip_files we implicitly
      provide if they didn't define any.
    has_explicit_skip_files: bool, indicating whether skip_files_regex was
      explicitly defined by the user
    runtime: str, runtime as defined in app.yaml
    environment: env.Environment enum

  Raises:
    SkipFilesError: if you are using a runtime that no longer supports
      skip_files (such as those defined in _GCLOUDIGNORE_REGISTRY), or if using
      a runtime that still supports skip_files, but both skip_files and
      a. gcloudignore file are present.

  Returns:
    An iterable object. The returned values are path names of source files that
    should be uploaded for deployment.
  """
  gcloudignore_registry = _GetGcloudignoreRegistry()
  registry_entry = gcloudignore_registry.Get(runtime, environment)

  if registry_entry:
    if has_explicit_skip_files:
      raise SkipFilesError(
          'You cannot use skip_files and have a .gcloudignore file in the same '
          'application. You should convert your skip_files patterns and put '
          'them in your .gcloudignore file. For information on the format and '
          'syntax of .gcloudignore files, see '
          'https://cloud.google.com/sdk/gcloud/reference/topic/gcloudignore.')
    file_chooser = gcloudignore.GetFileChooserForDir(
        source_dir,
        default_ignore_file=registry_entry,
        write_on_disk=True,
        gcloud_ignore_creation_predicate=lambda unused_dir: True,
        include_gitignore=False)
    return file_chooser.GetIncludedFiles(source_dir, include_dirs=False)
  elif os.path.exists(os.path.join(source_dir, gcloudignore.IGNORE_FILE_NAME)):
    if has_explicit_skip_files:
      raise SkipFilesError(
          'Cannot have both a .gcloudignore file and skip_files defined in '
          'the same application. We recommend you translate your skip_files '
          'ignore patterns to your .gcloudignore file. See '
          'https://cloud.google.com/sdk/gcloud/reference/topic/gcloudignore '
          'for more information about gcloudignore.')
    return gcloudignore.GetFileChooserForDir(source_dir).GetIncludedFiles(
        source_dir, include_dirs=False)
  else:
    return util.FileIterator(source_dir, skip_files_regex)
