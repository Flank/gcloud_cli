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
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetMountCommandTest(cli_test_base.CliTestBase,
                          sdk_test_base.WithFakeAuth):

  @test_case.Filters.DoNotRunOnWindows
  def testNotWindows(self):
    self.mockConnection(
        user="my-user", host="my-host", port=123, key="/key/path")
    self.Run("alpha cloud-shell get-mount-command myMountDir")
    self.AssertOutputContains(
        "sshfs my-user@my-host: myMountDir -p 123 -oIdentityFile=/key/path "
        "-oStrictHostKeyChecking=no"
    )

  @test_case.Filters.RunOnlyOnWindows
  def testWindows(self):
    with self.assertRaises(util.UnsupportedPlatform):
      self.Run("alpha cloud-shell get-mount-command myMountDir")

  def mockConnection(self,
                     user="some-user",
                     host="some-host",
                     port=6000,
                     key=None):
    self.StartPatch(
        "googlecloudsdk.command_lib.cloud_shell.util.PrepareEnvironment",
        return_value=util.ConnectionInfo(
            ssh_env=None, user=user, host=host, port=port, key=key))


if __name__ == "__main__":
  test_case.main()
