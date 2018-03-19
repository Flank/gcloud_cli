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

import os
import re

from googlecloudsdk.api_lib.app import util
from googlecloudsdk.command_lib.app import runtime_registry
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


_GCLOUDIGNORE_REGISTRY = {
    runtime_registry.RegistryEntry(
        re.compile(r'nodejs\d*'), {util.Environment.STANDARD}):
        _NODE_GCLOUDIGNORE,
    runtime_registry.RegistryEntry(
        re.compile(r'php[789]\d*'), {util.Environment.STANDARD}):
        _PHP_GCLOUDIGNORE,
}


class SkipFilesGcloudignoreConflictError(core_exceptions.Error):

  def __init__(self):
    super(SkipFilesGcloudignoreConflictError, self).__init__(
        ('Cannot have both a .gcloudignore file and skip_files defined in '
         'the same application. We recommend you translate your skip_files '
         'ignore patterns to your .gcloudignore file.'))


def _GetGcloudignoreRegistry():
  return runtime_registry.Registry(_GCLOUDIGNORE_REGISTRY)


def GetSourceFileIterator(source_dir, skip_files_regex, has_explicit_skip_files,
                          runtime, env):
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
    env: util.Environment enum

  Raises:
    SkipFilesGcloudignoreConflictError: if using a runtime that still supports
      skip_files, and both skip_files and .gcloudignore are present.

  Returns:
    An object that can act as an iterable. The returned values are path names
    of source files that should be uploaded for deployment.
  """
  gcloudignore_registry = _GetGcloudignoreRegistry()
  registry_entry = gcloudignore_registry.Get(runtime, env)

  if registry_entry:
    file_chooser = gcloudignore.GetFileChooserForDir(
        source_dir,
        default_ignore_file=registry_entry,
        write_on_disk=True,
        gcloud_ignore_creation_predicate=lambda unused_dir: True,
        include_gitignore=False)
    return file_chooser.GetIncludedFiles(source_dir, include_dirs=False)
  elif os.path.exists(os.path.join(source_dir, gcloudignore.IGNORE_FILE_NAME)):
    if has_explicit_skip_files:
      raise SkipFilesGcloudignoreConflictError()
    return gcloudignore.GetFileChooserForDir(source_dir).GetIncludedFiles(
        source_dir, include_dirs=False)
  else:
    return util.FileIterator(source_dir, skip_files_regex)
