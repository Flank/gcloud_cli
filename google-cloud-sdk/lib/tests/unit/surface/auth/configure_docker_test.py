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

from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.docker import client_lib
from googlecloudsdk.core.docker import credential_utils as cred_utils
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ConfigureDockerTest(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.test_dir = self.CreateTempDir('config')
    self.test_config = os.path.join(self.test_dir, 'config.json')
    self.StartObjectPatch(
        cred_utils.Configuration, 'SupportsRegistryHelpers', return_value=True)
    self.StartObjectPatch(client_lib, 'GetDockerVersion', return_value='17.05')
    self.StartObjectPatch(
        client_lib,
        'GetDockerConfigPath',
        return_value=(self.test_config, True))
    self.StartObjectPatch(files, 'SearchForExecutableOnPath', return_value=1)

  def _WriteTestDockerConfig(self, contents):
    new_cfg = self.test_config
    directory = os.path.dirname(new_cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(new_cfg, contents, private=True)
    return new_cfg

  def testConfigureSuccess(self):
    self._WriteTestDockerConfig('{}')
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrContains('Docker configuration file updated.')
    self.AssertErrContains(self.test_config)
    config_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     config_info.contents)

  def testDockerNotInstalled(self):
    self.StartObjectPatch(
        cred_utils.Configuration, 'ReadFromDisk'
    ).side_effect = client_lib.InvalidDockerConfigError(
        'Could not compare Docker client version:[No such file or directory]')
    with self.assertRaisesRegex(client_lib.DockerError,
                                'No such file or directory'):
      self.WriteInput('Y\n')
      self.Run('auth configure-docker')

  def testDockerConfigNotFound(self):
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrContains('Docker configuration file updated.')
    self.AssertErrContains('config.json')
    config_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     config_info.contents)

  def testDockerNotOnPath(self):

    def executable_on_path(binary):
      if binary == 'docker':
        return False
      return True

    self.StartObjectPatch(
        files, 'SearchForExecutableOnPath', side_effect=executable_on_path)
    self._WriteTestDockerConfig('{}')
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrContains(
        'WARNING: `docker` not in system PATH.\n'
        '`docker` and `docker-credential-gcloud` need to be in the same PATH '
        'in order to work correctly together.\n'
        'gcloud\'s Docker credential helper can be configured but '
        'it will not work until this is corrected.')
    config_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     config_info.contents)

  def testDockerCredentialGcloudNotOnPath(self):

    def executable_on_path(binary):
      if binary == 'docker-credential-gcloud':
        return False
      return True

    self.StartObjectPatch(
        files, 'SearchForExecutableOnPath', side_effect=executable_on_path)
    self._WriteTestDockerConfig('{}')
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrContains(
        'WARNING: `docker-credential-gcloud` not in system PATH.\n'
        'gcloud\'s Docker credential helper can be configured but '
        'it will not work until this is corrected.')
    config_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     config_info.contents)

  def testExistingConfigurationAlreadyConfigured(self):
    self._WriteTestDockerConfig(
        json.dumps(cred_utils.GetGcloudCredentialHelperConfig(), indent=2))
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrMatches(r'gcloud credential helpers already '
                          r'registered correctly.')
    self.AssertErrNotContains('Docker configuration file updated.')

  def testExistingConfigurationOverwrite(self):
    test_mappings = {'credHelpers': {'us.gcr.io': 'gcloud'}}
    self._WriteTestDockerConfig(json.dumps(test_mappings, indent=2))
    self.WriteInput('Y\n')
    self.Run('auth configure-docker')
    self.AssertErrMatches(r'Your config file at \[.*\] contains these '
                          r'credential helper entries')
    self.AssertErrContains('Docker configuration file updated.')
    config_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     config_info.contents)

  def testConfigureIOError(self):
    self._WriteTestDockerConfig('{}')
    self.StartObjectPatch(
        files,
        'WriteFileAtomically').side_effect = IOError('File Write Error FOO')
    with self.assertRaisesRegex(client_lib.DockerError,
                                r'Error writing Docker configuration to disk: '
                                r'File Write Error FOO'):
      self.WriteInput('Y\n')
      self.Run('auth configure-docker')

  def testReadConfigError(self):
    self.StartObjectPatch(
        cred_utils.Configuration,
        'ReadFromDisk',
        side_effect=client_lib.InvalidDockerConfigError)
    with self.assertRaises(client_lib.InvalidDockerConfigError):
      self.Run('auth configure-docker')

  def testInvalidDockerVersion(self):
    self.StartObjectPatch(
        cred_utils.Configuration, 'SupportsRegistryHelpers', return_value=False)
    with self.assertRaises(exceptions.Error):
      self.Run('auth configure-docker')
