# -*- coding: utf-8 -*- #
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
"""Integration tests for the emulators pubsub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import java
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class PubSubTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  def SetUp(self):
    # Verify that Java is installed or skip these tests
    with self.SkipTestIfRaises(java.JavaError):
      java.RequireJavaInstalled('test')

  def testStartEmulatorAndPrintEnv(self):
    port = self.GetPort()
    with self.ExecuteScriptAsync(
        'gcloud',
        ['beta', 'emulators', 'pubsub', 'start',
         '--host-port=localhost:' + port],
        match_strings=['[pubsub] INFO: Server started, listening on %s' % port],
        timeout=30):
      self.Run('beta emulators pubsub env-init')
      self.AssertOutputContains('PUBSUB_EMULATOR_HOST=localhost:' + port)

  def testStartEmulatorWithExplicitIP(self):
    port = self.GetPort()
    with self.ExecuteScriptAsync(
        'gcloud',
        ['beta', 'emulators', 'pubsub', 'start',
         '--host-port=127.0.0.1:' + port],
        match_strings=['[pubsub] INFO: Server started, listening on %s' % port],
        timeout=30):
      self.Run('beta emulators pubsub env-init')
      self.AssertOutputContains('PUBSUB_EMULATOR_HOST=127.0.0.1:' + port)

  def testStartEmulatorWithDefaultHost(self):
    with self.ExecuteLegacyScriptAsync(
        'gcloud',
        ['beta', 'emulators', 'pubsub', 'start'],
        match_strings=['[pubsub] INFO: Server started, listening on 8085'],
        timeout=30):
      self.Run('beta emulators pubsub env-init')
      self.AssertOutputContains('PUBSUB_EMULATOR_HOST=localhost:8085')

if __name__ == '__main__':
  test_case.main()
