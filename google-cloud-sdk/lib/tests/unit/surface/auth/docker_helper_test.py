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

import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.docker import credential_utils
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class DockerHelperTest(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):

  def SetUp(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.access_token = self.FakeAuthAccessToken()
    self.StartObjectPatch(c_store, 'Refresh', side_effect=FakeRefresh)

  def testGet(self):
    self.WriteInput('gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(
        data,
        {
            'Secret': self.FakeAuthAccessToken(),
            'Username': 'oauth2accesstoken'
        })

  def testGet_WithScheme(self):
    self.WriteInput('https://gcr.io\n')
    self.Run('auth docker-helper get')
    data = json.loads(self.GetOutput())
    self.assertEqual(
        data,
        {
            'Secret': self.FakeAuthAccessToken(),
            'Username': 'oauth2accesstoken'
        })

  def testGet_AllSupported(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': 'oauth2accesstoken'
      })
      self.ClearOutput()
      self.ClearErr()

  def testGet_AllSupported_WithScheme(self):
    for supported_registry in credential_utils.SupportedRegistries():
      self.WriteInput('https://{}\n'.format(supported_registry))
      self.Run('auth docker-helper get')
      data = json.loads(self.GetOutput())
      self.assertEqual(data, {
          'Secret': self.FakeAuthAccessToken(),
          'Username': 'oauth2accesstoken'
      })
      self.ClearOutput()
      self.ClearErr()

  def testList(self):
    self.Run('auth docker-helper list')

    for supported_registry in credential_utils.DefaultAuthenticatedRegistries():
      self.AssertOutputContains(
          '"https://{registry}": "oauth2accesstoken"'.format(
              registry=supported_registry))

  def testStore(self):
    self.Run('auth docker-helper store')
    self.AssertOutputEquals('')

  def testUnknownRepo(self):
    self.WriteInput('foo.io\n')
    with self.AssertRaisesExceptionMatches(
        exceptions.Error,
        'Repository url [foo.io] is not supported'):
      self.Run('auth docker-helper get')

  def testNoCreds(self):
    self.FakeAuthSetCredentialsPresent(False)
    self.WriteInput('gcr.io\n')
    with self.assertRaises(c_store.NoCredentialsForAccountException):
      self.Run('auth docker-helper get')
    self.AssertErrContains('ERROR: ')


if __name__ == '__main__':
  test_case.main()
