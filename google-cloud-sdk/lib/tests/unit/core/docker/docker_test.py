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
"""Tests for the docker command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import base64
import errno
import json
import os
import subprocess

from distutils import version as distutils_version
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.docker import client_lib
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.docker import docker
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock

_TOKEN = 'ma-token'
_ACCESS_TOKEN_USERNAME = 'gclouddockertoken'
_EMAIL = 'not@val.id'
_EXPECTED_DOCKER_OPTIONS = [
    '--username=' + _ACCESS_TOKEN_USERNAME, '--password=' + _TOKEN
]
_CREDENTIAL_STORE_KEY = 'credsStore'
_NON_DEFAULT_REGISTRY = 'snapify.com'


class DockerTest(sdk_test_base.WithFakeAuth):
  """Tests for the docker credential library."""

  def SetUp(self):
    self.process_mock = mock.Mock()
    self.process_mock.communicate.return_value = ("'output'", "'error'")
    self.process_mock.returncode = 0

    self.popen_mock = self.StartObjectPatch(subprocess, 'Popen', autospec=True)
    self.popen_mock.return_value = self.process_mock

    # Track whether we refreshed the access token
    self.refreshes = 0

    # pylint: disable=unused-argument, Has to match real signature.
    def FakeRefresh(cred, http=None):
      self.refreshes += 1
      if cred:
        cred.access_token = _TOKEN

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)

    auth_str = _ACCESS_TOKEN_USERNAME + ':' + _TOKEN
    self.auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

  def TearDown(self):
    for new_path in [True, False]:
      dcfg, unused_new_file = client_lib.GetDockerConfigPath(new_path)
      # If we created .dockercfg and/or .docker/config.json,
      # clear it to reset for the next test.
      if os.path.exists(dcfg):
        os.remove(dcfg)

  def WriteNewDockerConfig(self, contents):
    new_cfg, unused_true = client_lib.GetDockerConfigPath(force_new=True)
    directory = os.path.dirname(new_cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(new_cfg, contents, private=True)
    return new_cfg

  def TouchOldDockerConfig(self):
    cfg, new_format = client_lib.GetDockerConfigPath(force_new=False)
    self.assertFalse(new_format)
    directory = os.path.dirname(cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(cfg, '{}', private=True)
    return cfg

  def CheckDockerConfigAuths(self, expected):
    actual = docker.ReadDockerAuthConfig()
    self.assertEqual(expected, actual)

  def AssertDockerLoginForRegistry(self, registry, expected_opts):

    # pylint: disable=unused-argument, Has to match real signature.
    def MockPopen(*args, **kwargs):
      exec_args = args[0]

      # Assume that 'docker login' does the right thing,
      # updating its auth store with the given options.
      # Verify that 'docker login' was being called.
      self.assertEqual('docker', exec_args[0])
      self.assertEqual('login', exec_args[1])

      docker_login_options = exec_args[2:-1]
      target_server = exec_args[-1]

      # Verify that all of the options are as expected.
      self.assertEqual(sorted(docker_login_options), sorted(expected_opts))

      # Verify that the target server was correct, i.e. the last argument.
      self.assertEqual('https://' + registry, target_server)
      # Make sure that the mock's return_value is returned.
      return mock.DEFAULT

    return MockPopen

  def GetFakeDockerConfigInfo(self,
                              path,
                              new_format=True,
                              version='1.13',
                              contents=None):
    docker_info = docker.DockerConfigInfo(
        path,
        is_new_format=new_format,
        cfg_version=distutils_version.LooseVersion(version),
        cfg_contents=contents)
    return docker_info

  def testRoundtrip(self):
    docker.WriteDockerAuthConfig({})
    self.CheckDockerConfigAuths({})

  def testUpdateWithCredHelperConfigured(self):
    self.WriteNewDockerConfig(json.dumps({_CREDENTIAL_STORE_KEY: 'helper'}))
    self.popen_mock.side_effect = self.AssertDockerLoginForRegistry(
        constants.DEFAULT_REGISTRY, _EXPECTED_DOCKER_OPTIONS)

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.popen_mock.assert_called_once()

  def testMultipleUpdateCredHelperConfigured(self):
    self.WriteNewDockerConfig(json.dumps({_CREDENTIAL_STORE_KEY: 'helper'}))
    self.popen_mock.side_effect = self.AssertDockerLoginForRegistry(
        constants.DEFAULT_REGISTRY, _EXPECTED_DOCKER_OPTIONS)
    self.assertFalse(self.popen_mock.called)

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.popen_mock.side_effect = self.AssertDockerLoginForRegistry(
        constants.REGIONAL_REGISTRIES[0], _EXPECTED_DOCKER_OPTIONS)

    docker.UpdateDockerCredentials(constants.REGIONAL_REGISTRIES[0],
                                   refresh=False)
    self.assertEqual(1, self.refreshes)

    # 2x(docker login)
    self.assertEqual(self.popen_mock.call_count, 2)

  def testUpdateCredHelperConfiguredAndDockerFails(self):
    self.WriteNewDockerConfig(json.dumps({_CREDENTIAL_STORE_KEY: 'helper'}))
    self.popen_mock.side_effect = self.AssertDockerLoginForRegistry(
        constants.DEFAULT_REGISTRY, _EXPECTED_DOCKER_OPTIONS)
    self.process_mock.returncode = -1  # A failure code.

    with self.assertRaisesRegex(exceptions.Error, 'login failed'):
      docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.popen_mock.assert_called_once()

  def testUpdateWorksWhenDockerNotInstalled(self):
    # A subprocess may or may not be created, but needs to be mocked if so.
    self.popen_mock.side_effect = OSError(errno.ENOENT,
                                          'No such file or directory', 'foo')

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })

  def testUpdateCredHelperNotConfigured(self):
    # We get to modify the docker config directly in the non-cred-helper case.
    self.WriteNewDockerConfig('{}')

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })
    self.assertFalse(self.popen_mock.called)

  def testMultipleUpdateCredHelperNotConfigured(self):
    self.WriteNewDockerConfig('{}')

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)
    docker.UpdateDockerCredentials(constants.REGIONAL_REGISTRIES[0],
                                   refresh=False)
    self.assertEqual(1, self.refreshes)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        },
        'https://' + constants.REGIONAL_REGISTRIES[0]: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })

  def testUpdateWithOldConfig(self):
    self.TouchOldDockerConfig()

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })

  def testUpdateEmptyFile(self):
    self.WriteNewDockerConfig('')

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })
    self.assertFalse(self.popen_mock.called)

  def testUpdateInvalidJsonFile(self):
    self.WriteNewDockerConfig('not-json')

    with self.assertRaisesRegex(
        client_lib.InvalidDockerConfigError,
        r'Docker configuration file \[.*config\.json\] could not be read as '
        r'JSON: .*'):
      docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.assertFalse(self.popen_mock.called)

  def testUpdateWhitespaceFile(self):
    self.WriteNewDockerConfig('   \t\n')

    docker.UpdateDockerCredentials(constants.DEFAULT_REGISTRY)

    self.CheckDockerConfigAuths({
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': self.auth
        }
    })
    self.assertFalse(self.popen_mock.called)

if __name__ == '__main__':
  test_case.main()
