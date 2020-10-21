# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for anthoscli_backend module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import getpass
import os
import re

from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock
from oauth2client import client
import requests


class AnthoscliBackendTest(sdk_test_base.WithOutputCapture,
                           test_case.WithInput):
  """Unit tests for anthoscli_backend module."""

  MY_VARS = {'%APPDATA%': 'APP_DATA_DIR'}

  def _MakeTempConfigFiles(self):
    """Copy fixture data files to temp directories so they can be modified."""
    fixture_file_dir = self.Resource(
        'tests', 'unit', 'command_lib', 'anthos', 'testdata')
    config_v2_path = self.Resource(fixture_file_dir,
                                   'auth-config-v2alpha1.yaml')
    config_v2_multi_path = self.Resource(fixture_file_dir,
                                         'auth-config-multiple-v2alpha1.yaml')
    config_v1_multi_path = self.Resource(fixture_file_dir,
                                         'auth-config-multiple-v1alpha1.yaml')
    config_v1_path = self.Resource(fixture_file_dir,
                                   'auth-config-v1alpha1.yaml')
    config_v2_missing_providers = self.Resource(
        fixture_file_dir, 'auth-config-v2alpha1-missing-providers.yaml')
    config_v2_1p = self.Resource(fixture_file_dir,
                                 'auth-config-v2alpha1-1p.yaml')
    config_v2_1p_ldap = self.Resource(fixture_file_dir,
                                      'auth-config-v2alpha1-1p-ldap.yaml')
    self.v2_ex1_path = self.Touch(
        self.temp_path, 'config_v2_ex1.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_path)))
    self.v2_ex1_contents = files.ReadFileContents(self.v2_ex1_path)

    self.v2_ex2_multi_path = self.Touch(
        self.temp_path, 'config_v2_ex2.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_multi_path)))
    self.v2_ex2_multi_contents = files.ReadFileContents(self.v2_ex2_multi_path)

    self.v1_ex1_path = self.Touch(
        self.temp_path, 'config_v1_multi_path.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v1_multi_path)))
    self.v1_ex2_multi_path = self.Touch(
        self.temp_path, 'config_v1_multi_path.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v1_path)))
    self.v2_ex2_missing_providers = self.Touch(
        self.temp_path, 'config-v2alpha1-missing-providers.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_missing_providers)))
    self.v2_ex3_1p = self.Touch(
        self.temp_path, 'config-v2alpha1-1p.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_1p)))
    self.v2_ex4_1p_ldap = self.Touch(
        self.temp_path, 'config-v2alpha1-1p-ldap.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_1p_ldap)))

  def _MockExpandVar(self, path):
    regex = r'(\$VAR\d)|(%APPDATA%)'
    pattern = re.compile(regex)
    return pattern.sub(lambda m: self.MY_VARS.get(m.group(0)), path)

  def SetUp(self):
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    self.fake_cred = client.OAuth2Credentials(
        'access-token',
        'client_id',
        'client_secret',
        'fake-token',
        datetime.datetime(2017, 1, 8, 0, 0, 0),
        'token_uri',
        'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    self._MakeTempConfigFiles()

  # Helper function for mocking GET responses. Takes file path as an input and
  # returns the contents of that file as a response.
  def _FakeURLResponse(self, response_text, response_code):
    resp = mock.Mock(spec=requests.models.Response)
    resp.text = response_text
    resp.status_code = response_code
    return resp

  def testGetAuthTokens(self):
    self.mock_load = self.StartObjectPatch(c_store,
                                           'LoadFreshCredential',
                                           return_value=self.fake_cred)
    expected = ('{"auth_token": "access-token"}')
    actual = anthoscli_backend.GetAuthToken('fake-account', 'fake-operation')
    self.mock_load.assert_called_with('fake-account',
                                      allow_account_impersonation=False)
    self.assertEqual(expected, actual)

  def testGetAuthTokensWithError(self):
    self.mock_load = self.StartObjectPatch(
        c_store, 'LoadFreshCredential',
        side_effect=c_store.ReauthenticationException('Foo'))
    with self.assertRaisesRegex(anthoscli_backend.AnthosAuthException, 'Foo'):
      anthoscli_backend.GetAuthToken('fake-account', 'fake-operation')

  # Test GetFileOrURL with a file input for reading Login-Config.
  def testGetContentsFromSingleV2alpha1File(self):
    # Read from V2alpha1 File containing single ClientConfig object.
    login_config, contents, is_url = anthoscli_backend.GetFileOrURL(
        cluster_config=self.v2_ex1_path)
    self.assertEqual(login_config, self.v2_ex1_path)
    self.assertEqual(contents, self.v2_ex1_contents)
    self.assertEqual(is_url, False)

  # Test GetFileOrURL with a file input for reading multiple v2alpha1
  # Login-Config objects from the same file.
  def testGetContentsFromMultipleV2alpha1File(self):
    # Read from Multi V2 File
    login_config, contents, is_url = anthoscli_backend.GetFileOrURL(
        cluster_config=self.v2_ex2_multi_path)
    self.assertEqual(login_config, self.v2_ex2_multi_path)
    self.assertEqual(contents, self.v2_ex2_multi_contents)
    self.assertEqual(is_url, False)

  # Test GetFileOrURL with a URL input for reading Login-Config.
  def testGetContentsFromURL(self):
    # Mock the URL response.
    response_text = files.ReadFileContents(self.v2_ex2_multi_path)
    self.StartObjectPatch(requests,
                          'get',
                          return_value=self._FakeURLResponse(
                              response_text=response_text,
                              response_code=200))

    # Read from Multi V2 File
    sample_url = 'https://www.example.com/clientconfig'
    login_config, contents, is_url = anthoscli_backend.GetFileOrURL(
        cluster_config=sample_url)
    self.assertEqual(login_config, sample_url)
    self.assertEqual(contents, self.v2_ex2_multi_contents)
    self.assertEqual(is_url, True)

  # GetFileOrURL should throw exception when response doesn't return 200 for
  # reading Login-Config from URL.
  def testURLResponseException(self):
    # Mock the URL response.
    self.StartObjectPatch(requests,
                          'get',
                          return_value=self._FakeURLResponse(
                              response_text='error',
                              response_code=400))

    with self.assertRaises(anthoscli_backend.AnthosAuthException):
      sample_url = 'https://www.example.com/clientconfig'
      anthoscli_backend.GetFileOrURL(cluster_config=sample_url)

  ## Next set of tests contains verification of expected behavior when passing
  ## contents of login-config directly (as is done by URL) to prompting logic.

  # The GetPreferredAuthForCluster() function should succeed if is_url=True is
  # passed while passing the fetched login-config contents of the url.
  def testGetPreferredAuthNoPromptFromURL(self):
    config_contents = files.ReadFileContents(self.v2_ex1_path)

    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True)
    self.assertEqual(auth_method, 'oidc1')

  # The GetPreferredAuthForCluster() function should fail if is_url=True is
  # passed without also passing the fetched login-config contents of the url.
  def testGetPreferredAuthFromURLFails(self):
    with self.assertRaises(anthoscli_backend.AnthosAuthException):
      _, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
          cluster='testcluster',
          login_config='https://www.example.com',
          is_url=True)

  # No need to prompt. Should get preferred auth method from contents.
  def testURLContentsGetPreferredAuthForClusterNoPrompt(self):
    config_contents = files.ReadFileContents(self.v2_ex1_path)

    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True)
    self.assertEqual(auth_method, 'oidc1')

  # When the URL contents are passed with no preferred auth set, should prompt.
  def testURLContentsGetPreferredAuthForCluster(self):
    config_contents = files.ReadFileContents(self.v2_ex2_multi_path)

    self.WriteInput('1')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster-3',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True)
    self.assertEqual(auth_method, 'basic')
    self.AssertErrNotContains(
        'This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  # When --update is forced, should prompt and not print overwrite warning.
  def testURLContentsGetPreferredAuthForClusterForceUpdate(self):
    config_contents = files.ReadFileContents(self.v2_ex1_path)

    self.WriteInput('3')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True,
        force_update=True)
    self.assertEqual(auth_method, 'oidc2')
    self.AssertErrNotContains(
        'This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  # LDAP prompting works with URL contents passed in.
  def testURLContentsGetPreferredAuthForClusterWithLdap(self):
    config_contents = files.ReadFileContents(self.v2_ex1_path)

    self.StartObjectPatch(getpass, 'getpass').return_value = 'password'
    self.WriteInput('5')
    self.WriteInput('user')
    auth_method, username, passwd = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True,
        force_update=True)
    self.assertEqual(auth_method, 'ldap2')
    self.assertEqual(username, 'dXNlcg==')
    self.assertEqual(passwd, 'cGFzc3dvcmQ=')
    self.AssertErrNotContains(
        'This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  # When only one option in URL contents, still works.
  def testURLContentsGetPreferredAuthForClusterOneOption(self):
    config_contents = files.ReadFileContents(self.v2_ex3_1p)

    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True,
        force_update=True)
    self.assertEqual(auth_method, 'oidc1')
    self.AssertErrContains('Setting Preferred Authentication option to')
    self.AssertErrNotContains('PROMPT_CHOICE')

  # Prompting works for single option LDAP from URL.
  def testURLContentsGetPreferredAuthForClusterOneOptionLDAP(self):
    config_contents = files.ReadFileContents(self.v2_ex4_1p_ldap)

    self.StartObjectPatch(getpass, 'getpass').return_value = 'password'
    self.WriteInput('user')
    auth_method, username, passwd = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True,
        force_update=True)
    self.assertEqual(auth_method, 'ldap2')
    self.assertEqual(username, 'dXNlcg==')
    self.assertEqual(passwd, 'cGFzc3dvcmQ=')
    self.AssertErrContains('Setting Preferred Authentication option to')
    self.AssertErrNotContains('PROMPT_CHOICE')

  # If URL contents passed, handles v1alpha1 ClientConfig.
  def testURLContentsGetPreferredAuthForClusterOldVersion(self):
    config_contents = files.ReadFileContents(self.v1_ex1_path)

    self.assertIsNone(anthoscli_backend.GetPreferredAuthForCluster(
        cluster='mycluster',
        login_config='https://www.example.com',
        config_contents=config_contents,
        is_url=True)[0])

  # If URL contents passed, fails when invalid cluster is selected
  def testURLContentsGetPreferredAuthForClusterBadCluster(self):
    config_contents = files.ReadFileContents(self.v2_ex1_path)

    with self.assertRaises(anthoscli_backend.AnthosAuthException):
      anthoscli_backend.GetPreferredAuthForCluster(
          cluster='non-cluster',
          login_config='https://www.example.com',
          config_contents=config_contents,
          is_url=True)

  # If URL contents passed, fails when there are no providers.
  def testURLContentsGetPreferredAuthForClusterMissingProviders(self):
    config_contents = files.ReadFileContents(self.v2_ex2_missing_providers)

    with self.assertRaisesRegexp(anthoscli_backend.AnthosAuthException,
                                 r'No Authentication Providers found'):
      anthoscli_backend.GetPreferredAuthForCluster(
          cluster='test-cluster',
          login_config='https://www.example.com',
          config_contents=config_contents,
          is_url=True)

  ## The following tests are to read from file rather than from passed contents.

  def testGetPreferredAuthForClusterNoPrompt(self):
    # Make a Multi V2 File
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster', login_config=self.v2_ex1_path)
    self.assertEqual(auth_method, 'oidc1')

  def testGetPreferredAuthForCluster(self):
    # Make a Multi V2 File
    self.WriteInput('1')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster-3', login_config=self.v2_ex2_multi_path)
    self.assertEqual(auth_method, 'basic')
    self.AssertFileContains('preferredAuthentication: basic',
                            self.v2_ex2_multi_path)
    self.AssertErrContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterForceUpdate(self):
    self.WriteInput('3')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster', login_config=self.v2_ex1_path, force_update=True)
    self.assertEqual(auth_method, 'oidc2')
    self.AssertFileContains('preferredAuthentication: oidc2',
                            self.v2_ex1_path)
    self.AssertErrContains('This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterWithLdap(self):
    self.StartObjectPatch(getpass, 'getpass').return_value = 'password'
    self.WriteInput('5')
    self.WriteInput('user')
    auth_method, username, passwd = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster', login_config=self.v2_ex1_path, force_update=True)
    self.assertEqual(auth_method, 'ldap2')
    self.assertEqual(username, 'dXNlcg==')
    self.assertEqual(passwd, 'cGFzc3dvcmQ=')
    self.AssertFileContains('preferredAuthentication: ldap2',
                            self.v2_ex1_path)
    self.AssertErrContains('This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterOneOption(self):
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster', login_config=self.v2_ex3_1p, force_update=True)
    self.assertEqual(auth_method, 'oidc1')
    self.AssertFileContains('preferredAuthentication: oidc1',
                            self.v2_ex3_1p)
    self.AssertErrContains('Setting Preferred Authentication option to')
    self.AssertErrNotContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterOneOptionLDAP(self):
    self.StartObjectPatch(getpass, 'getpass').return_value = 'password'
    self.WriteInput('user')
    auth_method, username, passwd = anthoscli_backend.GetPreferredAuthForCluster(
        cluster='testcluster', login_config=self.v2_ex4_1p_ldap,
        force_update=True)
    self.assertEqual(auth_method, 'ldap2')
    self.assertEqual(username, 'dXNlcg==')
    self.assertEqual(passwd, 'cGFzc3dvcmQ=')
    self.AssertFileContains('preferredAuthentication: ldap2',
                            self.v2_ex4_1p_ldap)
    self.AssertErrContains('Setting Preferred Authentication option to')
    self.AssertErrNotContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterOldVersion(self):
    self.assertIsNone(anthoscli_backend.GetPreferredAuthForCluster(
        cluster='mycluster', login_config=self.v1_ex1_path)[0])

  def testGetPreferredAuthForClusterBadConfigFile(self):
    with self.assertRaises(file_parsers.YamlConfigFileError):
      anthoscli_backend.GetPreferredAuthForCluster(cluster='mycluster',
                                                   login_config='BAD_PATH')

  def testGetPreferredAuthForClusterBadCluster(self):
    with self.assertRaises(anthoscli_backend.AnthosAuthException):
      anthoscli_backend.GetPreferredAuthForCluster(
          cluster='non-cluster',
          login_config=self.v2_ex1_path)

  def testGetPreferredAuthForClusterMissingClusterOrConfig(self):
    self.assertIsNone(
        anthoscli_backend.GetPreferredAuthForCluster(
            cluster=None,
            login_config=self.v2_ex1_path)[0])
    self.assertIsNone(
        anthoscli_backend.GetPreferredAuthForCluster(
            cluster='mycluster',
            login_config=None)[0])

  def testGetPreferredAuthForClusterMissingProviders(self):
    with self.assertRaisesRegexp(anthoscli_backend.AnthosAuthException,
                                 r'No Authentication Providers found'):
      anthoscli_backend.GetPreferredAuthForCluster(
          cluster='test-cluster',
          login_config=self.v2_ex2_missing_providers)

  @test_case.Filters.DoNotRunOnWindows
  def testGetDefaultConfigPath(self):
    self.mock_bin_check = self.StartObjectPatch(
        bin_ops,
        'CheckForInstalledBinary',
        return_value='/usr/bin/kubectl-anthos')
    self.mock_expandvars.side_effect = self._MockExpandVar
    expected = {
        'LINUX':
            os.path.join(self.home_path, '.config/google/anthos/'
                         'kubectl-anthos-config.yaml'),
        'MACOSX':
            os.path.join(
                self.home_path, 'Library/Preferences/google/anthos/'
                'kubectl-anthos-config.yaml'),
    }
    command_executor = anthoscli_backend.AnthosAuthWrapper()
    for os_id in anthoscli_backend.DEFAULT_LOGIN_CONFIG_PATH:
      if os_id == platforms.OperatingSystem.WINDOWS.id:
        continue
      self.StartObjectPatch(
          platforms.OperatingSystem,
          'Current',
          return_value=platforms.OperatingSystem.FromId(os_id))
      self.assertEqual(expected[os_id], command_executor.default_config_path)

  @test_case.Filters.RunOnlyOnWindows
  def testGetDefaultConfigPathWindows(self):
    self.mock_bin_check = self.StartObjectPatch(
        bin_ops,
        'CheckForInstalledBinary',
        return_value='/usr/bin/kubectl-anthos')
    self.StartEnvPatch({'APPDATA': 'APP_DATA_DIR'})
    self.mock_expandvars.side_effect = self._MockExpandVar
    expected = {
        'WINDOWS': os.path.join('APP_DATA_DIR',
                                'google', 'anthos',
                                'kubectl-anthos-config.yaml')
    }
    command_executor = anthoscli_backend.AnthosAuthWrapper()
    self.StartObjectPatch(
        platforms.OperatingSystem,
        'Current',
        return_value=platforms.OperatingSystem.WINDOWS)
    self.assertEqual(expected[platforms.OperatingSystem.WINDOWS.id],
                     command_executor.default_config_path)


if __name__ == '__main__':
  test_case.main()
