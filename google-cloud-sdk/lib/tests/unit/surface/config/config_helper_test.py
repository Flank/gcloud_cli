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

import datetime

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ConfigHelperTest(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    self.refresh_mock = self.StartObjectPatch(store, 'Refresh')
    properties.VALUES.core.project.Set(self.Project())

  def FakeAuthExpiryTime(self):
    """Overrides the base testing class value for the expiry time."""
    return datetime.datetime(2000, 1, 2, 3, 4, 5, 678)

  def testConfigHelper(self):
    c = named_configs.ConfigurationStore.CreateConfig('foo')
    c.Activate()

    for force in ['', ' --force-auth-refresh']:
      result = self.Run('config config-helper' + force)
      self.assertEqual(result.credential.access_token,
                       self.FakeAuthAccessToken())
      self.assertEqual(result.credential.token_expiry, '2000-01-02T03:04:05Z')
      self.assertEqual(result.configuration.active_configuration, 'foo')
      self.assertEqual(result.configuration.properties['core']['project'],
                       self.Project())
      self.assertEqual(result.sentinels.config_sentinel,
                       config.Paths().config_sentinel_file)
      self.assertEqual(self.refresh_mock.called, bool(force))

  def testNoCredentials(self):
    self.FakeAuthSetCredentialsPresent(False)
    with self.assertRaisesRegexp(store.NoCredentialsForAccountException,
                                 'does not have any valid credentials'):
      self.Run('config config-helper')


class ConfigHelperTestGCE(sdk_test_base.WithFakeComputeAuth,
                          cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    self.refresh_mock = self.StartObjectPatch(store, 'Refresh')

  def testConfigHelper(self):
    c = named_configs.ConfigurationStore.CreateConfig('foo')
    c.Activate()

    for force in ['', ' --force-auth-refresh']:
      result = self.Run('config config-helper' + force)
      self.assertEqual(result.credential.access_token,
                       self.FakeAuthAccessToken())
      # GCE creds don't have an expiry_time.
      self.assertEqual(result.credential.token_expiry, None)
      self.assertEqual(result.configuration.active_configuration, 'foo')
      self.assertEqual(result.configuration.properties['core']['project'],
                       self.Project())
      self.assertEqual(result.sentinels.config_sentinel,
                       config.Paths().config_sentinel_file)
      self.assertEqual(self.refresh_mock.called, bool(force))

  def testNoCredentials(self):
    self.FakeAuthSetCredentialsPresent(False)
    with self.assertRaisesRegexp(store.NoCredentialsForAccountException,
                                 'does not have any valid credentials'):
      self.Run('config config-helper')


if __name__ == '__main__':
  cli_test_base.main()
