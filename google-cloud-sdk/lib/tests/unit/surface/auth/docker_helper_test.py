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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.docker import credential_utils
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from oauth2client import client
from google.oauth2 import credentials as google_auth_creds


class DockerHelperTestOauth2client(sdk_test_base.WithFakeAuth,
                                   cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)

    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.access_token = self.FakeAuthAccessToken()

    self.refresh_mock = self.StartObjectPatch(
        c_store, 'Refresh', side_effect=FakeRefresh)

  def GetFakeCred(self, token_expiry):
    return client.OAuth2Credentials(self.FakeAuthAccessToken(), None, None,
                                    None, token_expiry, None, None)

  def SetMockLoadCreds(self, expiry_time):
    fake_cred = self.GetFakeCred(expiry_time)
    self.StartObjectPatch(c_store, 'Load', return_value=fake_cred)

  def testGet(self):
    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testGet_WithScheme(self):
    self.WriteInput('https://gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testGet_AllSupported(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': '_dcgcloud_token'
      })
      self.refresh_mock.assert_not_called()
      self.ClearOutput()
      self.ClearErr()

  def testGet_AllSupported_WithScheme(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('https://{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': '_dcgcloud_token'
      })
      self.refresh_mock.assert_not_called()
      self.ClearOutput()
      self.ClearErr()

  def testRefresh_ExpiryTime30minRemaining(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_called_once()

  def testRefresh_ExpiryTimeExpired(self):
    expiry_time = datetime.datetime(2000, 1, 23, 4, 56, 7, 89)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_called_once()

  def testRefresh_FreshToken(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=56)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testList(self):
    self.Run('auth docker-helper list')

    for supported_registry in credential_utils.DefaultAuthenticatedRegistries():
      self.AssertOutputContains(
          '"https://{registry}": "_dcgcloud_token"'.format(
              registry=supported_registry))

  def testStore(self):
    self.Run('auth docker-helper store')
    self.AssertOutputEquals('')

  def testUnknownRepo(self):
    self.WriteInput('foo.io\n')
    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'Repository url [foo.io] is not supported'):
      self.Run('auth docker-helper get')

  def testNoCreds(self):
    self.FakeAuthSetCredentialsPresent(False)
    self.WriteInput('gcr.io\n')
    with self.assertRaises(c_store.NoCredentialsForAccountException):
      self.Run('auth docker-helper get')
    self.AssertErrContains('ERROR: ')


class DockerHelperTestGoogleAuth(sdk_test_base.WithFakeAuth,
                                 cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.use_google_auth = True

  def SetUp(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=False)

    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.token = self.FakeAuthAccessToken()

    self.refresh_mock = self.StartObjectPatch(
        c_store, 'Refresh', side_effect=FakeRefresh)

  def GetFakeCred(self, token_expiry):
    creds = google_auth_creds.Credentials(self.FakeAuthAccessToken())
    creds.expiry = token_expiry
    return creds

  def SetMockLoadCreds(self, expiry_time):
    fake_cred = self.GetFakeCred(expiry_time)
    self.StartObjectPatch(c_store, 'Load', return_value=fake_cred)

  def testGet(self):
    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testGet_WithScheme(self):
    self.WriteInput('https://gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testGet_AllSupported(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': '_dcgcloud_token'
      })
      self.refresh_mock.assert_not_called()
      self.ClearOutput()
      self.ClearErr()

  def testGet_AllSupported_WithScheme(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('https://{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': '_dcgcloud_token'
      })
      self.refresh_mock.assert_not_called()
      self.ClearOutput()
      self.ClearErr()

  def testRefresh_ExpiryTime30minRemaining(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_called_once()

  def testRefresh_ExpiryTimeExpired(self):
    expiry_time = datetime.datetime(2000, 1, 23, 4, 56, 7, 89)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_called_once()

  def testRefresh_FreshToken(self):
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=56)
    self.SetMockLoadCreds(expiry_time)

    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(data, {
        'Secret': self.FakeAuthAccessToken(),
        'Username': '_dcgcloud_token'
    })
    self.refresh_mock.assert_not_called()

  def testList(self):
    self.Run('auth docker-helper list')

    for supported_registry in credential_utils.DefaultAuthenticatedRegistries():
      self.AssertOutputContains(
          '"https://{registry}": "_dcgcloud_token"'.format(
              registry=supported_registry))

  def testStore(self):
    self.Run('auth docker-helper store')
    self.AssertOutputEquals('')

  def testUnknownRepo(self):
    self.WriteInput('foo.io\n')
    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'Repository url [foo.io] is not supported'):
      self.Run('auth docker-helper get')

  def testNoCreds(self):
    self.FakeAuthSetCredentialsPresent(False)
    self.WriteInput('gcr.io\n')
    with self.assertRaises(c_store.NoCredentialsForAccountException):
      self.Run('auth docker-helper get')
    self.AssertErrContains('ERROR: ')


if __name__ == '__main__':
  test_case.main()
