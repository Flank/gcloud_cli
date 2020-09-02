# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock
import six


class SshTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.mockConnection()
    self.ssh_init = self.StartObjectPatch(
        ssh.SSHCommand, "__init__", return_value=None, autospec=True)
    self.ssh_build = self.StartObjectPatch(
        ssh.SSHCommand, "Build", autospec=True, return_value=[])
    self.ssh_run = self.StartObjectPatch(
        ssh.SSHCommand, "Run", autospec=True, return_value=0)
    self.pipes_quote = self.StartObjectPatch(
        six.moves, "shlex_quote", side_effect=six.moves.shlex_quote)
    self.authorize = self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.AuthorizeEnvironment",
        return_value=None)
    self.authorize_v1 = self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.AuthorizeV1Environment",
        return_value=None)

  def testBetaNoArguments(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell ssh")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize_v1.assert_not_called()

  def testBetaNoProject(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    prop = properties.FromString("project")
    properties.PersistProperty(prop, None, scope=properties.Scope.USER)
    self.Run("beta cloud-shell ssh")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize_v1.assert_not_called()

  def testBetaCommand(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell ssh --command=ls")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "ls"],
        extra_flags=None,
        tty=False,
        options={"StrictHostKeyChecking": "no"})
    self.authorize_v1.assert_not_called()

  def testBetaDryRun(self):
    self.ssh_build.return_value = ["path to command", "arg'1"]

    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell ssh --dry-run")
    self.ssh_run.assert_not_called()
    self.assertEqual(
        len(self.ssh_build.return_value), self.pipes_quote.call_count)
    self.pipes_quote.assert_has_calls(
        [mock.call(arg) for arg in self.ssh_build.return_value])
    self.authorize_v1.assert_not_called()

  def testBetaSshFlag(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell ssh --ssh-flag=-someFlag --ssh-flag=anotherFlag")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=["-someFlag", "anotherFlag"],
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize_v1.assert_not_called()

  def testBetaAuthorizeSessionFlag(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell ssh --authorize-session")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize_v1.assert_called()

  def mockBetaConnection(self, user="some-user", host="some-host", port=6000):
    self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.PrepareV1Environment",
        return_value=util.ConnectionInfo(
            ssh_env=None, user=user, host=host, port=port, key=None))

  def testNoArguments(self):
    self.mockConnection(user="my-user", host="my-host", port=123)
    self.Run("alpha cloud-shell ssh")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize.assert_not_called()

  def testNoProject(self):
    self.mockConnection(user="my-user", host="my-host", port=123)
    prop = properties.FromString("project")
    properties.PersistProperty(prop, None, scope=properties.Scope.USER)
    self.Run("alpha cloud-shell ssh")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize.assert_not_called()

  def testCommand(self):
    self.mockConnection(user="my-user", host="my-host", port=123)
    self.Run("alpha cloud-shell ssh --command=ls")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "ls"],
        extra_flags=None,
        tty=False,
        options={"StrictHostKeyChecking": "no"})
    self.authorize.assert_not_called()

  def testDryRun(self):
    self.ssh_build.return_value = ["path to command", "arg'1"]

    self.mockConnection(user="my-user", host="my-host", port=123)
    self.Run("alpha cloud-shell ssh --dry-run")
    self.ssh_run.assert_not_called()
    self.assertEqual(
        len(self.ssh_build.return_value), self.pipes_quote.call_count)
    self.pipes_quote.assert_has_calls(
        [mock.call(arg) for arg in self.ssh_build.return_value])
    self.authorize.assert_not_called()

  def testSshFlag(self):
    self.mockConnection(user="my-user", host="my-host", port=123)
    self.Run(
        "alpha cloud-shell ssh --ssh-flag=-someFlag --ssh-flag=anotherFlag")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=["-someFlag", "anotherFlag"],
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize.assert_not_called()

  def testAuthorizeSessionFlag(self):
    self.mockConnection(user="my-user", host="my-host", port=123)
    self.Run("alpha cloud-shell ssh --authorize-session")
    self.ssh_init.assert_called_once_with(
        mock.ANY,
        remote=ssh.Remote(host="my-host", user="my-user"),
        port="123",
        identity_file=None,
        remote_command=["DEVSHELL_PROJECT_ID=fake-project", "bash -l"],
        extra_flags=None,
        tty=True,
        options={"StrictHostKeyChecking": "no"})
    self.authorize.assert_called()

  def mockConnection(self, user="some-user", host="some-host", port=6000):
    self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.PrepareEnvironment",
        return_value=util.ConnectionInfo(
            ssh_env=None, user=user, host=host, port=port, key=None))


if __name__ == "__main__":
  test_case.main()
