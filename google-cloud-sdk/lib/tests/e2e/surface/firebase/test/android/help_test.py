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

from tests.lib import test_case
from tests.lib.surface.firebase.test import commands
from tests.lib.surface.firebase.test import e2e_base


class HelpGcloudTestTests(e2e_base.TestIntegrationTestBase):
  """Integration tests for the *help gcloud firebase test* commands/groups."""

  def testHelpTestRun(self):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run('help {cmd}'.format(cmd=commands.ANDROID_TEST_RUN))
    self.AssertOutputContains('invoke a test in Firebase Test Lab')
    self.AssertOutputContains(commands.ANDROID_TEST_RUN)
    self.AssertOutputContains('ARGSPEC')
    self.AssertOutputContains('--app')
    self.AssertOutputContains('--async')
    self.AssertOutputContains('EXAMPLES')

  def testHelpTestDevicesList(self):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run('help {cmd} list'.format(cmd=commands.ANDROID_MODELS_LIST))
    self.AssertOutputContains('List all Android models available for testing')
    self.AssertOutputContains(commands.ANDROID_MODELS_LIST)


if __name__ == '__main__':
  test_case.main()
