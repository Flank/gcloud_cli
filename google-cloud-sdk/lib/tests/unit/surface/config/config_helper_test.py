# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock

CONFIG_HELPER_CMD = 'config config-helper'


class ConfigHelperTest(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    self.refresh_mock = self.StartObjectPatch(store, 'Refresh')
    properties.VALUES.core.project.Set(self.Project())
    properties.VALUES.auth.disable_load_google_auth.Set(True)

  def GetFakeCred(self, token_expiry):
    fake_cred = self._FakeAuthCredential()

    if self.use_google_auth:
      fake_cred.expiry = token_expiry
    else:
      fake_cred.token_expiry = token_expiry

    return fake_cred

  def SetMockLoadCreds(self, expiry_time):
    fake_cred = self.GetFakeCred(expiry_time)
    self.StartObjectPatch(store, 'Load', return_value=fake_cred)

  def testConfigHelper(self):
    c = named_configs.ConfigurationStore.CreateConfig('foo')
    c.Activate()
    expiry_time = datetime.datetime(2000, 1, 2, 3, 4, 5, 678)
    self.SetMockLoadCreds(expiry_time)

    for force in ['', ' --force-auth-refresh']:
      result = self.Run(CONFIG_HELPER_CMD + force)
      self.assertEqual(result.credential.access_token,
                       self.FakeAuthAccessToken())
      self.assertEqual(result.credential.token_expiry, '2000-01-02T03:04:05Z')
      self.assertEqual(result.configuration.active_configuration, 'foo')
      self.assertEqual(result.configuration.properties['core']['project'],
                       self.Project())
      self.assertEqual(result.sentinels.config_sentinel,
                       config.Paths().config_sentinel_file)
      self.assertTrue(self.refresh_mock.called)

  def testRefresh(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=40)
    self.SetMockLoadCreds(expiry_time)
    expected_refresh_mock_called = iter([False, False, True])

    for min_expiry in [None, '30m', '60m']:
      cmd = CONFIG_HELPER_CMD
      if min_expiry:
        cmd += ' --min-expiry=%s' % min_expiry

      self.Run(cmd)
      self.assertEqual(self.refresh_mock.called,
                       next(expected_refresh_mock_called))

  def testMinExpiry(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=40)
    self.SetMockLoadCreds(expiry_time)
    refresh_mock = self.StartObjectPatch(store, 'RefreshIfExpireWithinWindow')

    cmd = CONFIG_HELPER_CMD + ' --min-expiry=30s'
    self.Run(cmd)
    refresh_mock.assert_called_with(mock.ANY, '30')

  def testNoCredentials(self):
    self.FakeAuthSetCredentialsPresent(False)
    with self.assertRaisesRegex(store.NoCredentialsForAccountException,
                                'does not have any valid credentials'):
      self.Run(CONFIG_HELPER_CMD)


class ConfigHelperTestGoogleAuth(ConfigHelperTest):

  def PreSetUp(self):
    self.use_google_auth = True

  def SetUp(self):
    properties.VALUES.auth.disable_load_google_auth.Set(False)


class ConfigHelperTestGCE(sdk_test_base.WithFakeComputeAuth,
                          cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    self.refresh_mock = self.StartObjectPatch(store, 'Refresh')
    properties.VALUES.auth.disable_load_google_auth.Set(True)

  def testConfigHelper(self):
    c = named_configs.ConfigurationStore.CreateConfig('foo')
    c.Activate()

    for force in ['', ' --force-auth-refresh']:
      result = self.Run(CONFIG_HELPER_CMD + force)
      self.assertEqual(result.credential.access_token,
                       self.FakeAuthAccessToken())
      # GCE creds don't have an expiry_time.
      self.assertEqual(result.credential.token_expiry, None)
      self.assertEqual(result.configuration.active_configuration, 'foo')
      self.assertEqual(result.configuration.properties['core']['project'],
                       self.Project())
      self.assertEqual(result.sentinels.config_sentinel,
                       config.Paths().config_sentinel_file)
      self.assertTrue(self.refresh_mock.called)

  def testNoCredentials(self):
    self.FakeAuthSetCredentialsPresent(False)
    with self.assertRaisesRegex(store.NoCredentialsForAccountException,
                                'does not have any valid credentials'):
      self.Run(CONFIG_HELPER_CMD)


class ConfigHelperTestGCEGoogleAuth(ConfigHelperTestGCE):

  def SetUp(self):
    properties.VALUES.auth.disable_load_google_auth.Set(False)


if __name__ == '__main__':
  cli_test_base.main()
