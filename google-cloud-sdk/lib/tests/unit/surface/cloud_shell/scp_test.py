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
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock


class ScpTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.scp_init = self.StartObjectPatch(
        ssh.SCPCommand, "__init__", return_value=None, autospec=True)
    self.scp_build = self.StartObjectPatch(
        ssh.SCPCommand, "Build", autospec=True, return_value="")
    self.scp_run = self.StartObjectPatch(
        ssh.SCPCommand, "Run", autospec=True, return_value=0)

  def testBetaUploadOneFile(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp localhost:foo cloudshell:bar")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[ssh.FileReference.FromPath("foo")],
        destination=ssh.FileReference.FromPath("my-user@my-host:bar"),
        recursive=False,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=None,
        options={"StrictHostKeyChecking": "no"})

  def testBetaDownloadOneFile(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp cloudshell:foo localhost:bar")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[ssh.FileReference.FromPath("my-user@my-host:foo")],
        destination=ssh.FileReference.FromPath("bar"),
        recursive=False,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=None,
        options={"StrictHostKeyChecking": "no"})

  def testBetaUploadManyFiles(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp localhost:foo localhost:bar cloudshell:baz")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[
            ssh.FileReference.FromPath("foo"),
            ssh.FileReference.FromPath("bar")
        ],
        destination=ssh.FileReference.FromPath("my-user@my-host:baz"),
        recursive=False,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=None,
        options={"StrictHostKeyChecking": "no"})

  def testBetaDownloadManyFiles(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp cloudshell:foo cloudshell:bar localhost:baz")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[
            ssh.FileReference.FromPath("my-user@my-host:foo"),
            ssh.FileReference.FromPath("my-user@my-host:bar")
        ],
        destination=ssh.FileReference.FromPath("baz"),
        recursive=False,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=None,
        options={"StrictHostKeyChecking": "no"})

  def testBetaDryRun(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp localhost:foo cloudshell:bar --dry-run")
    self.scp_run.assert_not_called()

  def testBetaRecurse(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp localhost:foo cloudshell:bar --recurse")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[ssh.FileReference.FromPath("foo")],
        destination=ssh.FileReference.FromPath("my-user@my-host:bar"),
        recursive=True,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=None,
        options={"StrictHostKeyChecking": "no"})

  def testBetaScpFlag(self):
    self.mockBetaConnection(user="my-user", host="my-host", port=123)
    self.Run("beta cloud-shell scp localhost:foo cloudshell:bar "
             "--scp-flag=-someFlag --scp-flag=anotherFlag")
    self.scp_init.assert_called_once_with(
        mock.ANY,
        sources=[ssh.FileReference.FromPath("foo")],
        destination=ssh.FileReference.FromPath("my-user@my-host:bar"),
        recursive=False,
        compress=False,
        port="123",
        identity_file=None,
        extra_flags=["-someFlag", "anotherFlag"],
        options={"StrictHostKeyChecking": "no"})

  def testBetaRequiresPrefixesForAllPaths(self):
    with self.assertRaises(Exception):
      self.Run("beta cloud-shell scp foo bar")

  def mockBetaConnection(self, user="some-user", host="some-host", port=6000):
    self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.PrepareV1Environment",
        return_value=util.ConnectionInfo(
            ssh_env=None, user=user, host=host, port=port, key=None))


if __name__ == "__main__":
  test_case.main()
