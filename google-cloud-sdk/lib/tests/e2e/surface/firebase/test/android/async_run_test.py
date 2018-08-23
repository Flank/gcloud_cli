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

from tests.lib import test_case
from tests.lib.surface.firebase.test import e2e_base
from tests.lib.surface.firebase.test.android import commands


class AsyncTestRunTests(e2e_base.TestIntegrationTestBase):
  """Integration tests for: gcloud firebase test run --async commands.

  These relatively fast-executing tests exercise each of the main test types
  supported by Firebase Test Lab.
  """

  @test_case.Filters.skip('Failing sporadically.', 'b/36781383')
  def testInstrumentationTest_ExplicitType_ManyDimensions_Async(self):
    self.Run(
        '{cmd} --type instrumentation --app {app} --test {test} --timeout 5m '
        '--async --device-ids=Nexus7,Nexus9,Nexus10 -v 22 -l=ru -o=landscape'
        .format(
            cmd=commands.ANDROID_TEST_RUN,
            app=e2e_base.WALKSHARE_APP,
            test=e2e_base.WALKSHARE_TEST))

    self.AssertErrMatches(r'Upload.*walkshare.apk')
    self.AssertErrMatches(r'Upload.*walkshare-test.apk')
    self.AssertErrContains('instrumentation test on 3 device(s)')
    self.AssertOutputMatches(r'available.*\[https://.*testlab/histories/')
    self.AssertOutputNotContains('Inconclusive')

  @test_case.Filters.skip('Failing sporadically.', 'b/36781383')
  def testRoboTest_ExplicitType_ArgFileOverridesAsync_OneInvalidDimension(self):
    self.Run('{cmd} {argfile}:robo-integration --timeout 65s --async'.format(
        cmd=commands.ANDROID_TEST_RUN, argfile=e2e_base.INTEGRATION_ARGS))

    self.AssertErrMatches(r'async True.*overrides.*async: False')
    self.AssertErrMatches(r'Upload.*notepad.apk')
    self.AssertErrContains('execute your robo test on 1 device(s)')
    self.AssertOutputMatches(r'available.*\[https://console.*/histories/')
    self.AssertOutputNotContains('Inconclusive')


if __name__ == '__main__':
  test_case.main()
