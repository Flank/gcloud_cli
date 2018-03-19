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


class VersionsTests(e2e_base.TestIntegrationTestBase):

  def SetUp(self):
    pass

  @test_case.Filters.skip('Failing', 'b/73120615')
  def testAndroidVersionsList(self):
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertOutputMatches(r'^OS_VERSION_ID | VERSION | CODENAME',
                             normalize_space=True)
    self.AssertOutputMatches(r'19 .* 4.4.x .* KitKat')
    self.AssertOutputMatches(r'21 .* 5.0.x .* Lollipop')
    self.AssertOutputContains('default')


if __name__ == '__main__':
  test_case.main()
