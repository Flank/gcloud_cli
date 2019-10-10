# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for `gcloud app instances scp`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.app import ssh_base


class InstancesSCPTest(ssh_base.InstancesSSHTestBase):
  """Tests `gcloud app instances scp` command invocations."""

  def SetUp(self):
    self.remote_instance = ssh.Remote('i2')
    self.remote_file_1 = ssh.FileReference('rem_1', remote=self.remote)
    self.remote_file_2 = ssh.FileReference('rem_2', remote=self.remote)
    self.other_remote_file = ssh.FileReference('rem_3', remote=ssh.Remote('i5'))
    self.local_file_1 = ssh.FileReference('local_1')
    self.local_file_2 = ssh.FileReference('local_2')

  def _RunScp(self, args):
    """Automatically pre-populates the first part of the command."""
    self.Run('app instances scp --service default --version v1 ' + args)

  def testSingleRemoteToLocal(self):
    """Simple case with remote to local."""
    self._RunScp('i2:rem_1 local_1')
    self.require_ssh.assert_called_once()
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file_1],
        self.local_file_1,
        identity_file=self.key_file,
        recursive=False,
        compress=False,
        options=self.options)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), self.ssh_env)

  def testMultiRemoteToLocal(self):
    """Multiple remote files (same instance) to local."""
    self._RunScp('i2:rem_1 i2:rem_2 local_1')
    self.require_ssh.assert_called_once()
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file_1, self.remote_file_2],
        self.local_file_1,
        identity_file=self.key_file,
        recursive=False,
        compress=False,
        options=self.options)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), self.ssh_env)

  def testMultiRemoteToLocalPutty(self):
    """Multiple remote files (same instance) fails on putty."""
    self.ssh_env.suite = ssh.Suite.PUTTY
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        r'Multiple remote sources not supported by PuTTY.'):
      self._RunScp('i2:rem_1 i2:rem_2 local_1')
    self.require_ssh.assert_called_once()

  def testMultiInstanceRemoteToLocal(self):
    """Multiple remote files (different instances) to local."""
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        r'All sources must refer to the same remote when destination is local'):
      self._RunScp('i1:rem_1 i2:rem_2 local_1')
    self.require_ssh.assert_called_once()

  def testSingleLocalToRemote(self):
    """Simple case with remote to local."""
    self._RunScp('local_1 i2:rem_1')
    self.require_ssh.assert_called_once()
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.local_file_1],
        self.remote_file_1,
        identity_file=self.key_file,
        recursive=False,
        compress=False,
        options=self.options)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), self.ssh_env)

  def testMultiLocalToRemote(self):
    """Simple case with remote to local."""
    self._RunScp('local_1 local_2 i2:rem_1')
    self.require_ssh.assert_called_once()
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.local_file_1, self.local_file_2],
        self.remote_file_1,
        identity_file=self.key_file,
        recursive=False,
        compress=False,
        options=self.options)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), self.ssh_env)

  def testLocalToLocal(self):
    """Fail when local to local."""
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        r'Source\(s\) must be remote when destination is local.'):
      self._RunScp('local_1 local_2')
    self.require_ssh.assert_called_once()

  def testRemoteToRemote(self):
    """Fail when remote to remote."""
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        r'All sources must be local files when destination is remote.'):
      self._RunScp('i2:f1 i2:f2')
    self.require_ssh.assert_called_once()

  def testFlags(self):
    """Remote to local, but with all flags here."""
    self._RunScp('--recurse --compress i2:rem_1 local_1')
    self.require_ssh.assert_called_once()
    self.ensure_keys_exist.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), overwrite=False)
    self._AssertPopulateCalled()

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file_1],
        self.local_file_1,
        identity_file=self.key_file,
        recursive=True,
        compress=True,
        options=self.options)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), self.ssh_env)

  def testPopulationError(self):
    """Tests that an error during population is surfaced to the command."""

    class MyException(Exception):
      pass

    self.populate_public_key.side_effect = MyException()
    with self.assertRaises(MyException):
      self._RunScp('i2:rem_1 local_1')
    self.require_ssh.assert_called_once()

if __name__ == '__main__':
  test_case.main()
