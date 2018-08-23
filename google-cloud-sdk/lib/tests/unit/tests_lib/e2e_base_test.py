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

"""Tests for the e2e_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import files
from tests.lib import e2e_base
from tests.lib import test_case

import mock


class E2eBaseTest(test_case.Base):

  def testConfig_NoOverride(self):
    config_file = e2e_base._LoadTestConfig()
    if config_file:
      self.assertIn('auth_data', config_file)
    else:
      self.assertIsNone(config_file)

  def testOverrideConfig_FileExists_AbsolutePath(self):
    with files.TemporaryDirectory() as tmp_dir:
      config_file = os.path.join(tmp_dir, 'config.yaml')
      files.WriteFileContents(config_file, 'value: 42')
      with mock.patch.dict(os.environ, {'CLOUD_SDK_TEST_CONFIG': config_file}):
        self.assertEqual({'value': 42}, e2e_base._LoadTestConfig())

  def testOverrideConfig_FileExists_RelativePathCurrentDir(self):
    with files.TemporaryDirectory(change_to=True):
      config_file = 'config.yaml'
      files.WriteFileContents(config_file, 'value: 42')
      with mock.patch.dict(os.environ, {'CLOUD_SDK_TEST_CONFIG': config_file}):
        self.assertEqual({'value': 42}, e2e_base._LoadTestConfig())

  def testOverrideConfig_FileExists_RelativePathProjecDir(self):
    config_file = os.path.join('tests', 'unit', 'tests_lib',
                               'testdata', 'config.yaml')
    with mock.patch.dict(os.environ, {'CLOUD_SDK_TEST_CONFIG': config_file}):
      self.assertEqual({'value': 21}, e2e_base._LoadTestConfig())

  def testOverrideConfig_FileDoesNotExists_AbsolutePath(self):
    with files.TemporaryDirectory() as tmp_dir:
      config_file = os.path.join(tmp_dir, 'config.yaml')
      with mock.patch.dict(os.environ, {'CLOUD_SDK_TEST_CONFIG': config_file}):
        with self.assertRaises(ValueError):
          e2e_base._LoadTestConfig()


if __name__ == '__main__':
  test_case.main()
