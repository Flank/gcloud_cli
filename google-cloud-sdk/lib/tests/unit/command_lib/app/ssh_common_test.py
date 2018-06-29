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

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.command_lib.app import exceptions as command_exceptions
from googlecloudsdk.command_lib.app import ssh_common
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import instances_base


class KeyPopulateTest(instances_base.InstancesTestBase):
  """Tests ssh_common.PopulatePublicKey."""

  def SetUp(self):
    self.api_client = appengine_api_client.AppengineApiClient.GetApiClient()
    self.user = 'me'
    self.public_key = ssh.Keys.PublicKey('ssh-rsa', 'DATA', comment='comment')
    self.key_field = '{user}:ssh-rsa DATA {user}'.format(user=self.user)
    self.StartObjectPatch(ssh, 'GetDefaultSshUsername', autospec=True,
                          return_value=self.user)
    self.StartObjectPatch(ssh.KnownHosts, 'DEFAULT_PATH', '/my/hosts')
    self.options = {
        'IdentitiesOnly': 'yes',
        'UserKnownHostsFile': '/my/hosts',
        'CheckHostIP': 'no',
        'HostKeyAlias': 'gae.fakeproject.i2'}
    self.connection_details = ssh_common.ConnectionDetails(
        ssh.Remote('127.0.0.1', user='me'), self.options)

  def _ExpectGetVersionCall(self, service, version, exception=None,
                            environment=env.FLEX):
    name = self._FormatVersion(service, version)
    response = self.messages.Version(name=name,
                                     createTime='2016-01-01T12:00:00.000Z',
                                     createdBy='user@gmail.com',
                                     id='version1',
                                     runtime='intercal')
    if environment is env.FLEX:
      response.env = 'flexible'
    elif environment is env.MANAGED_VMS:
      response.vm = True
    self.mocked_client.apps_services_versions.Get.Expect(
        request=self.messages.AppengineAppsServicesVersionsGetRequest(
            name=name,
            view=(self.messages.AppengineAppsServicesVersionsGetRequest
                  .ViewValueValuesEnum.FULL)),
        exception=exception,
        response=None if exception else response)

  def testPopulateKey(self):
    """Base case of unlocked instance."""
    self._ExpectGetVersionCall('default', 'v1')
    self._ExpectGetInstanceCall('default', 'v1', 'i2', debug_enabled=True)
    self._ExpectDebugInstanceCall('default', 'v1', 'i2', ssh_key=self.key_field)
    connection_details = ssh_common.PopulatePublicKey(
        self.api_client, 'default', 'v1', 'i2', self.public_key)
    self.assertEqual(connection_details, self.connection_details)

  def testPopulateKeyDebugOff(self):
    """Debug not enabled on the instance."""
    self._ExpectGetVersionCall('default', 'v1')
    self._ExpectGetInstanceCall('default', 'v1', 'i2', debug_enabled=False)
    self._ExpectDebugInstanceCall('default', 'v1', 'i2', ssh_key=self.key_field)
    self.WriteInput('y')
    connection_details = ssh_common.PopulatePublicKey(
        self.api_client, 'default', 'v1', 'i2', self.public_key)
    self.assertEqual(connection_details, self.connection_details)
    self.AssertErrContains(
        'This instance is serving live application traffic.')

  def testPopulateKeyDebugOffUnattended(self):
    """Test without input, make sure we fail."""
    self._ExpectGetVersionCall('default', 'v1')
    self._ExpectGetInstanceCall('default', 'v1', 'i2', debug_enabled=False)
    with self.assertRaises(console_io.UnattendedPromptError):
      ssh_common.PopulatePublicKey(self.api_client, 'default', 'v1', 'i2',
                                   self.public_key)

  def testPopulateKeyMissingVersion(self):
    """The version doesn't exist."""
    self._ExpectGetVersionCall(
        'default', 'v1', exception=http_error.MakeHttpError(404))
    with self.AssertRaisesExceptionMatches(
        command_exceptions.MissingVersionError,
        'Version [default/v1] does not exist.'):
      ssh_common.PopulatePublicKey(self.api_client, 'default', 'v1', 'i2',
                                   self.public_key)

  def testPopulateKeyMissingInstance(self):
    """The instance doesn't exist."""
    self._ExpectGetVersionCall('default', 'v1')

    req = self.messages.AppengineAppsServicesVersionsInstancesGetRequest(
        name=self._FormatInstance('default', 'v1', 'i2'))
    self.mocked_client.apps_services_versions_instances.Get.Expect(
        request=req,
        exception=http_error.MakeHttpError(404))

    with self.AssertRaisesExceptionRegexp(
        command_exceptions.MissingInstanceError,
        r'Instance \[.*i2\] does not exist.'):
      ssh_common.PopulatePublicKey(self.api_client, 'default', 'v1', 'i2',
                                   self.public_key)

  def testPopulateKeyManagedVMs(self):
    """Fail while trying Managed VMs instance."""
    self._ExpectGetVersionCall('default', 'v1',
                               environment=env.MANAGED_VMS)
    with self.AssertRaisesExceptionMatches(
        command_exceptions.InvalidInstanceTypeError,
        'Managed VMs instances do not support this operation'):
      ssh_common.PopulatePublicKey(self.api_client, 'default', 'v1', 'i2',
                                   self.public_key)

  def testPopulateKeyStandard(self):
    """Fail while trying standard instance."""
    self._ExpectGetVersionCall('default', 'v1',
                               environment=env.STANDARD)
    with self.AssertRaisesExceptionMatches(
        command_exceptions.InvalidInstanceTypeError,
        'Standard instances do not support this operation'):
      ssh_common.PopulatePublicKey(self.api_client, 'default', 'v1', 'i2',
                                   self.public_key)

if __name__ == '__main__':
  test_case.main()
