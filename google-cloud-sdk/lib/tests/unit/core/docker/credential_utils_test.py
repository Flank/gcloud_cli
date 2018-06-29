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
"""Tests for the docker credential utils library."""
from __future__ import absolute_import
from __future__ import unicode_literals
import collections
import json
import os

from distutils import version as distutils_version
from googlecloudsdk.core.docker import client_lib
from googlecloudsdk.core.docker import credential_utils as cred_utils
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base

_EMPTY_JSON_OBJECT_STRING = '{}'
_INVALID_CRED_VERSION = '1.10'
_TEST_REGISTRIES = ['gcr.io', 'us.gcr.io', 'xyz.gcr.io']
_TEST_MAPPINGS = collections.OrderedDict(
    (x, 'gcloud') for x in _TEST_REGISTRIES)
_TEST_CRED_HELPERS_CONTENT_DICT = {
    cred_utils.CREDENTIAL_HELPER_KEY: _TEST_MAPPINGS
}
_TEST_CRED_HELPERS_CONTENT_STRING = json.dumps(
    _TEST_CRED_HELPERS_CONTENT_DICT, indent=2)


class ConfigurationTest(sdk_test_base.WithFakeAuth):
  """Tests for the docker Configuration library."""

  def SetUp(self):
    self.test_dir = self.CreateTempDir('config')
    self.test_config = os.path.join(self.test_dir, 'config.json')
    self.test_version = '1.13'
    self.StartObjectPatch(
        cred_utils,
        'DefaultAuthenticatedRegistries',
        return_value=_TEST_REGISTRIES)
    self.StartObjectPatch(
        client_lib,
        'GetDockerConfigPath',
        return_value=(self.test_config, True))
    self.mock_get_docker_version = self.StartObjectPatch(
        client_lib, 'GetDockerVersion', return_value=self.test_version)

  def _WriteTestDockerConfig(self, json_str):
    """Writes Test Docker configuration with json_str to test_dir."""
    new_cfg = self.test_config
    directory = os.path.dirname(new_cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(new_cfg, json_str, private=True)
    return new_cfg

  def _GetFakeConfiguration(self, json_str=_EMPTY_JSON_OBJECT_STRING):
    """Builds Test Configuration object from json_str."""
    return cred_utils.Configuration.FromJson(json_str,
                                             self.test_config)

  def testGetGcloudCredentialHelperConfig(self):
    self.assertEqual(cred_utils.GetGcloudCredentialHelperConfig(),
                     _TEST_CRED_HELPERS_CONTENT_DICT)

  def testGetOrderedCredentialHelperRegistries(self):
    self.assertEqual(_TEST_MAPPINGS,
                     cred_utils.GetOrderedCredentialHelperRegistries())

  def testGetRegisteredCredentialHelpers(self):
    docker_info = self._GetFakeConfiguration(
        _TEST_CRED_HELPERS_CONTENT_STRING)
    self.assertEqual(_TEST_CRED_HELPERS_CONTENT_DICT,
                     docker_info.GetRegisteredCredentialHelpers())

  def testGetRegisteredCredentialHelpersEmptyDockerFile(self):
    docker_info = self._GetFakeConfiguration(None)
    self.assertEqual({}, docker_info.GetRegisteredCredentialHelpers())

  def testRegisterCredentialHelpers(self):
    docker_info = self._GetFakeConfiguration(None)
    docker_info.RegisterCredentialHelpers(_TEST_MAPPINGS)
    updated_docker_info = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(updated_docker_info.GetRegisteredCredentialHelpers(),
                     _TEST_CRED_HELPERS_CONTENT_DICT)

  def testRegisterCredentialHelpersBadMappings(self):
    docker_info = self._GetFakeConfiguration('{"credHelpers": {"foo": "bar"}}')
    with self.assertRaisesRegex(
        ValueError,
        r'Invalid Docker credential helpers mappings'):
      docker_info.RegisterCredentialHelpers(['foo'])

  def testRegisterCredentialHelpersError(self):
    self.StartObjectPatch(files, 'WriteFileAtomically').side_effect = IOError()
    docker_info = self._GetFakeConfiguration()
    with self.assertRaisesRegex(cred_utils.DockerConfigUpdateError,
                                r'Error writing Docker configuration to disk'):
      docker_info.RegisterCredentialHelpers()

  def testRegisterCredentialHelpersNotSupported(self):
    docker_info = self._GetFakeConfiguration()
    self.mock_get_docker_version.return_value = '1.01'
    with self.assertRaisesRegex(cred_utils.DockerConfigUpdateError,
                                r'Credential Helpers not supported for this '
                                r'Docker client version 1.0'):
      docker_info.RegisterCredentialHelpers()

  def testReadFromDisk(self):
    self._WriteTestDockerConfig(_TEST_CRED_HELPERS_CONTENT_STRING)
    expected_config = self._GetFakeConfiguration(
        _TEST_CRED_HELPERS_CONTENT_STRING)
    actual_config = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(actual_config, expected_config)

  def testReadFromDiskMissingPath(self):
    self._WriteTestDockerConfig(_TEST_CRED_HELPERS_CONTENT_STRING)
    actual_config = cred_utils.Configuration.ReadFromDisk(path='/fake/path')
    self.assertEqual(actual_config.contents, {})

  def testSupportsRegistryHelpers(self):
    config = self._GetFakeConfiguration(_TEST_CRED_HELPERS_CONTENT_STRING)
    self.assertTrue(config.SupportsRegistryHelpers())

  def testDoesntSupportRegistryHelpers(self):
    config = self._GetFakeConfiguration(_TEST_CRED_HELPERS_CONTENT_STRING)
    self.mock_get_docker_version.return_value = '1.01'
    self.assertFalse(config.SupportsRegistryHelpers())

  def testSupportRegistryHelpersException(self):
    config = self._GetFakeConfiguration(_TEST_CRED_HELPERS_CONTENT_STRING)
    self.mock_get_docker_version.side_effect = Exception('any error')
    self.assertTrue(config.SupportsRegistryHelpers())  # Fail open.

  def testWriteToDisk(self):
    expected_config = self._GetFakeConfiguration(
        _TEST_CRED_HELPERS_CONTENT_STRING)
    expected_config.WriteToDisk()
    written_config = cred_utils.Configuration.ReadFromDisk()
    self.assertEqual(written_config, expected_config)

  def testWriteToDiskError(self):
    self.StartObjectPatch(files, 'WriteFileAtomically').side_effect = IOError()
    with self.assertRaisesRegex(cred_utils.DockerConfigUpdateError,
                                r'Error writing Docker configuration '
                                r'to disk:'):
      self._GetFakeConfiguration().WriteToDisk()

  def testFromJson(self):
    json_str = '{"credHelpers": {"foo": "bar"}}'
    parsed_config = self._GetFakeConfiguration(json_str)
    expected_config = cred_utils.Configuration(json.loads(json_str),
                                               self.test_config)
    self.assertEqual(parsed_config, expected_config)

  def testToJson(self):
    config = cred_utils.Configuration(_TEST_CRED_HELPERS_CONTENT_DICT,
                                      self.test_config)
    self.assertEqual(_TEST_CRED_HELPERS_CONTENT_STRING, config.ToJson())

  def testDockerVersion(self):
    expected_version = distutils_version.LooseVersion(self.test_version)
    config = self._GetFakeConfiguration(_TEST_CRED_HELPERS_CONTENT_STRING)
    self.assertEqual(config.DockerVersion(), expected_version)
