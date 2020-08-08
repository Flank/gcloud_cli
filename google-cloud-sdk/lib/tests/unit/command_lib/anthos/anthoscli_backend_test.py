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
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
from oauth2client import client


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
    self.v2_ex1_path = self.Touch(
        self.temp_path, 'config_v2_ex1.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_path)))
    self.v2_ex2_multi_path = self.Touch(
        self.temp_path, 'config_v2_ex2.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_multi_path)))
    self.v1_ex1_path = self.Touch(
        self.temp_path, 'config_v1_multi_path.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v1_multi_path)))
    self.v1_ex2_multi_path = self.Touch(
        self.temp_path, 'config_v1_multi_path.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v1_path)))
    self.v1_ex2_missing_providers = self.Touch(
        self.temp_path, 'config-v2alpha1-missing-providers.yaml',
        contents=yaml.dump_all(yaml.load_all_path(config_v2_missing_providers)))

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

  def testGetPreferredAuthForClusterNoPrompt(self):
    # Make a Multi V2 File
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        'testcluster', self.v2_ex1_path)
    self.assertEqual(auth_method, 'oidc1')

  def testGetPreferredAuthForCluster(self):
    # Make a Multi V2 File
    self.WriteInput('1')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        'testcluster-3', self.v2_ex2_multi_path)
    self.assertEqual(auth_method, 'basic')
    self.AssertFileContains('preferredAuthentication: basic',
                            self.v2_ex2_multi_path)
    self.AssertErrContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterForceUpdate(self):
    self.WriteInput('3')
    auth_method, _, _ = anthoscli_backend.GetPreferredAuthForCluster(
        'testcluster', self.v2_ex1_path, force_update=True)
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
        'testcluster', self.v2_ex1_path, force_update=True)
    self.assertEqual(auth_method, 'ldap2')
    self.assertEqual(username, 'dXNlcg==')
    self.assertEqual(passwd, 'cGFzc3dvcmQ=')
    self.AssertFileContains('preferredAuthentication: ldap2',
                            self.v2_ex1_path)
    self.AssertErrContains('This will overwrite current preferred auth method')
    self.AssertErrContains('PROMPT_CHOICE')

  def testGetPreferredAuthForClusterOldVersion(self):
    self.assertIsNone(anthoscli_backend.GetPreferredAuthForCluster(
        'mycluster', self.v1_ex1_path)[0])

  def testGetPreferredAuthForClusterBadConfigFile(self):
    with self.assertRaises(file_parsers.YamlConfigFileError):
      anthoscli_backend.GetPreferredAuthForCluster('mycluster', 'BAD_PATH')

  def testGetPreferredAuthForClusterBadCluster(self):
    with self.assertRaises(anthoscli_backend.AnthosAuthException):
      anthoscli_backend.GetPreferredAuthForCluster('non-cluster',
                                                   self.v2_ex1_path)

  def testGetPreferredAuthForClusterMissingClusterOrCOnfig(self):
    self.assertIsNone(
        anthoscli_backend.GetPreferredAuthForCluster(None,
                                                     self.v2_ex1_path)[0])
    self.assertIsNone(
        anthoscli_backend.GetPreferredAuthForCluster('mycluster', None)[0])

  def testGetPreferredAuthForClusterMissingProviders(self):
    with self.assertRaisesRegexp(anthoscli_backend.AnthosAuthException,
                                 r'No Authentication Providers found'):
      anthoscli_backend.GetPreferredAuthForCluster(
          'test-cluster', self.v1_ex2_missing_providers)

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
