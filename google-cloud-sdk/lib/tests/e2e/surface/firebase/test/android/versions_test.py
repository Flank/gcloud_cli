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
from tests.lib.surface.firebase.test import e2e_base
from tests.lib.surface.firebase.test.android import commands


class AndroidVersionsTests(e2e_base.TestIntegrationTestBase):

  def testAndroidVersionsList(self):
    self.Run(commands.ANDROID_VERSIONS_LIST)
    self.AssertOutputMatches(r'^OS_VERSION_ID | VERSION | CODENAME',
                             normalize_space=True)
    self.AssertOutputMatches(r'19 .* 4.4.x .* KitKat')
    self.AssertOutputMatches(r'21 .* 5.0.x .* Lollipop')
    self.AssertOutputContains('default')

  def testAndroidVersionsDescribe(self):
    self.Run(commands.ANDROID_VERSIONS_DESCRIBE + '25')
    self.AssertOutputContains('apiLevel: 25')
    self.AssertOutputContains("id: '25'")
    self.AssertOutputContains('codeName: Nougat')
    self.AssertOutputContains('versionString: 7.1.x')
    self.AssertOutputContains('releaseDate:')
    self.AssertOutputContains('  year: 2016')


if __name__ == '__main__':
  test_case.main()
