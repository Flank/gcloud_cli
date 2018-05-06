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

"""Tests for devshell credentials."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import os

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import encoding
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import devshell_test_base


class DevshellEnvironmentTests(sdk_test_base.SdkBase):

  def testThrowsNoDevshellServerInNoDevshellEnv(self):
    try:
      devshell.DevshellCredentials()
    except devshell.NoDevshellServer:
      pass

  def testIsDevshellEnvironment(self):
    self.StartEnvPatch({})
    self.assertTrue(devshell.IsDevshellEnvironment)
    encoding.SetEncodedValue(os.environ, devshell.DEVSHELL_ENV, str(1))
    self.assertTrue(devshell.IsDevshellEnvironment)
    del os.environ[devshell.DEVSHELL_ENV]


@test_case.Filters.RunOnlyOnLinux
@test_case.Filters.SkipInDebPackage('Socket conflict in docker container in '
                                    'test environment', 'b/37959415')
@test_case.Filters.SkipInRpmPackage('Socket conflict in docker container in '
                                    'test environment', 'b/37959415')
class ProxiedAuthTests(sdk_test_base.SdkBase):

  @sdk_test_base.Retry(
      why='The port used by the proxy may be in use.',
      max_retrials=3,
      sleep_ms=300)
  def _CreateAndStartDevshellProxy(self):
    self.devshell_proxy = devshell_test_base.AuthReferenceServer(self.GetPort())
    try:
      self.devshell_proxy.Start()
    except Exception as e:  # pylint: disable=bare-except
      # Clean up environment variables set by Start().
      self.devshell_proxy.Stop()
      raise e

  def SetUp(self):
    self._CreateAndStartDevshellProxy()
    self._devshell_provider = c_store.DevShellCredentialProvider()
    self._devshell_provider.Register()

  def TearDown(self):
    self.devshell_proxy.Stop()
    self._devshell_provider.UnRegister()

  def testRequestResponse(self):
    request = devshell.CredentialInfoRequest()
    response = devshell._SendRecv(request)
    self.assertEqual(
        response,
        devshell.CredentialInfoResponse(
            user_email='joe@example.com',
            project_id='fooproj',
            access_token='sometoken',
            expires_in=1800))

  def testProperties(self):
    self.assertEqual(
        properties.VALUES.core.account.Get(),
        'joe@example.com')
    self.assertEqual(
        properties.VALUES.core.project.Get(),
        'fooproj')

  # TODO(b/35925600): Add unit test to ensure creds refresh after expiry time
  # has passed.
  def testStore(self):
    creds = c_store.Load()
    self.assertEqual(type(creds), devshell.DevshellCredentials)
    self.assertEqual(creds.access_token, 'sometoken')
    self.assertGreater(creds.token_expiry, datetime.datetime.utcnow())
    self.assertLess(
        creds.token_expiry,
        datetime.datetime.utcnow() + datetime.timedelta(seconds=1800))

    accounts = c_store.AvailableAccounts()
    self.assertIn('joe@example.com', accounts)

  def testNoSerialize(self):
    creds = c_store.Load()
    # This should just do nothing. If the creds are actually serialized,
    # things blow up.
    c_store.Store(creds)


class EncodingTests(sdk_test_base.SdkBase):

  def doEncodeRecode(self, msg, encoded):
    pbl = devshell.MessageToPBLiteList(msg)
    self.assertEqual(pbl, encoded)
    recoded = devshell.PBLiteListToMessage(
        pbl, type(msg))
    self.assertEqual(msg, recoded)

  def testEncodeRequest(self):
    self.doEncodeRecode(devshell.CredentialInfoRequest(), [])

  def testEncodeResponse(self):
    self.doEncodeRecode(
        devshell.CredentialInfoResponse(
            user_email='joe@example.com'),
        ['joe@example.com', None, None, None])


if __name__ == '__main__':
  test_case.main()
