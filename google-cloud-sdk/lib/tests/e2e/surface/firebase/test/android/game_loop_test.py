# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import e2e_base
from tests.lib.surface.firebase.test.android import commands


class GameLoopRunTest(e2e_base.TestIntegrationTestBase):
  """Integration test for test type game-loop."""

  def testGameLoopTestType_InvalidScenarioNumber(self):
    # ftlgame.apk only supports scenarios from 1 to 5.
    with self.assertRaises(exceptions.BadMatrixError):
      self.Run(
          '{cmd} --type=game-loop --app={app} --scenario-numbers=2,6 '.format(
              cmd=commands.ANDROID_BETA_TEST_RUN, app=e2e_base.FTLGAME_APP))

  def testGameLoopTestType_InvalidScenarioLabel(self):
    with self.assertRaises(exceptions.BadMatrixError):
      self.Run('{cmd} --type=game-loop --app={app} --scenario-labels=bad-label '
               .format(
                   cmd=commands.ANDROID_BETA_TEST_RUN,
                   app=e2e_base.FTLGAME_APP))


if __name__ == '__main__':
  test_case.main()
