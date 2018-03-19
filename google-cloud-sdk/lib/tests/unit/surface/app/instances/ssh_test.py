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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import cli_test_base
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.app import ssh_base


class InstancesSSHTest(ssh_base.InstancesSSHTestBase):

  def testSSH(self):
    """Base case of unlocked instance."""
    self.Run('app instances ssh --service default --version v1 i2')
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=None,
        options=self.options,
        remote_command=None)

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)

  def testSSHShortFlagsInBeta(self):
    """Test that short flags work in the beta version."""
    self.Run('app instances ssh -s default -v v1 i2',
             track=calliope_base.ReleaseTrack.BETA)
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=None,
        options=self.options,
        remote_command=None)

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)
    self.AssertErrContains('the short flags `-s` and `-v` are deprecated')

  def testSSHShortFlagsInGA(self):
    """Test that short flags doesn't work in GA."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'unrecognized arguments:\n  -s\n  -v\n  v1\n  i2'):
      self.Run('app instances ssh -s default -v v1 i2')

  def testSSHWithContainer(self):
    """Go straight to the app container."""
    self.Run('app instances ssh --service default --version v1 i2 --container '
             'gaeapp')
    self._AssertPopulateCalled()

    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=True,
        options=self.options,
        remote_command='sudo docker exec -it gaeapp /bin/sh'.split())

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)

  def testSSHWithCommand(self):
    """Execute a remote command."""
    self.Run('app instances ssh --service default --version v1 i2 -- echo hi')
    self._AssertPopulateCalled()

    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=None,
        options=self.options,
        remote_command='echo hi'.split())

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)

  def testSSHWithContainerAndCommand(self):
    """Go straight to the app container and run a command."""
    self.Run(
        'app instances ssh --service default --version v1 i2 --container '
        'gaeapp -- echo hi')
    self._AssertPopulateCalled()

    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=None,
        options=self.options,
        remote_command='sudo docker exec -i gaeapp echo hi'.split())

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)

  def testPopulationError(self):
    """Tests that an error during population is surfaced to the command."""

    class MyException(Exception):
      pass

    self.populate_public_key.side_effect = MyException()
    with self.assertRaises(MyException):
      self.Run('app instances ssh --service default --version v1 i2')

  def testWithURI(self):
    """SSH using URI instead of specifying service and version."""
    self.Run('app instances ssh https://appengine.googleapis.com/v1/apps/'
             'fakeproject/services/default/versions/v1/instances/i2')
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.remote,
        identity_file=self.key_file,
        tty=None,
        options=self.options,
        remote_command=None)

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.ssh_env)


if __name__ == '__main__':
  test_case.main()
