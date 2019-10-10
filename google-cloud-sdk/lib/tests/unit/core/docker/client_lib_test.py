# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the docker client lib command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import json
import os
import subprocess
import sys

from distutils import version as distutils_version
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.docker import client_lib
from tests.lib import sdk_test_base
import mock

from six.moves import urllib


_TEST_DOCKER_VERSION = distutils_version.LooseVersion('1.13')


class ClientLibTest(sdk_test_base.WithFakeAuth):
  """Tests for the docker credential library."""

  def SetUp(self):
    self.process_mock = mock.Mock()
    self.process_mock.communicate.return_value = ("'output'", "'error'")
    self.process_mock.returncode = 0

    self.call_mock = self.StartObjectPatch(subprocess, 'call', autospec=True)
    self.popen_mock = self.StartObjectPatch(subprocess, 'Popen', autospec=True)
    self.popen_mock.return_value = self.process_mock

    self.test_dir = self.CreateTempDir('config')

  def testExecuteSuccess(self):
    self.call_mock.return_value = 1
    result = client_lib.Execute(['help'])
    self.assertTrue(self.call_mock.called)
    self.assertEqual(result, 1)

  def testExecuteDockerNotInstalled(self):
    self.call_mock.side_effect = OSError(errno.ENOENT,
                                         'No such file or directory', 'foo')

    with self.assertRaisesRegex(exceptions.Error, 'not installed'):
      client_lib.Execute(['ps', '-a'])

    self.assertTrue(self.call_mock.called)

  def testGetDockerConfigPathOldPath(self):
    self.StartEnvPatch({'DOCKER_CONFIG': ''})
    dockercfg_path, is_new_path = client_lib.GetDockerConfigPath()
    self.assertFalse(is_new_path)
    self.assertTrue('.dockercfg' in dockercfg_path)

  def testGetDockerConfigPathRespectsDockerConfigEnvVar(self):
    self.StartEnvPatch({'DOCKER_CONFIG': 'custom_directory'})
    dockercfg_path, _ = client_lib.GetDockerConfigPath(True)

    self.assertEqual(
        os.path.join('custom_directory', 'config.json'), dockercfg_path)

  def testGetDockerConfigPathReturnsCorrectDockerHomePath(self):
    # This test verifies that we locate the user's 'home directory' in the same
    # way as the Docker client:
    # https://docs.docker.com/engine/reference/commandline/login/

    dockercfg_path, _ = client_lib.GetDockerConfigPath(True)

    # The user's 'home directory' should be the temp folder that our mocks
    # return.
    self.assertTrue(dockercfg_path.startswith(self.home_path))

    if self.IsOnWindows():
      self.assertTrue(self.mock_expandvars.called)
      self.assertFalse(self.mock_get_home_path.called)
      self.mock_expandvars.assert_called_with('%USERPROFILE%')
    else:
      # Every platform aside from Windows should use files.GetHomeDir
      # to locate the user's home directory.
      self.assertTrue(self.mock_get_home_path.called)
      self.assertFalse(self.mock_expandvars.called)

  def testGetDockerProcess(self):
    proc_result = client_lib.GetDockerProcess(
        ['dummy_command'],
        stdin_file=sys.stdin,
        stdout_file=subprocess.PIPE,
        stderr_file=subprocess.PIPE)
    self.popen_mock.assert_called_once()
    self.assertEqual(proc_result.communicate(), ("'output'", "'error'"))

  def testGetDockerVersion(self):
    self.process_mock.communicate.return_value = ("'1.13'", "'stderr value'")
    result = client_lib.GetDockerVersion()
    self.assertEqual(_TEST_DOCKER_VERSION, result)

  def testGetDockerVersionNotFound(self):
    self.process_mock.returncode = 1
    with self.assertRaisesRegex(client_lib.DockerError,
                                'could not retrieve Docker client version'):
      client_lib.GetDockerVersion()

  def testGetNormalizedURL(self):
    input_url = 'http://gcr.io'
    expected_url = urllib.parse.urlparse(input_url)
    self.assertEqual(expected_url, client_lib.GetNormalizedURL(input_url))

  def testGetNormalizedURLFromLocalHost(self):
    input_url = 'localhost'
    expected_url = urllib.parse.urlparse('http://localhost')
    self.assertEqual(expected_url, client_lib.GetNormalizedURL(input_url))

  def testGetNormalizedURLNoScheme(self):
    input_url = 'gcr.io'
    expected_url = urllib.parse.urlparse('https://gcr.io')
    self.assertEqual(expected_url, client_lib.GetNormalizedURL(input_url))

  def testReadConfigurationFile(self):
    contents = {'x': 'y'}
    test_path = self.Touch(self.test_dir,
                           'test_config.json',
                           json.dumps(contents))
    self.assertEqual(contents, client_lib.ReadConfigurationFile(test_path))

  def testReadConfigurationFileInvalidFile(self):
    test_path = self.Touch(self.test_dir,
                           'test_config.json',
                           '')
    self.assertEqual({}, client_lib.ReadConfigurationFile(test_path))

  def testReadConfigurationFileEmptyFile(self):
    contents = 'FOO'
    test_path = self.Touch(self.test_dir,
                           'test_config.json',
                           contents)
    with self.assertRaisesRegex(client_lib.InvalidDockerConfigError,
                                r'Docker configuration file \[.*\] '
                                r'could not be read as JSON'):
      client_lib.ReadConfigurationFile(test_path)

  def testReadConfigurationFilePathNotFound(self):
    path_mock = self.StartObjectPatch(os.path, 'exists')
    path_mock.return_value = False
    self.assertEqual({}, client_lib.ReadConfigurationFile('//fake/path'))
    self.assertTrue(path_mock.called)

  def testReadConfigurationFileMissingPath(self):
    with self.assertRaisesRegex(ValueError,
                                'Docker configuration file path is empty'):
      client_lib.ReadConfigurationFile(None)
