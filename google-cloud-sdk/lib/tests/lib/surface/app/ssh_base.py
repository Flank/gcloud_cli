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

"""Base class for tests of SSH or SCP in gcloud app."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.command_lib.app import ssh_common
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import mock_matchers
from tests.lib.surface.app import instances_base


class InstancesSSHTestBase(instances_base.InstancesTestBase):
  """Base class for tests using SSH or SCP."""

  def SetUp(self):
    self.require_ssh = self.StartObjectPatch(ssh.Environment, 'RequireSSH',
                                             autospec=True)
    self.public_key = ssh.Keys.PublicKey('ssh-rsa', 'DATA', comment='comment')
    self.StartObjectPatch(ssh.Keys, 'GetPublicKey', autospec=True,
                          return_value=self.public_key)
    self.ssh_env = self._FakeSSHEnvironment()
    self.env_current = self.StartObjectPatch(ssh.Environment, 'Current',
                                             return_value=self.ssh_env)
    self.ensure_keys_exist = self.StartObjectPatch(
        ssh.Keys, 'EnsureKeysExist', autospec=True)
    self.key_file = '/my/key'
    self.StartObjectPatch(ssh.Keys, 'key_file', self.key_file)

    self.remote = ssh.Remote('host', user='me')
    self.options = {'MyOption': 'Value'}
    connection_details = ssh_common.ConnectionDetails(
        self.remote, self.options)
    self.populate_public_key = self.StartObjectPatch(
        ssh_common, 'PopulatePublicKey', autospec=True,
        return_value=connection_details)

    self.ssh_init = self.StartObjectPatch(
        ssh.SSHCommand, '__init__', return_value=None, autospec=True)
    self.ssh_run = self.StartObjectPatch(
        ssh.SSHCommand, 'Run', autospec=True, return_value=0)

    self.scp_init = self.StartObjectPatch(
        ssh.SCPCommand, '__init__', return_value=None, autospec=True)
    self.scp_run = self.StartObjectPatch(ssh.SCPCommand, 'Run', autospec=True,
                                         return_value=0)

  def _FakeSSHEnvironment(self, use_putty=False):
    env = ssh.Environment(ssh.Suite.PUTTY if use_putty else ssh.Suite.OPENSSH,
                          '')
    env.ssh = 'ssh'
    env.ssh_term = 'ssh'
    env.scp = 'scp'
    env.keygen = 'ssh-keygen'
    return env

  def _AssertPopulateCalled(self):
    self.populate_public_key.assert_called_once_with(
        mock_matchers.TypeMatcher(appengine_api_client.AppengineApiClient),
        'default', 'v1', 'i2', self.public_key)
