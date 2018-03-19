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

from googlecloudsdk.api_lib.firebase.test import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import commands
from tests.lib.surface.firebase.test import e2e_base


class GameLoopRunTest(e2e_base.TestIntegrationTestBase):
  """Integration test for test type game-loop."""

  @test_case.Filters.skip('Failing', 'b/68211846')
  def testGameLoopTestType(self):
    self.Run(
        u'{cmd} --type=game-loop --app={app} --async '
        u'--device model=shamu,version=23 '
        u'--scenario-numbers=3 --scenario-labels=compatibility '
        .format(cmd=commands.ANDROID_BETA_TEST_RUN,
                app=e2e_base.FTLGAME_APP))

    self.AssertErrMatches(r'Uploading.*ftlgame.apk')
    self.AssertErrContains('execute your game-loop test on 1 device')
    self.AssertOutputMatches(r'available at.*\[https://console.firebase')

  @test_case.Filters.skip('Failing', 'b/68211846')
  def testGameLoopTestType_InvalidScenarioNumber(self):
    # ftlgame.apk only supports scenarios from 1 to 5.
    with self.assertRaises(exceptions.BadMatrixError):
      self.Run(
          u'{cmd} --type=game-loop --app={app} --scenario-numbers=2,6 '
          .format(cmd=commands.ANDROID_BETA_TEST_RUN,
                  app=e2e_base.FTLGAME_APP))

  @test_case.Filters.skip('Failing', 'b/68211846')
  def testGameLoopTestType_InvalidScenarioLabel(self):
    with self.assertRaises(exceptions.BadMatrixError):
      self.Run(
          u'{cmd} --type=game-loop --app={app} --scenario-labels=bad-label '
          .format(cmd=commands.ANDROID_BETA_TEST_RUN,
                  app=e2e_base.FTLGAME_APP))

if __name__ == '__main__':
  test_case.main()
