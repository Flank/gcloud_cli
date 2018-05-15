# Copyright 2018 Google Inc. All Rights Reserved.
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
from tests.lib.surface.firebase.test.ios import commands


class IosVersionsTests(e2e_base.TestIntegrationTestBase):

  def testIosVersionsList(self):
    self.Run(commands.IOS_VERSIONS_LIST)
    self.AssertOutputMatches(
        r'^OS_VERSION_ID | MAJOR_VERSION | MAJOR_VERSION | TAGS',
        normalize_space=True)
    self.AssertOutputMatches(r'11.2 | 11 | 2', normalize_space=True)
    self.AssertOutputContains('default')

  def testIosVersionsDescribe(self):
    self.Run(commands.IOS_VERSIONS_DESCRIBE + '11.2')
    self.AssertOutputContains("id: '11.2'")
    self.AssertOutputContains('majorVersion: 11')
    self.AssertOutputContains('minorVersion: 2')
    self.AssertOutputContains('tags:')
    self.AssertOutputContains('default')


if __name__ == '__main__':
  test_case.main()
