
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base for tests to make sure that checked in apitools clients are uptodate."""

from __future__ import absolute_import
from __future__ import unicode_literals
import difflib
import os
import shutil

from googlecloudsdk.api_lib.regen import generate
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
import six


def _GetClientPath(apis_dir, *path):
  return os.path.join(apis_dir, *path)


def AssertDiffEqual(expected, actual):
  """Like unittest.assertEqual with a diff in the exception message."""
  if expected != actual:
    unified_diff = difflib.unified_diff(expected.splitlines(),
                                        actual.splitlines())
    raise AssertionError('\n'.join(unified_diff))


# For each discovery doc generate a test based on config file.
def _MakeTest(base_dir, apis_dir, api_name, api_version, api_config):
  """Creates a test method to verify that generated api client is uptodate."""

  # Template for each api/version test to be added to ClientGenCliTest class.
  def TestGenClient(self):
    api_version_in_targets = api_config.get('version', api_version)
    prefix = api_name + '_' + api_version_in_targets

    with files.TemporaryDirectory() as tmp_dir_path:
      # Place discovery doc into tmp folder.
      discovery_dir = os.path.join(tmp_dir_path, apis_dir)
      files.MakeDir(discovery_dir)
      shutil.copy(
          _GetClientPath(base_dir, apis_dir, api_config['discovery_doc']),
          discovery_dir)
      # Create parent folder __init__ files, as they do not exist in tmp dir,
      # this is to avoid unnecessary warnings which generally does not happen.
      api_dir = os.path.join(discovery_dir, api_name)
      files.MakeDir(api_dir)
      with open(os.path.join(discovery_dir, '__init__.py'), 'w'):
        pass
      with open(os.path.join(api_dir, '__init__.py'), 'w'):
        pass

      generate.GenerateApi(tmp_dir_path, apis_dir, api_name, api_version,
                           api_config)
      generate.GenerateResourceModule(
          tmp_dir_path, apis_dir, api_name, api_version,
          api_config['discovery_doc'], api_config.get('resources', {}))

      expected_files = set([prefix + '_client.py', prefix + '_messages.py',
                            'resources.py', '__init__.py'])
      output_dir = os.path.join(tmp_dir_path, apis_dir, api_name, api_version)
      actual_files = set(os.listdir(output_dir))
      self.assertTrue(
          actual_files <= expected_files,
          'At most expected {0} but got {1}'
          .format(expected_files, actual_files))
      for file_name in actual_files:
        AssertDiffEqual(
            files.ReadFileContents(
                _GetClientPath(base_dir, apis_dir, api_name, api_version,
                               file_name)),
            files.ReadFileContents(os.path.join(output_dir, file_name)))

  format_string = b'testGen_{0}_{1}' if six.PY2 else 'testGen_{0}_{1}'
  TestGenClient.__name__ = format_string.format(api_name, api_version)
  return TestGenClient


def MakeTestsFrom(base_dir, config_file, test_class):
  config = yaml.load_path(config_file)

  apis_dir = config['root_dir']

  # For each api/version dynamically create a test method and add it to
  # given test class. Standard test runner will scan this class and will
  # register a separate test for each case.
  for api_name, api_version_config in six.iteritems(config['apis']):
    for api_version, api_config in six.iteritems(api_version_config):
      test_func = _MakeTest(base_dir, apis_dir,
                            api_name, api_version, api_config)
      setattr(test_class, test_func.__name__, test_func)
