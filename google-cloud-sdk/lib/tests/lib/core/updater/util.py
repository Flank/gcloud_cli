# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Various test utilities for the updater."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import sys
import tarfile
import tempfile

from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base

import six
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


def FilesystemSupportsUnicodeEncodedPaths():
  """Returns True if the filesystem supports UNICODE encoded paths."""
  try:
    path = 'Ṳᾔḯ¢◎ⅾℯ'
    path.encode(sys.getfilesystemencoding())
    return True
  except (UnicodeError, TypeError):
    return False


class Base(sdk_test_base.SdkBase):
  """Base class for all updater tests."""

  # It doesn't really matter what these are, just as long as they are different.
  CURRENT_PLATFORM = platforms.Platform(platforms.OperatingSystem.LINUX, None)
  OTHER_PLATFORM = platforms.Platform(platforms.OperatingSystem.WINDOWS, None)
  PATHS = [
      os.path.join('lib', '{0}-{1}', 'file1.py'),
      os.path.join('lib', '{0}-{1}', 'file2.py'),
      os.path.join('platform', '{0}-{1}', 'code1.py'),
      os.path.join('platform', '{0}-{1}', 'code2.py'),
      os.path.join('bin', '{0}-{1}.py'),
  ]

  def SetUp(self):
    # sys.getfilesystemencoding() is initialized early in python startup and
    # cannot be changed thereafter. Some test runners do not give us the
    # opportunity to do the incantation to get it initialized to handle unicode
    # paths. So we check here if the default test runner encoding supports
    # unicode and if so use an installation directory name containing unicode
    # characters, otherwise just an ascii installation directory name. We know
    # that most of our test runners support unicode in pathnames.
    if FilesystemSupportsUnicodeEncodedPaths():
      sdk_root_dir = 'Ṳᾔḯ¢◎ⅾℯ-cloudsdk'
    else:
      sdk_root_dir = 'cloudsdk'
    self.sdk_root_path = self.CreateTempDir(sdk_root_dir)

    self.staging_path = self.CreateTempDir('staging')
    self.old_executable = sys.executable
    sys.executable = 'current/python'

  def TearDown(self):
    sys.executable = self.old_executable

  def Resource(self, *args):
    """Returns the path to a test resource under the 'data' directory.

    Args:
      *args: str, The relative path parts of the resource under the 'data'
        directory.

    Returns:
      str, The full path to the resource.
    """
    return super(Base, self).Resource(
        'tests', 'unit', 'core', 'updater', 'testdata', *args)

  def URLFromFile(self, base_path, *paths):
    """Creates a URL from a file and more path parts.

    Correctly converts Windows paths as well.

    Args:
      base_path: str, The absolute file path.
      *paths: str, More parts to add onto the ends of paths.

    Returns:
      str, A properly formatted URL.
    """
    url = ('file://' +
           ('/' if not base_path.startswith('/') else '') +
           base_path.replace('\\', '/'))
    return '/'.join([url] + list(paths))

  def CheckPathsExist(self, rel_paths, exists=True, alt_root=None):
    """Verifies that a given path does or does not exist.

    Args:
      rel_paths: list of str, The paths relative to the root directory to
        verify.
      exists: bool, True to ensure they exist, False to ensure they do not
        exist.
      alt_root: An optional path string to check the paths relative to.  If
        None, Directories.RootDir() will be used
    """
    root = alt_root if alt_root else self.sdk_root_path
    for p in rel_paths:
      full_path = os.path.join(root, p)
      if (os.path.isfile(full_path) or os.path.isdir(full_path)
          or os.path.islink(full_path)) is not exists:
        self.fail('File [{0}] in wrong state, should exist [{1}]'
                  .format(p, exists))

  def CreateTempTar(self, temp_dir, rel_paths, file_contents=''):
    """Creates a tar file with the given files in it."""
    tar_dir = tempfile.mkdtemp(dir=temp_dir)
    for rel_path in rel_paths:
      self.Touch(tar_dir, rel_path, contents=file_contents, makedirs=True)
    return self.CreateTempTarFromDir(temp_dir, tar_dir)

  def CreateTempTarFromDir(self, temp_dir, tar_dir):
    """Creates a tar file from the contents of a directory."""
    f, name = tempfile.mkstemp(suffix='.tar.gz', dir=temp_dir)
    os.close(f)

    with tarfile.open(name, mode='w|gz') as tar_file:
      for top_element in os.listdir(tar_dir):
        tar_file.add(os.path.join(tar_dir, top_element), top_element)
    return name

  def CreateFakeComponent(self, name, deps, version=None, is_required=False):
    """Constructs a schemas.Component from the given data."""
    return schemas.Component(
        id=name, details=None,
        version=schemas.ComponentVersion(build_number=version,
                                         version_string=version),
        dependencies=deps, data=None, is_hidden=False, is_required=is_required,
        is_configuration=False,
        platform=schemas.ComponentPlatform(None, None))

  def CreateSnapshotFromStrings(self, revision, component_string,
                                dependency_string):
    """Generates an entire ComponentSnaphost from some strings.

    Args:
      revision: int, The revision of the snapshot.
      component_string: A comma separated string of components like a1,b2,c1
        where the letters are component names and the numbers are the current
        version of that component in this snapshot.
      dependency_string: A string like a->b|b->c where the values are component
        names (no versions) and the -> represents an dependency.  Multiple
        dependencies are separated by the | character.

    Returns:
      A ComponentSnapshot.
    """
    regex = r'([a-z]+)(\d*)'
    component_versions = {}
    if component_string:
      for c in component_string.split(','):
        result = re.match(regex, c)
        component_versions[result.group(1)] = result.group(2)

    dependencies = dict((c, list()) for c in component_versions)
    if dependency_string:
      for dependency in dependency_string.split('|'):
        component, dependency_list = dependency.split('->')
        for d in dependency_list.split(','):
          dependencies[component].append(d)

    component_tuples = []
    for c, deps in six.iteritems(dependencies):
      component_tuples.append((c, component_versions[c], deps, None))

    return self.CreateSnapshotFromComponents(revision, component_tuples)

  def CreateComponentJSON(self, component_id, version, dependencies,
                          is_required=False, data_url=None):
    """Generates a JSON dictionary for a component from the given data."""
    data = {
        'id': component_id,
        'is_required': is_required,
        'details': {
            'display_name': component_id + ' Nice Name',
            'description': 'This is component: ' + component_id
        },
        'version': {
            'build_number': version,
            'version_string': str(version)
        },
        'dependencies': dependencies,
        }
    if data_url:
      data['data'] = {
          'type': 'tar',
          'source': data_url,
          'checksum': str(version),
          'contents_checksum': str(version)
      }
    return data

  def CreateSnapshotFromComponents(self, revision, component_tuples,
                                   release_notes_file=None, notifications=None):
    """Generates a ComponentSnapshot from the given tuples.

    Args:
      revision: int, The revision of the snapshot.
      component_tuples: A list of tuples in the format
        (component_id, version, dependencies, data_url) for each component to
        add to the snapshot.
      release_notes_file: str, The path to a local release notes file for
        testing.  If None, a dummy file is used.
      notifications: list, A list of dictionary representations of
        NotificationSpec objects to insert into this snapshot.

    Returns:
      A ComponentSnapshot.
    """
    components = []
    for component_id, version, dependencies, data_url in component_tuples:
      is_required = component_id.startswith('req_')
      data = self.CreateComponentJSON(
          component_id, version, dependencies, is_required, data_url)
      components.append(data)
    release_notes_url = (self.URLFromFile(release_notes_file)
                         if release_notes_file else 'RELEASE_NOTES')

    data = {'revision': revision, 'release_notes_url': release_notes_url,
            'version': str(revision), 'components': components,
            'notifications': notifications}
    sdk_definition = schemas.SDKDefinition.FromDictionary(data)
    return snapshots.ComponentSnapshot(sdk_definition)

  def GeneratePathsFor(self, component_id, version):
    """Generates a list of relative file paths for this component."""
    return [p.format(component_id, version) for p in self.PATHS]

  def CreateSnapshotFromComponentsGenerateTars(
      self, revision, component_tuples, release_notes_file=None,
      notifications=None):
    """Generates a ComponentSnapshot and a real .tar file for each component.

    Args:
      revision: int, The revision of the snapshot.
      component_tuples: A list of tuples in the format
        (component_id, version, dependencies) for each component to add to the
        snapshot.
      release_notes_file: str, The path to a local release notes file for
        testing.  If None, a dummy file is used.
      notifications: list, A list of dictionary representations of
        NotificationSpec objects to insert into this snapshot.

    Returns:
      A tuple of (ComponentSnapshot, relative file paths).
    """
    new_tuples = []
    paths = {}
    for component_id, version, dependencies in component_tuples:
      rel_paths = self.GeneratePathsFor(component_id, version)
      tar_file = self.CreateTempTar(self.staging_path, rel_paths)
      new_tuples.append((
          component_id, version, dependencies,
          self.URLFromFile(six.moves.urllib.request.pathname2url(tar_file))))
      paths[component_id] = rel_paths
    snapshot = self.CreateSnapshotFromComponents(
        revision, new_tuples, release_notes_file=release_notes_file,
        notifications=notifications)
    return snapshot, paths

  def CreateTempSnapshotFileFromSnapshot(self, snapshot, versioned=False):
    """Writes the given snapshot to a real file and return the path to it."""
    handle, path = tempfile.mkstemp(suffix='.temp_snapshot',
                                    dir=self.staging_path)
    os.close(handle)
    snapshot.WriteToFile(path)

    if versioned:
      file_name = (
          update_manager.UpdateManager.VERSIONED_SNAPSHOT_FORMAT.format(
              snapshot.version))
      snapshot.WriteToFile(os.path.join(os.path.dirname(path), file_name))

    return path

  def ChangePlatformForComponents(self, snapshot, ids, platform=None):
    """Change the opt-in platform for the given components in the snapshot.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot to update
      ids: list(str), The components to update the platforms for
      platform: platforms.Platform, The platform to set the given components to.
    """
    if not platform:
      platform = self.OTHER_PLATFORM
    operating_system = ([platform.operating_system]
                        if platform.operating_system else None)
    architecture = [platform.architecture] if platform.architecture else None
    component_platform = schemas.ComponentPlatform(operating_system,
                                                   architecture)
    for component_id in ids:
      snapshot.components[component_id].platform = component_platform
