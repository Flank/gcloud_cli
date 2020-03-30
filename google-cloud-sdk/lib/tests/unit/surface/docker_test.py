# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import os

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.docker import client_lib
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.docker import docker
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

_PROJECT = 'my-project-7465'

_TOKEN = 'ma-token'
_ACCESS_TOKEN_USERNAME = 'gclouddockertoken'
_EMAIL = 'not@val.id'
_EXPECTED_DOCKER_OPTIONS = ['--username=' + _ACCESS_TOKEN_USERNAME,
                            '--password=' + _TOKEN]
_CREDENTIAL_STORE_KEY = 'credsStore'


class DockerTests(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth):
  """Tests for the gcloud docker command."""

  def SetUp(self):
    properties.VALUES.core.project.Set(_PROJECT)
    self.execute_mock = self.StartPatch(
        'googlecloudsdk.core.docker.client_lib.Execute', autospec=True)

    self.process_mock = mock.Mock()
    self.process_mock.communicate.return_value = ('stdout', 'stderr')
    self.process_mock.returncode = 0
    self.get_process_mock = self.StartPatch(
        'googlecloudsdk.core.docker.client_lib.GetDockerProcess', autospec=True)
    self.get_process_mock.return_value = self.process_mock

    # Track whether we refreshed the access token
    self.refreshed = False

    # pylint: disable=unused-argument, Has to match real signature.
    def FakeRefresh(cred, http=None):
      self.refreshed = True
      if cred:
        cred.access_token = _TOKEN
        self.StartObjectPatch(store, 'Load', return_value=cred)

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)

  def TearDown(self):
    for new_path in [True, False]:
      dcfg, unused_new_file = client_lib.GetDockerConfigPath(new_path)
      # If we created .dockercfg and/or .docker/config.json,
      # clear it to reset for the next test.
      if os.path.exists(dcfg):
        os.remove(dcfg)

  def CheckDockerConfig(self, expected):
    actual_json = docker.ReadDockerAuthConfig()
    # Avoid having to annotate all strings with u'foo' for
    # Python 2.6 compatibility by simply roundtripping
    # through JSON once here.
    sanitized_dict = json.loads(json.dumps(expected))
    self.assertEqual(sanitized_dict, actual_json)

  def TouchNewDockerConfig(self):
    new_cfg, unused_true = client_lib.GetDockerConfigPath(force_new=True)
    directory = os.path.dirname(new_cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(new_cfg, '{}', private=True)

  def WriteNewDockerConfig(self, full_cfg):
    new_cfg, unused_true = client_lib.GetDockerConfigPath(force_new=True)
    directory = os.path.dirname(new_cfg)
    if not os.path.exists(directory):
      os.makedirs(directory)
    files.WriteFileContents(new_cfg, encoding.Decode(json.dumps(full_cfg)),
                            private=True)

  def AssertRegistryLogin(self, registry):

    # pylint: disable=unused-argument, Has to match real signature.
    def LoginCommandVerifier(*args, **kwargs):
      exec_args = args[0]

      # Assume that 'docker login' does the right thing,
      # updating its auth store with the given options.
      # Verify that 'docker login' was being called.
      self.assertEqual('login', exec_args[0])

      docker_login_options = exec_args[1:-1]
      target_server = exec_args[-1]

      # Verify that all of the options are as expected.
      self.assertCountEqual(docker_login_options, _EXPECTED_DOCKER_OPTIONS)

      # Verify that the target server was correct, i.e. the last argument.
      self.assertEqual(registry, target_server)

      self.process_mock.communicate.return_value = ('Login Succeeded\n', '')

      # Make sure that the mock's return_value is returned.
      return mock.DEFAULT

    return LoginCommandVerifier

  def DockerLoginWithOutput(self, registry, stdout, stderr):

    # pylint: disable=unused-argument, Has to match real signature.
    def LoginCommandVerifier(*args, **kwargs):
      exec_args = args[0]

      # Assume that 'docker login' does the right thing,
      # updating its auth store with the given options.
      # Verify that 'docker login' was being called.
      self.assertEqual('login', exec_args[0])

      docker_login_options = exec_args[1:-1]
      target_server = exec_args[-1]

      # Verify that all of the options are as expected.
      self.assertCountEqual(docker_login_options, _EXPECTED_DOCKER_OPTIONS)

      # Verify that the target server was correct, i.e. the last argument.
      self.assertEqual(registry, target_server)

      self.process_mock.communicate.return_value = (stdout, stderr)

      # Make sure that the mock's return_value is returned.
      return mock.DEFAULT

    return LoginCommandVerifier

  def AssertCommand(self, expected_command):
    # pylint: disable=unused-argument, Has to match real signature.
    def MockExecute(*args, **kwargs):
      exec_args = args[0]

      self.assertCountEqual(
          exec_args,
          expected_command,
          'Unexpected arguments, wanted {want}, but got: {got}'.format(
              want=expected_command, got=exec_args))

    return MockExecute

  def RecordRegistriesForLogin(self):
    self.logins = []

    # pylint: disable=unused-argument, Has to match real signature.
    def MultiLoginCommandVerifier(*args, **kwargs):
      # Assume that 'docker login' does the right thing,
      # updating its auth store with the given options.
      exec_args = args[0]

      # Verify that 'docker login' was being called.
      self.assertEqual('login', exec_args[0])

      docker_login_options = exec_args[1:-1]
      target_server = exec_args[-1]

      # Verify that all of docker login's options are as expected.
      self.assertCountEqual(docker_login_options, _EXPECTED_DOCKER_OPTIONS)

      self.logins.append(target_server)
      self.process_mock.communicate.return_value = ('Login Succeeded\n', '')

      # Make sure that the mock's return_value is returned.
      return mock.DEFAULT

    return MultiLoginCommandVerifier

  def testAuthorizeOnly(self):
    docker.WriteDockerAuthConfig({})

    self.Run('docker --authorize-only')

    self.AssertErrContains(constants.DEFAULT_REGISTRY)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(('https://' + registry, {
            'email': _EMAIL,
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }) for registry in constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE))

  def testAuthorizeOnlyWithNewFile(self):
    self.TouchNewDockerConfig()
    docker.WriteDockerAuthConfig({})

    self.Run('docker --authorize-only')

    self.AssertErrContains(constants.DEFAULT_REGISTRY)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(('https://' + registry, {
            'email': _EMAIL,
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }) for registry in constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE))

  def testAuthorizeOnlyWithCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    self.get_process_mock.side_effect = self.RecordRegistriesForLogin()

    self.Run('docker --authorize-only')

    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    # 1x'docker login' per registry
    self.assertEqual(self.get_process_mock.call_count,
                     len(constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE))
    for registry in constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE:
      self.AssertErrContains(registry)
      self.assertIn('https://' + registry, self.logins)

  def testAuthorizeOnlyAllowDefaultRegistryWithCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    registry = constants.DEFAULT_REGISTRY
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.get_process_mock.assert_called_once()

  def testAuthorizeOnlyAllowDefaultRegistryWithPortAndCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    registry = constants.DEFAULT_REGISTRY + ':12345'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.get_process_mock.assert_called_once()

  def testAuthorizeOnlyDefaultRegistryWithPathAndCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    registry = constants.DEFAULT_REGISTRY + '/somepath'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.get_process_mock.assert_called_once()

  def testAuthorizeOnlyDefaultRegistryWithSchemeAndCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    registry = 'test://' + constants.DEFAULT_REGISTRY
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry=registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.get_process_mock.assert_called_once()

  def testAuthorizeOnlyAllowRegionalRegistriesWithCredStore(self):
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    registry = constants.REGIONAL_GCR_REGISTRIES[0]
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.get_process_mock.assert_called_once()

  def testAuthorizeOnlyDockerNotInstalled(self):
    # This tests support for gcloud app deploy's current requirement for
    # docker-binaryless interaction with a remote docker daemon.
    self.get_process_mock.side_effect = exceptions.Error(
        'Docker is not installed.')

    self.Run('docker --authorize-only')

    self.AssertErrContains(constants.DEFAULT_REGISTRY)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(('https://' + registry, {
            'email': _EMAIL,
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }) for registry in constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE))

  def testSimpleDockerCommand(self):
    self.execute_mock.side_effect = self.AssertCommand(['ps', '-a'])

    self.Run('docker -- ps -a')

    self.assertTrue(self.execute_mock.called)

  def testSimpleDockerCommandWithHost(self):
    self.execute_mock.side_effect = self.AssertCommand(
        ['-H', 'tcp://1.2.3.4:9876', 'ps', '-a'])

    self.Run('docker --docker-host=tcp://1.2.3.4:9876 -- ps -a')

    self.assertTrue(self.execute_mock.called)

  def testIsExpectedErrorLine(self):
    self.assertFalse(docker._IsExpectedErrorLine('Unexpected!'))
    self.assertFalse(docker._IsExpectedErrorLine('Also unexpected!!'))

    # Some observed error lines that are non-fatal.
    self.assertTrue(
        docker._IsExpectedErrorLine(
            'WARNING! Using --password via the CLI is insecure. Use '
            '--password-stdin.'
        ))
    self.assertTrue(
        docker._IsExpectedErrorLine(
            'Flag --email has been deprecated, will be removed in 1.13.'))
    self.assertTrue(
        docker._IsExpectedErrorLine(
            'Warning: \'--email\' is deprecated, it will be removed soon. '
            'See usage.'
        ))

  def testAuthorizeOnlyWithCredHelperSurfacesUnexpectedOutput(self):
    registry = constants.DEFAULT_REGISTRY
    self.WriteNewDockerConfig({_CREDENTIAL_STORE_KEY: 'helper'})
    self.get_process_mock.side_effect = self.DockerLoginWithOutput(
        'https://' + registry, 'Login Succeeded\n'
        'Unexpected!\n',
        'Warning: \'--email\' is deprecated, it will be removed soon. See '
        'usage.\n'
        'Flag --email has been deprecated, will be removed in 1.13.\n'
        'Also unexpected!\n'
        'WARNING! Using --password via the CLI is insecure. '
        'Use --password-stdin.\n')
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    # 'docker login' per registry
    self.get_process_mock.assert_called_once()

    # Make sure we're only surfacing unexpected output.
    self.AssertOutputNotContains('Login Succeeded')
    self.AssertOutputContains('Unexpected!')
    self.AssertErrNotContains(
        'Warning: \'--email\' is deprecated, it will be removed soon. '
        'See usage.')
    self.AssertErrNotContains(
        'Flag --email has been deprecated, will be removed in 1.13.')
    self.AssertErrContains('Also unexpected!')
    self.AssertErrNotContains(
        'WARNING! Using --password via the CLI is insecure. '
        'Use --password-stdin.')

  # HAPPY CASE AUTHORIZATION!
  # These are very similar to the above, but run with the precondition that a
  # dockerconfig exists that does not contain a credential helper.

  def testAuthorizeOnlyAllowDefaultRegistry(self):
    # {"auths":{}}
    docker.WriteDockerAuthConfig({})

    registry = constants.DEFAULT_REGISTRY
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig({
        'https://' + registry: {
            'email': 'not@val.id',
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }
    })

  def testAuthorizeOnlyAllowDefaultRegistryWithPort(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = constants.DEFAULT_REGISTRY + ':12345'
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(list(initial_entry.items()) + list({
            'https://' + registry: {
                'email': _EMAIL,
                'auth': base64.b64encode(
                    (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
            }
        }.items())))

  def testAuthorizeOnlyDefaultRegistryWithPath(self):
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = constants.DEFAULT_REGISTRY + '/somepath'
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(list(initial_entry.items()) + list({
            'https://' + registry: {
                'email': _EMAIL,
                'auth': base64.b64encode(
                    (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
            }
        }.items())))

  def testAuthorizeOnlyDefaultRegistryWithScheme(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'test://' + constants.DEFAULT_REGISTRY
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(list(initial_entry.items()) + list({
            registry: {
                'email': _EMAIL,
                'auth': base64.b64encode(
                    (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
            }
        }.items())))

  def testAuthorizeOnlyAllowRegionalRegistries(self):
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = constants.REGIONAL_GCR_REGISTRIES[0]
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)
    self.CheckDockerConfig(
        dict(list(initial_entry.items()) + list({
            'https://' + registry: {
                'email': _EMAIL,
                'auth': base64.b64encode(
                    (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
            }
        }.items())))

  def testAuthorizeOnlyStaleEntry(self):
    initial_entry = {
        constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    self.Run('docker --authorize-only')

    self.AssertErrContains(constants.DEFAULT_REGISTRY)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

    # Make sure that the stale, schemeless entry has been removed and that
    # we are left with the default https-prefixed entries.
    self.CheckDockerConfig(
        dict(('https://' + registry, {
            'email': _EMAIL,
            'auth': base64.b64encode(
                (_ACCESS_TOKEN_USERNAME + ':' + _TOKEN).encode()).decode()
        }) for registry in constants.DEFAULT_REGISTRIES_TO_AUTHENTICATE))

  # Non-Default authorization tests.
  # These logins should always leverage 'docker login' so that we can authorize
  # arbitrary endpoints but have the ability to reject truly unsupported
  # auth attempts before a real request is made.

  def testAuthorizeOnlyCustomServer(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'foo.bar.google.com:12345'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

  def testAuthorizeOnlyLocalhost(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'localhost'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='http://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

  def testAuthorizeOnlyLocalhostWithPort(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'localhost:5000'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='http://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

  def testAuthorizeOnlyCustomServerNotGoogleWithPort(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'foo.bar.notgoogle.com:12345'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry='https://' + registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

  def testAuthorizeOnlyCustomServerWithScheme(self):
    self.TouchNewDockerConfig()
    initial_entry = {
        'https://' + constants.DEFAULT_REGISTRY: {
            'email': _EMAIL,
            'auth': base64.b64encode(b'another-user:another-token').decode()
        }
    }
    docker.WriteDockerAuthConfig(initial_entry)

    registry = 'https://foo.bar.google.com'
    self.get_process_mock.side_effect = self.AssertRegistryLogin(
        registry=registry)
    self.Run('docker --server {registry} '
             '--authorize-only'.format(registry=registry))

    self.AssertErrContains('non-default')
    self.AssertErrContains(registry)
    # Check that we Refresh explicitly regardless of Load refreshing
    self.assertTrue(self.refreshed)

  def testAccountFlagWarning(self):
    self.TouchNewDockerConfig()
    try:
      self.Run('docker --account=fake_account')
    except calliope_exceptions.ExitCodeNoError:
      # Excepting the failed docker command since we only
      # test to verify account warnings.
      pass
    self.AssertErrContains(
        'Docker uses the account from the gcloud config.'
        'To set the account in the gcloud config, run `gcloud config set '
        'account <account_name>`')

  def testNoAccountFlagNoWarning(self):
    self.TouchNewDockerConfig()
    try:
      self.Run('docker')
    except calliope_exceptions.ExitCodeNoError:
      # Excepting the failed docker command since we only
      # test to verify account warnings.
      pass
    self.AssertErrNotContains(
        'Docker uses the account from the gcloud config.'
        'To set the account in the gcloud config, run `gcloud config set '
        'account <account_name>`')


if __name__ == '__main__':
  test_case.main()
