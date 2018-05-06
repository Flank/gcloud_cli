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


class LocalesTests(e2e_base.TestIntegrationTestBase):

  def SetUp(self):
    pass

  def testAndroidLocalesList(self):
    self.Run(commands.ANDROID_LOCALES_LIST)
    self.AssertOutputMatches(r'^LOCALE | NAME | REGION', normalize_space=True)
    self.AssertOutputMatches(r'da_DK .* Danish .* Denmark')
    self.AssertOutputMatches(r'en_US .* English .* United States')
    self.AssertOutputMatches(r'zh .* Chinese ')
    self.AssertOutputContains('default')


if __name__ == '__main__':
  test_case.main()
