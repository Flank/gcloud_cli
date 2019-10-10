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
"""Integration tests for the emulators bigtable commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class BigtableTest(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  @test_case.Filters.DoNotRunOnWindows('Not supported on Windows.')
  def testStartEmulatorAndPrintEnv(self):
    with self.ExecuteScriptAsync(
        'gcloud',
        ['beta', 'emulators', 'bigtable', 'start'],
        match_strings=['[bigtable] Cloud Bigtable '
                       'emulator running on 127.0.0.1:8086'],
        timeout=30):
      self.Run('beta emulators bigtable env-init')
      # Default port for bigtable emulator is 8086
      self.AssertOutputContains('BIGTABLE_EMULATOR_HOST=localhost:8086')


if __name__ == '__main__':
  test_case.main()
