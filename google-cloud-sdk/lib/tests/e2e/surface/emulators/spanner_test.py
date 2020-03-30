# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Integration tests for the emulators spanner commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class SpannerTest(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  @test_case.Filters.skipAlways(
      'The emulator is not a fully-static binary and currently does not run on '
      'the cloud sdk kokoro ubuntu vm', 'b/151742960')
  @test_case.Filters.RunOnlyOnLinux('Native binaries only on linux.')
  def testStartEmulatorAndPrintEnv(self):
    with self.ExecuteScriptAsync(
        'gcloud', ['beta', 'emulators', 'spanner', 'start'],
        match_strings=['Cloud Spanner emulator running'],
        timeout=30):
      self.Run('beta emulators spanner env-init')
      # Default port for spanner emulator is 9010
      self.AssertOutputContains('SPANNER_EMULATOR_HOST=localhost:9010')


if __name__ == '__main__':
  test_case.main()
